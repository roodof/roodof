"""Offline user help is included with the imported installation, never a filesystem browser."""
from html import escape
from pathlib import Path
import unittest
from unittest.mock import patch

from pler import __version__
from pler.help import render
import pler.help as help_module


class OfflineHelpTests(unittest.TestCase):
    def test_both_languages_render_the_imported_version_and_safe_operations(self):
        for lang in ('en','tr'):
            page=render(lang)
            self.assertIn('<html lang="'+lang+'">',page)
            self.assertIn(__version__,page)
            self.assertIn('pler cache reset',page)
            self.assertIn('pler archive off',page)
            self.assertIn('pler archive on',page)
            self.assertIn('pler archive clear',page)
            self.assertIn('metadata-archive.json',page)
            self.assertNotIn('__PLER_VERSION__',page)
            self.assertNotIn('<script',page)
            self.assertNotIn('https://',page)
            self.assertNotIn('http://',page)
            self.assertIn('href="/app.css"',page)

    def test_unknown_languages_fall_back_without_copying_the_value(self):
        for lang in ('../private','<script>',None,True,[]):
            self.assertEqual(render(lang),render('en'))

    def test_unknown_or_pathlike_chapters_are_refused_before_any_file_read(self):
        with patch.object(Path,'read_text',side_effect=AssertionError('unvalidated file read')):
            for chapter in ('../private','/etc/passwd',r'C:\private','https://example.invalid','',None,[]):
                with self.subTest(chapter=chapter),self.assertRaises(ValueError): render('en',chapter)

    def test_contract_is_bundled_with_the_imported_package_and_escaped(self):
        contract=Path(help_module.__file__).with_name('help')/'accounting.txt'
        contents=contract.read_text('utf-8')
        self.assertIn('Retained-log accounting contract',contents)
        self.assertIn(escape(contents),render('en','accounting'))
        self.assertIn(escape(contents),render('tr','accounting'))
        self.assertNotIn('__ACCOUNTING__',render('tr','accounting'))

    def test_bundled_contract_matches_the_candidate_source_contract(self):
        source=Path(__file__).resolve().parents[1]/'ACCOUNTING.md'
        bundled=Path(help_module.__file__).with_name('help')/'accounting.txt'
        self.assertEqual(bundled.read_text('utf-8'),source.read_text('utf-8'))

    def test_contract_markup_cannot_add_an_active_element(self):
        read=Path.read_text
        def artificial(path,*args,**kwargs):
            return '<script>PRIVATE-CANARY</script>' if path.name=='accounting.txt' else read(path,*args,**kwargs)
        with patch.object(Path,'read_text',artificial): page=render('en','accounting')
        self.assertIn('&lt;script&gt;PRIVATE-CANARY&lt;/script&gt;',page)
        self.assertNotIn('<script>',page)

    def test_help_uses_only_the_fixed_bundled_file_set(self):
        read=Path.read_text
        seen=[]
        base=Path(help_module.__file__).with_name('help')
        def checked(path,*args,**kwargs):
            self.assertEqual(path.parent,base)
            seen.append(path.name)
            return read(path,*args,**kwargs)
        with patch.object(Path,'read_text',checked):
            for lang in ('en','tr'):
                for chapter in ('guide','accounting'): render(lang,chapter)
        self.assertEqual(set(seen),{'en.html','tr.html','en-accounting.html','tr-accounting.html','accounting.txt'})


if __name__=='__main__':unittest.main()
