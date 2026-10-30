"""Speed guard: large slowdowns fail CI before a release.

CI machines differ in speed, so no test here compares with a fixed number of seconds. Each compares two
timings taken in the same process on the same invented logs (speed_logs.py): PLER's work against plain
json.loads of the same bytes, or one PLER path against another. The limits are about twice the largest ratio
seen on Windows and Linux with Python 3.9, 3.12 and 3.14 on 30 October 2026 (in the comments), so ordinary
noise passes and a regression like 0.2.11's ninefold later read does not; smaller slowdowns are left to the
recorded measurements. That the page's unchanged refresh merges nothing is checked by test_rescan.py.
"""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import claude_code, codex, scan
from pler.usage.cache import FileCache
from pler.usage.zstd import decoder
from speed_logs import best, claude_lines, codex_lines

TURNS = 400       # about 6 MB of transcript and 7 MB of rollout
GROWTH = 30       # lines appended while an agent works


class SpeedGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp())
        cls.claude = cls.root / 'claude' / 'projects' / 'invented' / 'session.jsonl'
        cls.rollout = cls.root / 'codex' / 'sessions' / '2026' / '10' / '30' / 'rollout-invented.jsonl'
        cls.claude.parent.mkdir(parents=True)
        cls.rollout.parent.mkdir(parents=True)
        (cls.root / 'codex' / 'archived_sessions').mkdir()
        cls.lines = {cls.claude: claude_lines(TURNS), cls.rollout: codex_lines(TURNS)}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.root), ignore_errors=True)

    def setUp(self):
        for path, lines in self.lines.items():
            path.write_bytes(b''.join(lines[:-GROWTH]))
        cache = self.root / 'cache'
        shutil.rmtree(str(cache), ignore_errors=True)
        env = patch.dict(os.environ, PLER_CACHE_DIR=str(cache), CLAUDE_CONFIG_DIR=str(self.root / 'claude'),
                         CODEX_HOME=str(self.root / 'codex'))
        env.start(); self.addCleanup(env.stop)

    def grow(self):
        for path, lines in self.lines.items():
            with path.open('ab') as stream:
                stream.write(b''.join(lines[-GROWTH:]))

    @staticmethod
    def parse(path):
        for line in path.read_bytes().splitlines():
            json.loads(line)

    def test_a_first_read_costs_a_few_plain_json_parses(self):
        # Seen: 2.8-4.2 for both readers, once 5.6.
        decode = decoder()[0]
        for path, read in ((self.claude, lambda: claude_code._rows(self.claude)),
                           (self.rollout, lambda: codex._rows(self.rollout, decode))):
            with self.subTest(log=path.name):
                ratio = best(read) / best(lambda: self.parse(path))
                self.assertLess(ratio, 10, 'reading took %.1f times a plain JSON parse' % ratio)

    def test_a_later_read_of_unchanged_logs_stays_cheap(self):
        # Seen: 12-21 times a plain parse of the reader caches on Windows, 18-28 on Linux.
        scan()
        caches = [self.root / 'cache' / name for name in ('claude.json', 'codex.json')]
        ratio = best(scan) / best(lambda: [json.loads(path.read_bytes()) for path in caches])
        self.assertLess(ratio, 60, 'a later read took %.1f times parsing its caches' % ratio)

    def test_a_grown_log_is_read_on_from_where_the_last_read_ended(self):
        # Seen: 0.018-0.026 of a full read.
        cache = FileCache('claude', 'speed-guard')
        cache.get(self.claude)
        point = {}
        cache.put(self.claude, claude_code._rows(self.claude, None, point), point)
        cache.save()
        self.grow()
        cache = FileCache('claude', 'speed-guard')
        self.assertIsNone(cache.get(self.claude))
        resume = cache.grown(self.claude)
        self.assertIsNotNone(resume)
        continued = best(lambda: claude_code._rows(self.claude, resume, {}))
        full = best(lambda: claude_code._rows(self.claude))
        self.assertLess(continued / full, 0.25, 'continuing took %.2f of a full read' % (continued / full))
