"""List-price equivalents: each response once, by its own model and prompt size, never an invented price."""
import tempfile
import unittest
from pathlib import Path

from pler.usage import claude_code, codex, pricing
from pler.usage.archive import sanitize
from pler.usage.summary import summarize
from test_logs import write_jsonl


def tokens(input=0, cache_read=0, cache_write=0, output=0):
    return dict(input=input, cache_read=cache_read, cache_write=cache_write, output=output, reasoning=0)


def reply(identity, at, usage, model='claude-opus-5-5', block='text'):
    return dict(type='assistant', timestamp=at, sessionId='s1', cwd='/invented/project', requestId='r-' + identity,
                message=dict(id=identity, model=model, usage=usage, content=[dict(type=block, text='invented')]))


class PriceTableTests(unittest.TestCase):
    def test_claude_one_hour_and_five_minute_writes_are_priced_apart(self):
        value = pricing.response_cost('claude-code', 'claude-opus-5-5',
                                      tokens(input=1_000_000, cache_read=1_000_000, cache_write=3_000_000, output=1_000_000),
                                      write_1h=1_000_000)
        # 4 input + 0.20 read + 2 x 5 (5-minute writes) + 1 x 8 (1-hour write) + 20 output
        self.assertAlmostEqual(value, 42.20)

    def test_dated_model_ids_use_their_family_price(self):
        self.assertAlmostEqual(pricing.response_cost('claude-code', 'claude-haiku-4-5-20251001', tokens(output=1_000_000)), 5)

    def test_unknown_model_other_speed_or_inconsistent_split_is_not_priced(self):
        for agent, model in (('claude-code', 'claude-invented-9'), ('codex', 'codex-auto-review'), ('codex', None),
                             ('claude-code', '<synthetic>'), ('other', 'claude-opus-5-5')):
            self.assertIsNone(pricing.response_cost(agent, model, tokens(input=10)), model)
        self.assertIsNone(pricing.response_cost('claude-code', 'claude-opus-5-5', tokens(input=10), standard=False))
        self.assertIsNone(pricing.response_cost('claude-code', 'claude-opus-5-5', tokens(cache_write=5), write_1h=6))

    def test_prompt_size_selects_a_tier_and_an_uncovered_size_stays_unpriced(self):
        short = tokens(input=200_000, cache_read=72_000, output=1_000_000)
        long = tokens(input=200_000, cache_read=72_001, output=1_000_000)
        self.assertAlmostEqual(pricing.response_cost('codex', 'gpt-6.1-sol', short), 0.4 + 0.0072 + 10)
        self.assertAlmostEqual(pricing.response_cost('codex', 'gpt-6.1-sol', long), 0.8 + 0.0144002 + 15)
        self.assertIsNotNone(pricing.response_cost('codex', 'gpt-5.3-codex', short))
        self.assertIsNone(pricing.response_cost('codex', 'gpt-5.3-codex', long))
        self.assertIsNone(pricing.response_cost('claude-code', 'claude-sonnet-4-5', tokens(input=200_001)))
        self.assertAlmostEqual(pricing.response_cost('claude-code', 'claude-haiku-5-5', tokens(input=100_001)), 0.0500005)

    def test_codex_new_cache_writes_without_lifetime_are_unpriced_legacy_rate_is_preserved(self):
        for model in ('gpt-6-astra','gpt-6.1-sol','gpt-6.1-terra','gpt-6-luna','gpt-6-sol'):
            self.assertIsNone(pricing.response_cost('codex',model,tokens(input=50,cache_write=100,output=10)))
            self.assertIsNotNone(pricing.response_cost('codex',model,tokens(input=50,output=10)))
        self.assertAlmostEqual(pricing.response_cost('codex','gpt-5.3-codex',tokens(cache_write=100_000)),0.175)

    def test_unlisted_codex_dated_suffix_is_not_a_published_model_alias(self):
        self.assertIsNone(pricing.response_cost('codex','gpt-6.1-sol-20990101',tokens(input=100)))


class ReaderPricingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'session.jsonl'

    def claude(self, rows):
        write_jsonl(self.path, rows)
        issues = []
        sessions = claude_code.read([self.path], issues)
        self.assertEqual(issues, [])
        return sessions

    def test_content_block_copies_are_priced_once_with_their_one_hour_share(self):
        usage = dict(input_tokens=1_000_000, cache_read_input_tokens=0, cache_creation_input_tokens=2_000_000,
                     output_tokens=0, cache_creation=dict(ephemeral_5m_input_tokens=1_000_000,
                                                          ephemeral_1h_input_tokens=1_000_000),
                     speed='standard', inference_geo='global', service_tier='standard')
        session, = self.claude([reply('m1', '2026-10-29T10:00:00Z', usage),
                                reply('m1', '2026-10-29T10:00:02Z', usage, block='thinking')])
        self.assertAlmostEqual(session.api_usd, 4 + 5 + 8)
        self.assertEqual(session.api_priced_tokens, 3_000_000)
        totals = summarize([session])['totals']
        self.assertEqual((totals['api_usd'], totals['api_priced_share']), (17.0, 1.0))

    def test_fast_or_us_only_responses_and_unknown_models_are_counted_but_unpriced(self):
        base = dict(input_tokens=1_000_000, output_tokens=0)
        session, = self.claude([reply('m1', '2026-10-29T10:00:00Z', dict(base, speed='fast')),
                                reply('m2', '2026-10-29T10:00:01Z', dict(base, inference_geo='us')),
                                reply('m3', '2026-10-29T10:00:02Z', base, model='claude-invented-9'),
                                reply('m4', '2026-10-29T10:00:03Z', base)])
        self.assertEqual(session.tokens['input'], 4_000_000)
        self.assertAlmostEqual(session.api_usd, 4)
        self.assertAlmostEqual(summarize([session])['totals']['api_priced_share'], 0.25)

    def test_a_region_logged_as_not_available_is_priced_like_an_absent_one(self):
        # Claude Code wrote 'not_available' for every response before the region was reported.
        base = dict(input_tokens=1_000_000, output_tokens=0, speed='standard', service_tier='standard')
        session, = self.claude([reply('m1', '2026-09-23T10:00:00Z', dict(base, inference_geo='not_available')),
                                reply('m2', '2026-10-29T10:00:00Z', dict(base, inference_geo='global'))])
        self.assertAlmostEqual(session.api_usd, 8)
        self.assertEqual(session.api_priced_tokens, 2_000_000)

    def test_the_archive_keeps_only_numeric_split_and_short_words(self):
        usage = dict(input_tokens=1, output_tokens=1, cache_creation_input_tokens=5, ephemeral_1h_input_tokens=5,
                     speed='standard', inference_geo='global')
        row = dict(type='assistant', sessionId='s1', timestamp='2026-10-29T10:00:00Z',
                   message=dict(id='m1', model='claude-opus-5-5', usage=usage, content=[]))
        kept = sanitize('claude-code', [row])[0]['message']['usage']
        self.assertEqual((kept['ephemeral_1h_input_tokens'], kept['speed'], kept['inference_geo']), (5, 'standard', 'global'))
        bad = sanitize('claude-code', [dict(row, message=dict(row['message'], usage=dict(usage, ephemeral_1h_input_tokens=6)))])
        self.assertEqual(bad, [dict(type='pler_file_issue', reason='MalformedRows')])
        odd = sanitize('claude-code', [dict(row, message=dict(row['message'], usage=dict(usage, speed='not a word!')))])
        self.assertNotIn('speed', odd[0]['message']['usage'])
        self.assertIs(odd[0]['message']['usage']['price_inputs_complete'],False)

    def test_codex_responses_are_priced_by_their_turn_model(self):
        rows = [dict(type='session_meta', timestamp='2026-10-29T09:00:00Z', payload=dict(id='c1', cwd='/invented/project')),
                dict(type='turn_context', timestamp='2026-10-29T09:00:01Z', payload=dict(model='gpt-6.1-sol')),
                dict(type='token_usage_record', timestamp='2026-10-29T09:00:02Z',
                     payload=dict(response_id='r1', usage=dict(input_tokens=100_000, output_tokens=1_000_000))),
                dict(type='turn_context', timestamp='2026-10-29T09:00:03Z', payload=dict(model='codex-auto-review')),
                dict(type='token_usage_record', timestamp='2026-10-29T09:00:04Z',
                     payload=dict(response_id='r2', usage=dict(input_tokens=100_000, output_tokens=0)))]
        path = Path(self.temp.name) / 'rollout-test.jsonl'
        write_jsonl(path, rows)
        sessions, issues = codex.read([path])
        self.assertEqual(issues, [])
        session, = sessions
        self.assertAlmostEqual(session.api_usd, 0.2 + 10)  # the second response's model has no published price
        self.assertEqual(session.api_priced_tokens, 1_100_000)


if __name__ == '__main__':
    unittest.main()
