"""Archive integrity and cache behavior. Invented logs or checked-in reference fixtures only."""
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler.usage import claude_code, codex, scan, unzstd, xxh64, zstd
from pler.usage.cache import FileCache, version
from pler.usage.records import total,timestamp
from pler.usage.projects import ProjectRoots
from test_logs import SECRET, USAGE, ZSTD_FILES, ZSTD_SAMPLES, claude_reply, codex_rows, stored_zstd, write_jsonl


class ArchiveIntegrityTests(unittest.TestCase):
    def test_missing_checksum_bytes_and_wrong_checksums_are_rejected(self):
        for path in sorted(ZSTD_FILES.glob('*.zst')):
            data=path.read_bytes()
            if data[4]&4:
                for broken in (data[:-1],data[:-4],data[:-1]+bytes([data[-1]^1])):
                    with self.subTest(path=path.name,missing=len(data)-len(broken)),self.assertRaises(ValueError):
                        unzstd.decompress(broken)

    def test_checksum_matches_independently_encoded_reference_frames(self):
        checked=0
        for path in sorted(ZSTD_FILES.glob('*.zst')):
            data=path.read_bytes()
            if data[4]&4:
                raw=ZSTD_SAMPLES[path.name.split('-')[0]]()
                self.assertEqual(xxh64.digest(raw)&0xFFFFFFFF,int.from_bytes(data[-4:],'little'),path.name)
                checked+=1
        self.assertGreaterEqual(checked,5)
        self.assertEqual(xxh64.digest(b''),0xEF46DB3751D8E999)

    def test_batched_literal_path_preserves_every_reference_byte(self):
        original=unzstd._huffman
        def batched(data,at):
            tree,end=original(data,at)
            tree[3]=unzstd._literal_lookup(*tree[:3])
            return tree,end
        with patch.object(unzstd,'_huffman',side_effect=batched):
            for path in sorted(ZSTD_FILES.glob('*.zst')):
                with self.subTest(path=path.name):
                    self.assertEqual(unzstd.decompress(path.read_bytes()),ZSTD_SAMPLES[path.name.split('-')[0]]())

    def test_wrong_declared_content_size_is_rejected(self):
        frame=stored_zstd(b'abc')
        # This helper writes an 8-byte frame content size after its descriptor.
        for size in (0,2,4,10**9):
            damaged=frame[:5]+size.to_bytes(8,'little')+frame[13:]
            with self.subTest(size=size),self.assertRaises(ValueError): unzstd.decompress(damaged)

    def test_every_truncation_of_a_raw_frame_is_rejected(self):
        frame=stored_zstd(b'not a transcript')
        for end in range(len(frame)):
            with self.subTest(end=end),self.assertRaises(ValueError): unzstd.decompress(frame[:end])
        self.assertEqual(unzstd.decompress(frame),b'not a transcript')

    def test_truncated_skippable_frame_and_reserved_header_are_rejected(self):
        frame=(0x184D2A53).to_bytes(4,'little')+(5).to_bytes(4,'little')+b'abcde'
        self.assertEqual(unzstd.decompress(frame),b'')
        for end in range(len(frame)):
            with self.subTest(end=end),self.assertRaises(ValueError): unzstd.decompress(frame[:end])
        valid=stored_zstd(b'abc')
        with self.assertRaises(ValueError): unzstd.decompress(valid[:4]+bytes([valid[4]|8])+valid[5:])

    def test_incomplete_second_frame_cannot_hide_behind_valid_first_frame(self):
        one=(ZSTD_FILES/'tiny-3.zst').read_bytes()
        two=(ZSTD_FILES/'log-3.zst').read_bytes()
        for tail in (two[:-1],two[:5],b'garbage'):
            with self.subTest(tail_length=len(tail)),self.assertRaises(ValueError): unzstd.decompress(one+tail)

    def test_bad_compressed_log_is_reported_while_other_usage_survives(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            write_jsonl(root/'rollout-good.jsonl',codex_rows())
            bad=(ZSTD_FILES/'log-3.zst').read_bytes()[:-1]
            (root/'rollout-bad.jsonl.zst').write_bytes(bad)
            with patch.object(codex,'decoder',return_value=(unzstd.decompress,'plain python')):
                rows,issues=codex.read(codex.files([root]))
            self.assertEqual((len(rows),total(rows[0].tokens),len(issues)),(1,2100,1))

    def test_library_adapter_reads_all_frames_and_requires_each_eof(self):
        class Frame:
            def decompress(self,data):
                self.eof=data.startswith(b'F')
                self.unused_data=data[1:] if self.eof else b''
                return b'x'
        module=SimpleNamespace(ZstdDecompressor=lambda:SimpleNamespace(decompressobj=Frame))
        self.assertEqual(zstd._library_frames(module,b'FFF'),b'xxx')
        for broken in (b'',b'F?',b'?'):
            with self.subTest(broken=broken),self.assertRaises(ValueError): zstd._library_frames(module,broken)


class ClaudeCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        environment=dict(PLER_CACHE_DIR=str(self.root/'cache'),CLAUDE_CONFIG_DIR=str(self.root/'claude'),
                         CODEX_HOME=str(self.root/'codex'))
        self.environment=patch.dict(os.environ,environment)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.path=self.root/'claude/projects/shop/test.jsonl'
        self.good=claude_reply('s1','m1','r1',USAGE,
                              [dict(type='text',text=SECRET),dict(type='tool_use',name='Bash',id='t1',input=dict(command=SECRET))],
                              '2026-10-26T10:00:00Z')
        write_jsonl(self.path,[dict(type='user',sessionId='s1',uuid='u1',message=dict(content=SECRET)),self.good])

    def test_unchanged_claude_logs_are_not_reopened_and_text_never_enters_cache(self):
        first,sources=scan()
        with patch.object(claude_code,'_rows',side_effect=AssertionError('no reread')):
            second,again=scan()
        self.assertEqual([s.as_dict() for s in first],[s.as_dict() for s in second])
        self.assertIsNotNone(timestamp(sources.pop('observed_at')))
        self.assertIsNotNone(timestamp(again.pop('observed_at')))
        self.assertEqual(sources,again)
        stored=(self.root/'cache/claude.json').read_text('utf-8')
        for private in (SECRET,'command','"text"'):
            self.assertNotIn(private,stored)
        self.assertEqual((first[0].prompts,first[0].tools),(1,{'Bash':1}))

    def test_cache_hit_keeps_malformed_file_warning_and_good_rows(self):
        with self.path.open('a',encoding='utf-8') as stream: stream.write('{"unfinished":\n')
        first,sources=scan()
        with patch.object(claude_code,'_rows',side_effect=AssertionError('no reread')):
            second,again=scan()
        self.assertEqual((total(first[0].tokens),len(sources['skipped'])),(1260,1))
        self.assertEqual(sources['skipped'],again['skipped'])
        self.assertEqual([s.as_dict() for s in first],[s.as_dict() for s in second])

    def test_changed_copy_updates_largest_reply_without_counting_prompt_or_tool_twice(self):
        copied=self.path.with_name('z-copy.jsonl')
        rows=[json.loads(line) for line in self.path.read_text('utf-8').splitlines()]
        write_jsonl(copied,rows)
        first,_=scan()
        rows[-1]['message']['usage']['output_tokens']=100
        write_jsonl(copied,rows)
        with patch.object(claude_code,'_rows',wraps=claude_code._rows) as reader:
            second,_=scan()
        self.assertEqual(reader.call_count,1)
        self.assertEqual((second[0].calls,second[0].prompts,second[0].tools),(1,1,{'Bash':1}))
        self.assertEqual(total(second[0].tokens),total(first[0].tokens)+50)

    def test_access_failure_after_bad_row_is_retried_without_caching_partial_access(self):
        row=self.good
        class FailingStream:
            def __enter__(self): return self
            def __exit__(self,*_): return False
            def __iter__(self):
                yield json.dumps(row)
                yield '{"unfinished":'
                raise PermissionError('PRIVATE')
        for attempt in range(2):
            cache=FileCache('claude',version(claude_code))
            with patch('builtins.open',return_value=FailingStream()) as opened:
                issues=[]
                sessions=claude_code.read([self.path],issues,cache)
            cache.save()
            self.assertEqual((opened.call_count,total(sessions[0].tokens)),(1,1260))
            self.assertEqual(issues,[(str(self.path),'PermissionError')])
        self.assertFalse((self.root/'cache/claude.json').exists())

    def test_corrupt_cached_numbers_fall_back_to_original_claude_log(self):
        scan()
        target=self.root/'cache/claude.json'
        value=json.loads(target.read_text('utf-8'))
        rows=next(iter(value['files'].values()))['rows']
        next(row for row in rows if row['type']=='assistant')['message']['usage']['output_tokens']=999999
        target.write_text(json.dumps(value),'utf-8')
        sessions,_=scan()
        self.assertEqual(total(sessions[0].tokens),1260)

    def test_nonfinite_or_oversized_running_cost_does_not_hide_valid_usage(self):
        rows=[self.good,dict(type='cost-state',sessionId='s1',totalCostUSD=10**1000)]
        write_jsonl(self.path,rows)
        sessions,sources=scan()
        self.assertEqual((total(sessions[0].tokens),len(sources['skipped'])),(1260,1))

    def test_reading_helpers_changing_invalidates_old_codex_cache(self):
        path=self.root/'codex/sessions/rollout-test.jsonl'
        write_jsonl(path,codex_rows())
        helper=self.root/'decoder.py'
        helper.write_text('old validation','utf-8')
        with patch.object(unzstd,'__file__',str(helper)):
            scan()
            with patch.object(codex,'_rows',side_effect=AssertionError('reuse')): scan()
            helper.write_text('new validation','utf-8')
            with patch.object(codex,'_rows',wraps=codex._rows) as reader: scan()
        self.assertEqual(reader.call_count,1)


class CacheWriteTests(unittest.TestCase):
    def test_changed_source_is_not_saved_under_the_old_signature(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            path=Path(folder)/'source.jsonl'
            path.write_text('{}\n','utf-8')
            cache=FileCache('test','v1')
            self.assertIsNone(cache.get(path))
            path.write_text('{}\n{}\n','utf-8')
            cache.put(path,[dict(type='metadata')])
            cache.save()
            self.assertFalse(cache.path.exists())

    def test_failed_replace_preserves_old_cache_and_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            path=Path(folder)/'source.jsonl'
            path.write_text('{}\n','utf-8')
            cache=FileCache('test','v1')
            cache.get(path)
            cache.put(path,[dict(type='old')])
            cache.save()
            original=cache.path.read_bytes()
            cache=FileCache('test','v1')
            cache.get(path)
            cache.put(path,[dict(type='new')])
            with patch('pler.usage.cache.os.replace',side_effect=PermissionError('PRIVATE')): cache.save()
            self.assertEqual(cache.path.read_bytes(),original)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])


class LocalProjectTests(unittest.TestCase):
    def test_network_project_names_are_never_probed(self):
        roots=ProjectRoots()
        with patch.object(Path,'exists',side_effect=AssertionError('network probe')),patch.object(Path,'lstat',side_effect=AssertionError('network probe')):
            for name in ('//server/share/project','\\\\server\\share\\project','\\\\?\\UNC\\server\\share',
                         '\\/server/share/project','/\\server/share/project'):
                with self.subTest(name=name): self.assertEqual(roots.root(name),os.path.normpath(name))

    def test_reparse_project_ancestor_is_never_followed(self):
        with tempfile.TemporaryDirectory() as folder:
            roots=ProjectRoots(temp=Path(folder)/'other-temp')
            info=SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400)
            with patch.object(Path,'lstat',return_value=info),patch.object(Path,'exists',side_effect=AssertionError('followed link')):
                self.assertEqual(roots.root(folder),os.path.normpath(folder))

    def test_git_marker_symlink_is_not_followed_or_used_as_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'project'
            root.mkdir()
            child=root/'child'
            child.mkdir()
            real=Path.lstat
            def guarded(path,*args,**kwargs):
                if path==root/'.git': return SimpleNamespace(st_mode=stat.S_IFLNK,st_file_attributes=0)
                return real(path,*args,**kwargs)
            roots=ProjectRoots(temp=Path(folder)/'other-temp')
            with patch.object(Path,'lstat',guarded),patch.object(Path,'exists',side_effect=AssertionError('followed link')):
                self.assertEqual(roots.root(str(child)),os.path.normpath(str(child)))


if __name__=='__main__': unittest.main()
