"""RSA/SHA-256 release verification using Windows CNG, never a remote trust key."""
import base64
import ctypes as c
import hashlib
import os
import struct


class Padding(c.Structure):
    _fields_=[('algorithm',c.c_wchar_p)]


def api():
    if os.name!='nt':raise ValueError('Windows signature verifier unavailable')
    dll=c.WinDLL('bcrypt.dll')
    signatures={
        'BCryptOpenAlgorithmProvider':([c.POINTER(c.c_void_p),c.c_wchar_p,c.c_wchar_p,c.c_ulong]),
        'BCryptImportKeyPair':([c.c_void_p,c.c_void_p,c.c_wchar_p,c.POINTER(c.c_void_p),c.c_void_p,c.c_ulong,c.c_ulong]),
        'BCryptVerifySignature':([c.c_void_p,c.c_void_p,c.c_void_p,c.c_ulong,c.c_void_p,c.c_ulong,c.c_ulong]),
        'BCryptCloseAlgorithmProvider':([c.c_void_p,c.c_ulong]),
        'BCryptDestroyKey':([c.c_void_p]),
    }
    for name,args in signatures.items():
        fn=getattr(dll,name);fn.argtypes=args;fn.restype=c.c_long
    return dll


def public_blob(encoded):
    if not isinstance(encoded,str) or len(encoded)>1200:raise ValueError('invalid public key')
    blob=base64.b64decode(encoded,validate=True)
    if len(blob)<24:raise ValueError('invalid public key')
    magic,bits,exponent,modulus,p,q=struct.unpack('<6I',blob[:24])
    if (magic!=0x31415352 or bits not in (3072,4096) or modulus!=bits//8 or exponent!=3 or p or q
            or len(blob)!=24+exponent+modulus or blob[24:27]!=b'\x01\x00\x01' or not blob[27]&128):
        raise ValueError('invalid public key')
    return blob


def key_id(encoded):return hashlib.sha256(public_blob(encoded)).hexdigest()[:24]


class InstallationLease:
    """Shared while an app runs, exclusive during a version switch; OS releases crashed owners."""
    def __init__(self,root,exclusive=False):
        self.kernel=c.WinDLL('kernel32.dll',use_last_error=True)
        self.kernel.CreateFileW.argtypes=[c.c_wchar_p,c.c_ulong,c.c_ulong,c.c_void_p,c.c_ulong,c.c_ulong,c.c_void_p]
        self.kernel.CreateFileW.restype=c.c_void_p
        self.kernel.CloseHandle.argtypes=[c.c_void_p];self.kernel.CloseHandle.restype=c.c_int
        self.handle=self.kernel.CreateFileW(str(root/'.pler-running.lock'),0xc0000000 if exclusive else 0x80000000,0 if exclusive else 3,None,4,128,None)
        if self.handle in (None,c.c_void_p(-1).value):self.handle=None;raise ValueError('installation in use')

    def close(self):
        if self.handle:self.kernel.CloseHandle(self.handle);self.handle=None


def process_running(pid):
    if type(pid) is not int or not 0<pid<2**32:raise ValueError('invalid process')
    kernel=c.WinDLL('kernel32.dll',use_last_error=True)
    kernel.OpenProcess.argtypes=[c.c_ulong,c.c_int,c.c_ulong];kernel.OpenProcess.restype=c.c_void_p
    kernel.WaitForSingleObject.argtypes=[c.c_void_p,c.c_ulong];kernel.WaitForSingleObject.restype=c.c_ulong
    kernel.CloseHandle.argtypes=[c.c_void_p];kernel.CloseHandle.restype=c.c_int
    handle=kernel.OpenProcess(0x100000,0,pid)
    if not handle:return c.get_last_error()!=87  # access-denied/unknown owners remain protected
    try:return kernel.WaitForSingleObject(handle,0)==258
    finally:kernel.CloseHandle(handle)


def private_directory(path):
    """Protect staging (including its private backup) even beside a shared installation."""
    if os.name!='nt':os.chmod(path,0o700);return
    kernel=c.WinDLL('kernel32.dll');adv=c.WinDLL('advapi32.dll');token=c.c_void_p();sid=c.c_wchar_p();descriptor=c.c_void_p()
    kernel.GetCurrentProcess.restype=c.c_void_p
    kernel.CloseHandle.argtypes=[c.c_void_p];kernel.LocalFree.argtypes=[c.c_void_p];kernel.LocalFree.restype=c.c_void_p
    adv.OpenProcessToken.argtypes=[c.c_void_p,c.c_ulong,c.POINTER(c.c_void_p)];adv.OpenProcessToken.restype=c.c_int
    adv.GetTokenInformation.argtypes=[c.c_void_p,c.c_int,c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong)];adv.GetTokenInformation.restype=c.c_int
    adv.ConvertSidToStringSidW.argtypes=[c.c_void_p,c.POINTER(c.c_wchar_p)];adv.ConvertSidToStringSidW.restype=c.c_int
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes=[c.c_wchar_p,c.c_ulong,c.POINTER(c.c_void_p),c.c_void_p]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype=c.c_int
    adv.SetFileSecurityW.argtypes=[c.c_wchar_p,c.c_ulong,c.c_void_p];adv.SetFileSecurityW.restype=c.c_int
    try:
        if not adv.OpenProcessToken(kernel.GetCurrentProcess(),8,c.byref(token)):raise ValueError('private staging ACL')
        size=c.c_ulong();adv.GetTokenInformation(token,1,None,0,c.byref(size));buffer=c.create_string_buffer(size.value)
        if not adv.GetTokenInformation(token,1,buffer,size.value,c.byref(size)):raise ValueError('private staging ACL')
        owner=c.cast(buffer,c.POINTER(c.c_void_p)).contents.value
        if not adv.ConvertSidToStringSidW(owner,c.byref(sid)):raise ValueError('private staging ACL')
        sddl='D:P(A;OICI;FA;;;'+sid.value+')(A;OICI;FA;;;SY)'
        if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,c.byref(descriptor),None):raise ValueError('private staging ACL')
        if not adv.SetFileSecurityW(str(path),0x80000004,descriptor):raise ValueError('private staging ACL')
    finally:
        if descriptor:kernel.LocalFree(descriptor)
        if sid:kernel.LocalFree(c.cast(sid,c.c_void_p))
        if token:kernel.CloseHandle(token)


def verify(encoded,data,signature):
    blob=public_blob(encoded)
    if not isinstance(signature,bytes) or len(signature)!=(len(blob)-27):return False
    dll=api();algorithm=c.c_void_p();key=c.c_void_p()
    try:
        if dll.BCryptOpenAlgorithmProvider(c.byref(algorithm),'RSA',None,0):raise ValueError('signature provider')
        if dll.BCryptImportKeyPair(algorithm,None,'RSAPUBLICBLOB',c.byref(key),c.create_string_buffer(blob),len(blob),0):
            raise ValueError('signature key')
        digest=hashlib.sha256(data).digest();padding=Padding('SHA256')
        return dll.BCryptVerifySignature(key,c.byref(padding),c.create_string_buffer(digest),len(digest),
                                         c.create_string_buffer(signature),len(signature),2)==0
    finally:
        if key:dll.BCryptDestroyKey(key)
        if algorithm:dll.BCryptCloseAlgorithmProvider(algorithm,0)
