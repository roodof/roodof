"""Maintainer-only release signing. Private keys are user-bound DPAPI files outside source.

No signing key or private blob is printed, included in the application or sent to a service.
"""
import argparse
import base64
import ctypes as c
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pler import update_crypto as crypto


class Blob(c.Structure):_fields_=[('size',c.c_ulong),('data',c.c_void_p)]


def protect(data,decrypt=False):
    dll=c.WinDLL('crypt32.dll');kernel=c.WinDLL('kernel32.dll')
    fn=dll.CryptUnprotectData if decrypt else dll.CryptProtectData
    fn.argtypes=[c.POINTER(Blob),c.c_void_p,c.c_void_p,c.c_void_p,c.c_void_p,c.c_ulong,c.POINTER(Blob)];fn.restype=c.c_int
    kernel.LocalFree.argtypes=[c.c_void_p];kernel.LocalFree.restype=c.c_void_p
    buffer=c.create_string_buffer(data);source=Blob(len(data),c.cast(buffer,c.c_void_p));output=Blob()
    if not fn(c.byref(source),None,None,None,None,1,c.byref(output)):raise ValueError('private key protection failed')
    try:return c.string_at(output.data,output.size)
    finally:kernel.LocalFree(output.data)


def signing_key(private=None):
    dll=crypto.api();algorithm=c.c_void_p();key=c.c_void_p()
    if dll.BCryptOpenAlgorithmProvider(c.byref(algorithm),'RSA',None,0):raise ValueError('signature provider')
    if private is None:
        dll.BCryptGenerateKeyPair.argtypes=[c.c_void_p,c.POINTER(c.c_void_p),c.c_ulong,c.c_ulong];dll.BCryptGenerateKeyPair.restype=c.c_long
        dll.BCryptFinalizeKeyPair.argtypes=[c.c_void_p,c.c_ulong];dll.BCryptFinalizeKeyPair.restype=c.c_long
        if dll.BCryptGenerateKeyPair(algorithm,c.byref(key),3072,0) or dll.BCryptFinalizeKeyPair(key,0):raise ValueError('key generation failed')
    elif dll.BCryptImportKeyPair(algorithm,None,'RSAFULLPRIVATEBLOB',c.byref(key),c.create_string_buffer(private),len(private),0):
        raise ValueError('private key unavailable')
    return dll,algorithm,key


def export(dll,key,kind):
    fn=dll.BCryptExportKey;fn.argtypes=[c.c_void_p,c.c_void_p,c.c_wchar_p,c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong),c.c_ulong];fn.restype=c.c_long
    size=c.c_ulong()
    if fn(key,None,kind,None,0,c.byref(size),0):raise ValueError('key export failed')
    buffer=c.create_string_buffer(size.value)
    if fn(key,None,kind,buffer,size.value,c.byref(size),0):raise ValueError('key export failed')
    return buffer.raw[:size.value]


def generate():
    dll,algorithm,key=signing_key()
    try:return export(dll,key,'RSAFULLPRIVATEBLOB'),base64.b64encode(export(dll,key,'RSAPUBLICBLOB')).decode('ascii')
    finally:dll.BCryptDestroyKey(key);dll.BCryptCloseAlgorithmProvider(algorithm,0)


def sign(private,payload):
    dll,algorithm,key=signing_key(private)
    try:
        fn=dll.BCryptSignHash;fn.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_ulong,c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong),c.c_ulong];fn.restype=c.c_long
        digest=hashlib.sha256(payload).digest();padding=crypto.Padding('SHA256');size=c.c_ulong()
        if fn(key,c.byref(padding),c.create_string_buffer(digest),len(digest),None,0,c.byref(size),2):raise ValueError('signing failed')
        buffer=c.create_string_buffer(size.value)
        if fn(key,c.byref(padding),c.create_string_buffer(digest),len(digest),buffer,size.value,c.byref(size),2):raise ValueError('signing failed')
        public=base64.b64encode(export(dll,key,'RSAPUBLICBLOB')).decode('ascii')
        return public,buffer.raw[:size.value]
    finally:dll.BCryptDestroyKey(key);dll.BCryptCloseAlgorithmProvider(algorithm,0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    new=sub.add_parser('create-key');new.add_argument('--private-key',type=Path,required=True);new.add_argument('--public-keys',type=Path,required=True)
    release=sub.add_parser('sign');release.add_argument('--private-key',type=Path,required=True);release.add_argument('--package',type=Path,required=True)
    release.add_argument('--version',required=True);release.add_argument('--output',type=Path,required=True)
    release.add_argument('--notes-en',required=True);release.add_argument('--notes-tr',required=True)
    args=parser.parse_args();private=args.private_key.resolve()
    if ROOT==private or ROOT in private.parents or ROOT.parent/'sites' in private.parents:parser.error('Private signing keys must stay outside application and Site source.')
    if args.action=='create-key':
        if private.exists() or args.public_keys.exists() and json.loads(args.public_keys.read_text())['keys']:parser.error('Refusing to replace existing keys.')
        secret,public=generate();private.parent.mkdir(parents=True,exist_ok=True)
        with private.open('xb') as file:file.write(protect(secret))
        args.public_keys.write_text(json.dumps(dict(format=1,keys={crypto.key_id(public):public}),indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(key_id=crypto.key_id(public),private_key_protection='Windows current-user DPAPI',public_keys=str(args.public_keys))))
    else:
        from pler.updates import canonical,validate_payload
        now=datetime.now(timezone.utc).replace(microsecond=0)
        payload=dict(format=1,product='pler',channel='early-beta',platform='windows-x64',version=args.version,
                     published_at=now.isoformat(),expires_at=(now+timedelta(days=90)).isoformat(),
                     url='https://roodof.com/downloads/PLER-'+args.version+'-windows-x64.zip',
                     sha256=hashlib.sha256(args.package.read_bytes()).hexdigest(),size=args.package.stat().st_size,
                     compatibility=dict(updater=2,schema=2,work=3,backup=1),notes=dict(en=args.notes_en,tr=args.notes_tr))
        validate_payload(payload)
        public,signature=sign(protect(private.read_bytes(),True),canonical(payload))
        envelope=dict(payload=payload,key_id=crypto.key_id(public),signature=base64.b64encode(signature).decode('ascii'))
        with args.output.open('x',encoding='utf-8') as file:json.dump(envelope,file,ensure_ascii=False,indent=2);file.write('\n')
        print(json.dumps(dict(version=args.version,key_id=envelope['key_id'],sha256=payload['sha256'],output=str(args.output))))


if __name__=='__main__':main()
