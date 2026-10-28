"""XXH64 with seed zero, for zstd content checksums. No authentication claim.

Algorithm: https://github.com/Cyan4973/xxHash/blob/dev/doc/xxhash_spec.md
"""
from struct import iter_unpack, unpack_from

MASK = (1 << 64) - 1
P1, P2 = 0x9E3779B185EBCA87, 0xC2B2AE3D27D4EB4F
P3, P4, P5 = 0x165667B19E3779F9, 0x85EBCA77C2B2AE63, 0x27D4EB2F165667C5


def _rotate(value, bits):
    return ((value << bits) | (value >> (64 - bits))) & MASK


def _round(value, lane):
    return (_rotate((value + lane * P2) & MASK, 31) * P1) & MASK


def digest(data):
    size, at = len(data), 0
    if size >= 32:
        a, b, c, d = (P1 + P2) & MASK, P2, 0, (-P1) & MASK
        at = size - size % 32
        # Four independent lanes; keep the hot loop free of per-lane calls.
        for x, y, z, w in iter_unpack('<QQQQ', memoryview(data)[:at]):
            a = (a + x * P2) & MASK
            a = (((a << 31) | (a >> 33)) * P1) & MASK
            b = (b + y * P2) & MASK
            b = (((b << 31) | (b >> 33)) * P1) & MASK
            c = (c + z * P2) & MASK
            c = (((c << 31) | (c >> 33)) * P1) & MASK
            d = (d + w * P2) & MASK
            d = (((d << 31) | (d >> 33)) * P1) & MASK
        value = (_rotate(a, 1) + _rotate(b, 7) + _rotate(c, 12) + _rotate(d, 18)) & MASK
        for lane in (a, b, c, d):
            value = ((value ^ _round(0, lane)) * P1 + P4) & MASK
    else:
        value = P5
    value = (value + size) & MASK
    while at + 8 <= size:
        value ^= _round(0, unpack_from('<Q', data, at)[0])
        value = (_rotate(value, 27) * P1 + P4) & MASK
        at += 8
    if at + 4 <= size:
        value ^= (unpack_from('<I', data, at)[0] * P1) & MASK
        value = (_rotate(value, 23) * P2 + P3) & MASK
        at += 4
    while at < size:
        value ^= data[at] * P5 & MASK
        value = _rotate(value, 11) * P1 & MASK
        at += 1
    value ^= value >> 33
    value = value * P2 & MASK
    value ^= value >> 29
    value = value * P3 & MASK
    return value ^ (value >> 32)
