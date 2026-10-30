"""Seeded malformed inputs and append partitions preserve good accounting and private-text boundaries."""
import json
import os
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import claude_code,codex,input_limits
from pler.usage.cache import FileCache
from pler.usage.records import total
from test_logs import SECRET,USAGE,claude_reply,codex_rows


PRIVATE='PRIVATE-FUZZ-TEXT-NEVER-PERSIST'


def encoded(row,ascii=True):
    return json.dumps(row,ensure_ascii=ascii).encode('utf-8')+b'\n'


def ignored(rng):
    alphabet='[]{}\\"\n\r\t\x01\u03bb\u2028abc123'
    text=PRIVATE+''.join(rng.choice(alphabet) for _ in range(rng.randrange(10,80)))
    return dict(type='ignored-fuzz-record',nested=[dict(text=text),[text,text[::-1]]])


def account(agent,path):
    issues=[]
    if agent=='claude':sessions=claude_code.read([path],issues)
    else:sessions,issues=codex.read([path])
    value=(sum(s.calls for s in sessions),sum(total(s.tokens) for s in sessions),
           tuple((s.tokens_complete,s.calls_complete,tuple(sorted(s.issues))) for s in sessions),
           tuple(reason for _,reason in issues))
    return value


def projection(agent,path,resume=None,point=None):
    return (claude_code._rows(path,resume,point) if agent=='claude' else
            codex._rows(path,codex.decoder()[0],resume,point))


class ReaderFuzzTests(unittest.TestCase):
    def test_seeded_malformed_rows_keep_good_usage_independent_of_byte_chunks(self):
        rng=random.Random(20261030)
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            for case in range(20):
                agent='claude' if case%2==0 else 'codex'
                path=base/('transcript.jsonl' if agent=='claude' else 'rollout-invented.jsonl')
                if agent=='claude':
                    valid=[encoded(claude_reply('invented','m'+str(n),'r'+str(n),USAGE,
                              [dict(type='text',text=PRIVATE)],'2026-10-20T10:00:0%sZ'%n)) for n in (1,2)]
                    expected=(2,2520)
                else:
                    valid=[encoded(row) for row in codex_rows()]
                    expected=(2,2100)
                malformed=(b'{"ignored":"unfinished\\\n',b'{"ignored":NaN}\n',
                           b'{"ignored":"unescaped\x01control"}\n',b'[1,2,3]\n')[case//2%4]
                deep=b'{"ignored":'+b'['*300+b'0'+b']'*300+b'}\n'
                too_long=b'{"ignored":"'+PRIVATE.encode()+b'x'*1300+b'"}\n'
                noise=[encoded(ignored(rng),ascii=bool(case%3)),malformed,deep,too_long,
                       b'{"ignored":"invalid-utf8-\xff"}\n']
                rng.shuffle(noise)
                path.write_bytes(valid[0]+b''.join(noise)+b''.join(valid[1:]))
                with patch.object(input_limits,'MAX_LINE_BYTES',1024):
                    reference=account(agent,path)
                    self.assertEqual(reference[:2],expected)
                    self.assertTrue(reference[3])
                    self.assertFalse(all(row[0] for row in reference[2]))
                    for width in (1 if case==0 else rng.choice((3,7,11,31)),rng.choice((73,127,4096))):
                        with self.subTest(case=case,agent=agent,chunk=width),patch.object(input_limits,'CHUNK_BYTES',width):
                            self.assertEqual(account(agent,path),reference)
                            slim=json.dumps(projection(agent,path))
                            self.assertNotIn(PRIVATE,slim)
                            self.assertNotIn(SECRET,slim)

    def test_seeded_complete_append_partitions_match_full_projection_after_every_growth(self):
        rng=random.Random(52320261030)
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            cache_folder=base/'cache';cache_folder.mkdir()
            with patch.dict(os.environ,PLER_CACHE_DIR=str(cache_folder)):
                for agent in ('claude','codex'):
                    path=base/(agent+'.jsonl')
                    if agent=='claude':
                        lines=[encoded(claude_reply('invented','m0','r0',USAGE,
                                      [dict(type='text',text=PRIVATE)],'2026-10-20T10:00:00Z'))]
                    else:lines=[encoded(row) for row in codex_rows()[:2]]
                    for number in range(1,11):
                        if agent=='claude':
                            row=claude_reply('invented','m'+str(number),'r'+str(number),USAGE,
                                            [dict(type='text',text=PRIVATE)],'2026-10-20T10:00:%02dZ'%number)
                        else:
                            row=dict(type='token_usage_record',timestamp='2026-10-20T10:00:%02dZ'%number,
                                     payload=dict(response_id='r'+str(number),usage=dict(input_tokens=100,
                                         cached_input_tokens=10,output_tokens=5,reasoning_output_tokens=0)))
                        lines.append(encoded(row))
                        lines.append(encoded(ignored(rng),ascii=bool(number%2)))
                        if number in (3,8):lines.append(b'{malformed-complete-line\n')
                    path.write_bytes(lines[0])
                    cursor=1;continued=0
                    while True:
                        cache=FileCache('fuzz-'+agent,'invented-reader-version')
                        cache.get(path)
                        resume=cache.grown(path)
                        continued+=resume is not None
                        point={}
                        rows=projection(agent,path,resume,point)
                        with self.subTest(agent=agent,prefix=cursor):
                            self.assertEqual(rows,projection(agent,path))
                            self.assertNotIn(PRIVATE,json.dumps(rows))
                            self.assertNotIn(SECRET,json.dumps(rows))
                        cache.put(path,rows,point);cache.save()
                        if cursor==len(lines):break
                        end=min(len(lines),cursor+rng.randrange(1,5))
                        with path.open('ab') as stream:stream.write(b''.join(lines[cursor:end]))
                        cursor=end
                    if path.stat().st_ino:self.assertGreater(continued,0)
                    else:self.assertEqual(continued,0)
                    final=account(agent,path)
                    self.assertEqual(final[:2],(11,13860) if agent=='claude' else (10,1050))
                    self.assertFalse(all(row[0] for row in final[2]))
