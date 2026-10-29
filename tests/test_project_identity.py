"""Distinct safe project names and temporary repositories. Invented paths/files only."""
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler.usage.projects import ProjectRoots, assign, labels
from pler.usage.records import Session


class ProjectDisplayTests(unittest.TestCase):
    def display(self, paths, lang='en'):
        return labels(paths,lang=lang,home='/invented/home',temp='/invented/temp')

    def test_duplicate_short_names_get_distinct_opaque_suffixes_without_ancestors(self):
        paths=['/PRIVATE-CLIENT-ONE/work/client/app','/PRIVATE-CLIENT-TWO/archive/client/app']
        with patch.object(Path,'lstat',side_effect=AssertionError('display probed a path')):
            shown=self.display(paths)
        self.assertEqual(len(set(shown.values())),2)
        for name in shown.values(): self.assertRegex(name,r'^client/app #[0-9a-f]{8}$')
        encoded=json.dumps(list(shown.values()))
        for secret in ('PRIVATE-CLIENT-ONE','PRIVATE-CLIENT-TWO','archive','work'):
            self.assertNotIn(secret,encoded)

    def test_full_mapping_is_stable_under_reordering_duplicates_and_generators(self):
        paths=['/a/client/app','/b/client/app','/c/server/api']
        first=self.display(paths)
        self.assertEqual(first,self.display(reversed(paths)))
        self.assertEqual(first,self.display(iter(paths+paths)))
        self.assertEqual(first['/c/server/api'],'server/api')

    def test_unique_names_keep_the_existing_two_folder_display(self):
        shown=self.display(['/clients/shop','/work/engine/src'])
        self.assertEqual(shown,{'/clients/shop':'clients/shop','/work/engine/src':'engine/src'})

    def test_unknown_home_and_temporary_labels_are_localized(self):
        paths=[None,'','/invented/home','/invented/temp']
        english=self.display(paths)
        turkish=self.display(paths,'tr')
        self.assertEqual(english[None],'Unknown project')
        self.assertEqual(english[''],english[None])
        self.assertEqual(english['/invented/home'],'Home folder (no project)')
        self.assertEqual(english['/invented/temp'],'Temporary folders')
        self.assertEqual(turkish[None],'Proje bilinmiyor')
        self.assertEqual(turkish['/invented/home'],'Ev klasörü (proje dışı)')
        self.assertNotEqual(turkish['/invented/temp'],english['/invented/temp'])

    def test_equivalent_host_spellings_do_not_invent_an_extra_project(self):
        paths=[os.path.join(os.sep,'invented','client','app'),
               os.path.join(os.sep,'invented','client','app')+os.sep]
        shown=self.display(paths)
        self.assertEqual(len(set(shown.values())),1)
        self.assertNotIn('#',next(iter(shown.values())))

    def test_windows_paths_follow_the_host_identity_rules(self):
        paths=['C:/PRIVATE-ONE/client/app','D:/PRIVATE-TWO/client/app']
        shown=self.display(paths)
        self.assertEqual(len(set(shown.values())),2)
        self.assertTrue(all(name.startswith('client/app #') for name in shown.values()))
        if os.name=='nt':
            variants=['C:/client/App','c:\\CLIENT\\app']
            equivalent=self.display(variants)
            self.assertEqual(len(set(equivalent.values())),1)
            self.assertNotIn('#',next(iter(equivalent.values())))

    def test_case_distinct_posix_projects_remain_distinct(self):
        if os.name=='nt': self.skipTest('POSIX case-sensitive project identity')
        shown=self.display(['/work/client/App','/work/client/app'])
        self.assertEqual(len({name.casefold() for name in shown.values()}),2)

    def test_colliding_hash_prefixes_expand_until_the_names_are_distinct(self):
        class Digest:
            def __init__(self,value): self.value=value
            def hexdigest(self): return 'a'*8+('1' if b'one' in self.value else '2')+'0'*55
        with patch('pler.usage.projects.hashlib.sha256',side_effect=Digest):
            shown=self.display(['/one/client/app','/two/client/app'])
        self.assertEqual(len(set(shown.values())),2)
        self.assertTrue(all(re.fullmatch(r'client/app #[a-f0-9]{9}',name) for name in shown.values()))


class TemporaryRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.scratch=self.base/'shared-temp'
        self.home=self.base/'home'
        self.scratch.mkdir()
        self.home.mkdir()

    def roots(self): return ProjectRoots(self.home,self.scratch)

    def test_separate_repositories_inside_temp_keep_their_own_project(self):
        first,second=self.scratch/'run-one'/'app',self.scratch/'run-two'/'app'
        for path in (first,second):
            (path/'.git').mkdir(parents=True)
            (path/'src').mkdir()
        roots=self.roots()
        self.assertEqual(roots.root(str(first/'src')),os.path.normpath(str(first)))
        self.assertEqual(roots.root(str(second/'src')),os.path.normpath(str(second)))
        sessions=[Session('codex','one','invented-one',project=str(first/'src')),
                  Session('codex','two','invented-two',project=str(second/'src'))]
        assigned=assign(sessions,self.home,self.scratch)
        self.assertEqual({row.project for row in assigned},{os.path.normpath(str(first)),os.path.normpath(str(second))})

    def test_plain_temporary_work_keeps_the_shared_bucket(self):
        plain=self.scratch/'plain'/'task'
        plain.mkdir(parents=True)
        roots=self.roots()
        for path in (plain,self.scratch/'not-created',self.scratch):
            with self.subTest(path=path): self.assertEqual(roots.root(str(path)),os.path.normpath(str(self.scratch)))

    def test_shared_temp_or_ancestor_git_markers_do_not_swallow_temporary_work(self):
        (self.base/'.git').mkdir()
        (self.scratch/'.git').mkdir()
        child=self.scratch/'plain'
        child.mkdir()
        real=Path.lstat
        probes=[]
        def guarded(path,*args,**kwargs):
            if path.name=='.git': probes.append(path)
            return real(path,*args,**kwargs)
        with patch.object(Path,'lstat',guarded): result=self.roots().root(str(child))
        self.assertEqual(result,os.path.normpath(str(self.scratch)))
        self.assertNotIn(self.base/'.git',probes)
        self.assertNotIn(self.scratch/'.git',probes)

    def test_similar_sibling_name_is_not_a_temporary_descendant(self):
        sibling=self.base/'shared-temp-files'
        sibling.mkdir()
        self.assertEqual(self.roots().root(str(sibling)),os.path.normpath(str(sibling)))

    def test_a_worktree_gitdir_marker_keeps_its_root_below_temp(self):
        worktree=self.scratch/'worktree'
        worktree.mkdir()
        (worktree/'.git').write_text('gitdir: ../invented-metadata\n','ascii')
        self.assertEqual(self.roots().root(str(worktree)),os.path.normpath(str(worktree)))

    def test_network_projects_are_never_probed(self):
        with patch.object(Path,'lstat',side_effect=AssertionError('network probe')):
            for path in ('//invented-server/share/project',r'\\invented-server\share\project'):
                self.assertEqual(self.roots().root(path),os.path.normpath(path))

    def test_a_temporary_reparse_ancestor_is_not_followed(self):
        child=self.scratch/'linked'/'task'
        real=Path.lstat
        def guarded(path,*args,**kwargs):
            if path==self.scratch/'linked': return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400)
            return real(path,*args,**kwargs)
        with patch.object(Path,'lstat',guarded),patch.object(Path,'exists',side_effect=AssertionError('followed a link')):
            self.assertEqual(self.roots().root(str(child)),os.path.normpath(str(self.scratch)))


if __name__=='__main__':unittest.main()
