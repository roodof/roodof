"""Hand-encoded prefix streams exercise the bounded lookup and its long-code fallback."""
import unittest

from pler.usage import unzstd


def prefix_tree():
    # A complete tree with twelve byte symbols and code lengths from 1 through 11.
    codes=['1'*n+'0' for n in range(10)]+['1'*10+'0','1'*11]
    top=max(map(len,codes));symbols=[None]*(1<<top);widths=[None]*(1<<top)
    for symbol,code in enumerate(codes):
        width=len(code);start=int(code,2)<<(top-width);size=1<<(top-width)
        symbols[start:start+size]=[symbol]*size;widths[start:start+size]=[width]*size
    return codes,[symbols,widths,top,None]


def packed(bits):
    value=(1<<len(bits))|int(bits or '0',2)
    return value.to_bytes((len(bits)+8)//8,'little')


class LiteralBoundaryTests(unittest.TestCase):
    def test_short_long_and_exact_lookup_boundary_pairs_decode_every_byte(self):
        codes,tree=prefix_tree();tree[3]=unzstd._literal_lookup(*tree[:3])
        patterns=[[0],[10],[11],[10,0],[0,10],[10,10],[11,11],[0,0,11,0,10,11]*17]
        for pattern in patterns:
            with self.subTest(pattern=pattern[:6],length=len(pattern)):
                stream=packed(''.join(codes[i] for i in pattern));expected=bytes(pattern)
                lookup=bytearray();single=bytearray()
                unzstd._huffman_stream(stream,len(pattern),tree,lookup)
                unzstd._huffman_single(stream,len(pattern),tree,single)
                self.assertEqual(lookup,expected);self.assertEqual(single,expected)

    def test_extra_bits_missing_code_bits_and_missing_end_markers_still_fail(self):
        codes,tree=prefix_tree();tree[3]=unzstd._literal_lookup(*tree[:3])
        valid=codes[10]+codes[11]
        for stream in (packed(valid+'0'),packed(valid[:-1]),b'',b'\x00'):
            with self.subTest(stream=stream),self.assertRaises(ValueError):
                unzstd._huffman_stream(stream,2,tree,bytearray())


if __name__=='__main__':unittest.main()
