"""Private work titles survive verified recovery; ordinary reports never carry them."""
import hashlib
import io
import json
import zipfile
from unittest.mock import patch

from pler.usage import backup,work_items
from test_adoption_api import IsolatedMetadata

TITLE='PRIVATE-WORK-TITLE-CANARY'


class WorkBackupTests(IsolatedMetadata):
    def rewrite(self,data,change):
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            members={name:package.read(name) for name in package.namelist()}
        manifest=json.loads(members.pop(backup.MANIFEST));change(manifest,members)
        manifest['files']={name:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in members.items()}
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as package:
            package.writestr(backup.MANIFEST,json.dumps(manifest).encode())
            for name,raw in members.items():package.writestr(name,raw)
        return output.getvalue()

    def test_work_items_and_shared_links_roundtrip_without_reader_cache_or_live_sources(self):
        store=work_items.Folder(self.cache)
        one=store.mutate('create',title=TITLE,session='a'*24)['id']
        two=store.mutate('create',title='Second',session='a'*24)['id']
        store.mutate('link',identity=one,session='b'*24)
        data=backup.create();summary=backup.inspect(data)
        self.assertEqual((summary['work_items'],summary['work_links']),(2,3))
        self.assertIn(TITLE.encode(),data,'private backup intentionally contains manual labels')
        self.assertNotIn(TITLE,json.dumps(summary))
        restored=self.root/'recovered';backup.restore(data,restored)
        self.assertEqual(work_items.Folder(restored).read(),store.read())
        self.assertEqual(set(restored.iterdir()),{restored/work_items.FILENAME,restored/'metadata-archive-generation.json'})

    def test_older_backup_without_optional_work_file_remains_valid_and_restores_no_work(self):
        data=backup.create()
        old=self.rewrite(data,lambda manifest,members:manifest.update(version='0.2.25'))
        info=backup.inspect(old)
        self.assertEqual((info['work_items'],info['work_links']),(0,0))
        restored=self.root/'old-recovered';backup.restore(old,restored)
        self.assertEqual(work_items.Folder(restored).read(),{})

    def test_corrupt_or_extra_private_work_payload_is_refused_even_with_matching_checksums(self):
        work_items.Folder(self.cache).mutate('create',title=TITLE)
        data=backup.create()
        def add_field(manifest,members):
            value=json.loads(members[work_items.FILENAME])
            next(iter(value['items'].values()))['prompt']='PRIVATE-PROMPT-CANARY'
            members[work_items.FILENAME]=json.dumps(value).encode()
        for changed in (self.rewrite(data,add_field),
                        self.rewrite(data,lambda manifest,members:members.update({work_items.FILENAME:b'{broken'}))):
            with self.assertRaises(backup.BackupError):backup.inspect(changed)
            with self.assertRaises(backup.BackupError):backup.restore(changed,self.root/'must-not-exist')
            self.assertFalse((self.root/'must-not-exist').exists())

    def test_bad_saved_work_file_cannot_silently_disappear_from_a_successful_backup(self):
        self.cache.mkdir();path=self.cache/work_items.FILENAME;path.write_bytes(b'{broken')
        with self.assertRaises(backup.BackupError):backup.create()
        self.assertEqual(path.read_bytes(),b'{broken')

    def test_restore_does_not_merge_or_overwrite_the_current_work_store(self):
        store=work_items.Folder(self.cache);store.mutate('create',title=TITLE)
        data=backup.create();before=(self.cache/work_items.FILENAME).read_bytes()
        with self.assertRaises(backup.BackupError):backup.restore(data,self.cache)
        self.assertEqual((self.cache/work_items.FILENAME).read_bytes(),before)
