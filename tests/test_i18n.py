"""English and Turkish stay complete and consistent: same keys, same placeholders, every word the code and the page
use exists, the right language is picked, and counted nouns read naturally."""
from datetime import datetime, timedelta, timezone
import ast
import json
from pathlib import Path
import re
import string
import unittest
from unittest import mock

from pler import i18n
from pler.dashboard import project_view
from pler.usage.records import Session

SOURCE = Path(__file__).resolve().parent.parent / 'src' / 'pler'
NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


def fields(template):
    return sorted(name for _, name, _, _ in string.Formatter().parse(template) if name is not None)


def page_table():
    script = (SOURCE / 'web' / 'app.js').read_text(encoding='utf-8')
    return script, json.loads(script[script.index('/*I18N*/') + 8:script.index('/*END*/')])


class TableTests(unittest.TestCase):
    def test_python_tables_match_key_for_key_and_placeholder_for_placeholder(self):
        english, turkish = i18n.TEXT['en'], i18n.TEXT['tr']
        self.assertEqual(set(english), set(turkish))
        for key in english:
            with self.subTest(key=key):
                self.assertEqual(fields(english[key]), fields(turkish[key]))
        self.assertEqual(set(i18n.NOUNS['en']), set(i18n.NOUNS['tr']))

    def test_every_key_the_python_code_says_exists(self):
        used = set()
        for path in SOURCE.rglob('*.py'):
            used |= set(re.findall(r"say\(\s*[\w.\[\]']+,\s*'([\w.]+)'", path.read_text(encoding='utf-8')))
        prefixes = {key for key in used if key.endswith('.')}  # completed at run time, e.g. 'status.' + '300'
        self.assertGreater(len(used), 40)
        self.assertEqual(sorted(used - prefixes - set(i18n.TEXT['en'])), [])
        for prefix in prefixes:
            self.assertTrue(any(key.startswith(prefix) for key in i18n.TEXT['en']), prefix)

    def test_page_tables_match_and_cover_the_page(self):
        script, table = page_table()
        self.assertEqual(set(table['en']), set(table['tr']))
        for key, value in table['en'].items():
            other = table['tr'][key]
            with self.subTest(key=key):
                if isinstance(value, list):
                    self.assertEqual(len(value), 2)
                else:
                    self.assertIsInstance(other, str)
                    self.assertEqual(sorted(re.findall(r'\{(\w+)\}', value)), sorted(re.findall(r'\{(\w+)\}', other)))
        page = (SOURCE / 'web' / 'index.html').read_text(encoding='utf-8')
        used = set(re.findall(r"\bt\('([a-z0-9_]+)'", script)) | set(re.findall(r'data-i18n(?:-label|-placeholder)?="(\w+)"', page))
        used |= {'noun_' + noun for noun in re.findall(r"count\([^,]+,'(\w+)'", script)}
        used -= {'big_'}  # built as 'big_' + power
        self.assertEqual(sorted(used - set(table['en'])), [])

    def test_no_turkish_word_is_left_outside_the_tables(self):
        turkish = re.compile('[çğıöşüÇĞİÖŞÜ]')
        script, _ = page_table()
        outside = script[:script.index('/*I18N*/')] + script[script.index('/*END*/'):]
        self.assertEqual(turkish.findall(outside), [])
        for path in SOURCE.rglob('*.py'):
            if path.name == 'i18n.py':
                continue
            with self.subTest(file=path.name):
                source = path.read_text(encoding='utf-8')
                catalog_lines = set()
                if path.name == 'diagnostics.py':
                    # Diagnostics intentionally owns its bilingual allowlist. Only that table
                    # is exempt; executable code still goes through the same check below.
                    catalog = next(node for node in ast.parse(source).body if isinstance(node, ast.Assign)
                                   and any(isinstance(target, ast.Name) and target.id == 'CATALOG' for target in node.targets))
                    for row in ast.literal_eval(catalog.value).values():
                        self.assertEqual(len(row), 7)
                        self.assertTrue(all(isinstance(value, str) and value for value in row))
                        self.assertEqual(fields(row[3]), fields(row[5]))
                        self.assertEqual(fields(row[4]), fields(row[6]))
                    catalog_lines = set(range(catalog.lineno, catalog.end_lineno + 1))
                strings = [line for index, line in enumerate(source.splitlines(), 1) if index not in catalog_lines and turkish.search(line)
                           and not line.strip().startswith('#')]
                self.assertEqual(strings, [])


class LanguageTests(unittest.TestCase):
    def test_choice_order(self):
        with mock.patch('locale.getlocale', return_value=('English_United States', '1252')):
            self.assertEqual(i18n.language({}), 'en')
            self.assertEqual(i18n.language({'LANG': 'tr_TR.UTF-8'}), 'tr')
            self.assertEqual(i18n.language({'PLER_LANG': 'tr'}), 'tr')
            self.assertEqual(i18n.language({'PLER_LANG': 'de', 'LANG': 'de_DE.UTF-8'}), 'en')
        with mock.patch('locale.getlocale', return_value=('English_United States', '1254')):  # Turkish regional settings
            self.assertEqual(i18n.language({}), 'tr')
            self.assertEqual(i18n.language({'PLER_LANG': 'en'}), 'en')

    def test_numbers_and_counted_nouns(self):
        self.assertEqual((i18n.big(2_200_000_000, 'en'), i18n.big(2_200_000_000, 'tr')), ('2.2 billion', '2,2 milyar'))
        self.assertEqual((i18n.big(950, 'en'), i18n.big(None, 'tr')), ('950', 'bilinmiyor'))
        self.assertEqual([i18n.count('en', n, 'session') for n in (0, 1, 2)], ['0 sessions', '1 session', '2 sessions'])
        self.assertEqual(i18n.count('tr', 2, 'session'), '2 oturum')
        self.assertEqual(i18n.count('en', 4700, 'model_call', '4.7 thousand'), '4.7 thousand model calls')
        self.assertEqual((i18n.window(300, 'en'), i18n.window(10080, 'tr'), i18n.window(60, 'en')), ('5-hour', 'haftalık', '60-minute'))


class PageDataTests(unittest.TestCase):
    def test_observations_and_labels_follow_the_requested_language(self):
        rows = [Session('codex', 's%d' % i, 'x', project='/work/a', started=NOW - timedelta(hours=1), ended=NOW,
                        calls=1, prompts=1, tokens=dict(input=10, cache_read=0, cache_write=0, output=0, reasoning=0)) for i in range(2)]
        rows.append(Session('codex', 'big', 'x', project=None, started=NOW - timedelta(hours=1), ended=NOW, calls=1, prompts=1,
                            tokens=dict(input=1000, cache_read=0, cache_write=0, output=0, reasoning=0)))
        english, turkish = project_view(rows, {}, days=0, now=NOW), project_view(rows, {}, days=0, now=NOW, lang='tr')
        self.assertEqual((english['lang'], turkish['lang']), ('en', 'tr'))
        self.assertEqual(english['insights'][0]['title'], 'Usage is concentrated in one session')
        self.assertEqual(turkish['insights'][0]['title'], 'Kullanım tek bir oturumda yoğunlaşıyor')
        self.assertIn('Unknown project', {row['name'] for row in english['projects']})
        self.assertIn('Proje bilinmiyor', {row['name'] for row in turkish['projects']})
        self.assertEqual(project_view(rows, {}, days=0, now=NOW, lang='xx')['lang'], 'en')
        with self.assertRaisesRegex(ValueError, 'period'):
            project_view(rows, {}, days=5)
        with self.assertRaisesRegex(ValueError, 'Dönem'):
            project_view(rows, {}, days=5, lang='tr')


if __name__ == '__main__':
    unittest.main()
