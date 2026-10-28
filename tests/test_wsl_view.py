"""A stopped or unavailable selected distro is explained without leaking any selected path."""
import unittest

from pler.dashboard import project_view


class WslCoverageTests(unittest.TestCase):
    def test_unavailable_selected_wsl_source_has_a_localized_explanation(self):
        for reason in ('WSLNotRunning', 'WSLUnavailable'):
            for lang, phrase in (('en', 'Open the distribution yourself'), ('tr', 'Dağıtımı kendiniz açıp')):
                with self.subTest(reason=reason, lang=lang):
                    value = project_view([], dict(claude_files=0, codex_files=0,
                        skipped=[('private-path-canary', reason)]), days=0, lang=lang)
                    self.assertFalse(value['quality']['tokens_complete'])
                    warnings = {item['code']: item['detail'] for item in value['quality']['issues']}
                    self.assertIn(phrase, warnings['wsl_unavailable'])
                    self.assertNotIn('private-path-canary', str(value))
