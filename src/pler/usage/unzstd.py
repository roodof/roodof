"""Zstandard decompression in plain Python (RFC 8878) for computers that have neither Python 3.14, the
`zstandard` package nor a `zstd` program. Slower than those, same bytes. No dictionaries.
Frame bounds, declared content sizes and optional content checksums are checked."""

from .xxh64 import digest as xxh64

MAGIC = 0xFD2FB528

LL_BASE = list(range(16)) + [16, 18, 20, 22, 24, 28, 32, 40, 48, 64, 128, 256, 512, 1024, 2048, 4096,
                             8192, 16384, 32768, 65536]
LL_BITS = [0] * 16 + [1, 1, 1, 1, 2, 2, 3, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
ML_BASE = list(range(3, 35)) + [35, 37, 39, 41, 43, 47, 51, 59, 67, 83, 99, 131, 259, 515, 1027, 2051,
                                4099, 8195, 16387, 32771, 65539]
ML_BITS = [0] * 32 + [1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]


def _fail(what):
    raise ValueError('zstd: ' + what)


class _Back:
    """A bitstream read from its last byte backwards, as zstd writes FSE and Huffman streams."""

    def __init__(self, data):
        if not data or not data[-1]:
            _fail('bitstream has no end marker')
        last = data[-1]
        self.data, self.p, self.n = data, len(data) - 1, last.bit_length() - 1
        self.c, self.over = last, False

    def read(self, k):
        if not k:
            return 0
        n = self.n
        if n < k:
            p = self.p
            if p:
                q = p - 8 if p > 8 else 0
                self.c = ((self.c & ((1 << n) - 1)) << ((p - q) << 3)) | int.from_bytes(self.data[q:p], 'little')
                n += (p - q) << 3
                self.p = q
            if n < k:
                self.over = True
                value = (self.c << (k - n)) & ((1 << k) - 1)
                self.n = self.c = 0
                return value
        n -= k
        self.n = n
        return (self.c >> n) & ((1 << k) - 1)


def _counts(data, pos, max_log, max_symbol):
    """An FSE table description: (accuracy log, normalized counts, position after it)."""
    bits = int.from_bytes(data[pos:pos + 512], 'little')
    log = (bits & 15) + 5
    if log > max_log:
        _fail('table accuracy too high')
    at, remaining, threshold, width, counts = 4, (1 << log) + 1, 1 << log, log + 1, []
    while remaining > 1 and len(counts) <= max_symbol:
        largest = 2 * threshold - 1 - remaining
        low = (bits >> at) & (threshold - 1)
        if low < largest:
            count, at = low, at + width - 1
        else:
            count = (bits >> at) & (2 * threshold - 1)
            if count >= threshold:
                count -= largest
            at += width
        count -= 1
        remaining -= -count if count < 0 else count
        counts.append(count)
        if not count:
            while True:
                repeat = (bits >> at) & 3
                at += 2
                counts.extend([0] * repeat)
                if repeat != 3:
                    break
        while remaining < threshold:
            width -= 1
            threshold >>= 1
    if remaining != 1 or len(counts) > max_symbol + 1:
        _fail('bad table description')
    return log, counts, pos + (at + 7) // 8


def _table(log, counts):
    """FSE decoding table: (symbols, bit counts, state bases, accuracy log)."""
    size = 1 << log
    symbols, high, following = [0] * size, size - 1, []
    for symbol, count in enumerate(counts):
        if count == -1:
            symbols[high] = symbol
            high -= 1
        following.append(1 if count == -1 else count)
    step, mask, at = (size >> 1) + (size >> 3) + 3, size - 1, 0
    for symbol, count in enumerate(counts):
        for _ in range(count):
            symbols[at] = symbol
            at = (at + step) & mask
            while at > high:
                at = (at + step) & mask
    nbits, bases = [0] * size, [0] * size
    for state, symbol in enumerate(symbols):
        x = following[symbol]
        following[symbol] = x + 1
        nbits[state] = log - (x.bit_length() - 1)
        bases[state] = (x << nbits[state]) - size
    return symbols, nbits, bases, log


DEFAULTS = dict(
    ll=_table(6, [4, 3] + [2] * 11 + [1] * 3 + [2] * 9 + [3, 2] + [1] * 5 + [-1] * 4),
    of=_table(5, [1] * 6 + [2] * 3 + [1] * 15 + [-1] * 5),
    ml=_table(6, [1, 4, 3] + [2] * 6 + [1] * 37 + [-1] * 7))


def _huffman(data, pos):
    """Huffman tree description: ((symbols, bit counts, max bits), position after it)."""
    head = data[pos]
    pos += 1
    if head < 128:
        log, counts, start = _counts(data, pos, 6, 255)
        symbols, nbits, bases, log = _table(log, counts)
        stream, weights = _Back(data[start:pos + head]), []
        one, two = stream.read(log), stream.read(log)
        while len(weights) < 255:
            weights.append(symbols[one])
            one = bases[one] + stream.read(nbits[one])
            if stream.over:
                weights.append(symbols[two])
                break
            weights.append(symbols[two])
            two = bases[two] + stream.read(nbits[two])
            if stream.over:
                weights.append(symbols[one])
                break
        pos += head
    else:
        count = head - 127
        weights = [w for byte in data[pos:pos + (count + 1) // 2] for w in (byte >> 4, byte & 15)][:count]
        pos += (count + 1) // 2
    total = sum(1 << (w - 1) for w in weights if w)
    top = total.bit_length()
    rest = (1 << top) - total
    if not total or top > 11 or rest & (rest - 1):
        _fail('bad Huffman weights')
    weights.append(rest.bit_length())
    symbols, nbits = [], []
    for weight in range(1, top + 1):
        for symbol, w in enumerate(weights):
            if w == weight:
                symbols += [symbol] * (1 << (weight - 1))
                nbits += [top + 1 - weight] * (1 << (weight - 1))
    return [symbols, nbits, top, None], pos


def _literal_lookup(symbols, widths, top):
    """Decode one or two literals per bounded lookup, rather than a Python loop per byte."""
    bits = min(12, 2 * top)
    mask, shift, table = (1 << top) - 1, bits - top, []
    for value in range(1 << bits):
        first = value >> shift
        used = widths[first]
        second = ((value << used) >> shift) & mask
        combined = used + widths[second]
        if combined <= bits:
            table.append((bytes((symbols[first], symbols[second])), combined, 2))
        else:
            table.append((bytes((symbols[first],)), used, 1))
    return table, bits


def _huffman_stream(data, count, tree, out):
    if tree[3] is None:
        return _huffman_single(data, count, tree, out)
    symbols, nbits, top, (table, bits) = tree
    if not data or not data[-1]:
        _fail('bitstream has no end marker')
    last = data[-1]
    n, c, p, mask = last.bit_length() - 1, last, len(data) - 1, (1 << top) - 1
    from_bytes, append = int.from_bytes, out.append
    remaining, lookup_mask = count, (1 << bits) - 1
    while remaining:
        if n < bits:
            if p:
                q = p - 16 if p > 16 else 0
                c = ((c & ((1 << n) - 1)) << ((p - q) << 3)) | from_bytes(data[q:p], 'little')
                n += (p - q) << 3
                p = q
        if n >= bits and remaining >= 2:
            chunk, used, emitted = table[(c >> (n - bits)) & lookup_mask]
            out += chunk
            remaining -= emitted
            n -= used
            continue
        if n < top:
            v = (c << (top - n)) & mask
            append(symbols[v])
            n -= nbits[v]
            if n < 0:
                _fail('Huffman stream too short')
            remaining -= 1
            continue
        v = (c >> (n - top)) & mask
        append(symbols[v])
        n -= nbits[v]
        remaining -= 1
    if p or n:
        _fail('Huffman stream has extra bits')


def _huffman_single(data, count, tree, out):
    """Small literal blocks do not amortize construction of a larger lookup table."""
    symbols, nbits, top = tree[:3]
    if not data or not data[-1]:
        _fail('bitstream has no end marker')
    last = data[-1]
    n, c, p, mask = last.bit_length() - 1, last, len(data) - 1, (1 << top) - 1
    from_bytes, append = int.from_bytes, out.append
    for _ in range(count):
        if n < top:
            if p:
                q = p - 16 if p > 16 else 0
                c = ((c & ((1 << n) - 1)) << ((p - q) << 3)) | from_bytes(data[q:p], 'little')
                n += (p - q) << 3
                p = q
            if n < top:
                v = (c << (top - n)) & mask
                append(symbols[v])
                n -= nbits[v]
                if n < 0:
                    _fail('Huffman stream too short')
                continue
        v = (c >> (n - top)) & mask
        append(symbols[v])
        n -= nbits[v]
    if p or n:
        _fail('Huffman stream has extra bits')


def _literals(data, pos, state):
    first = data[pos]
    kind, form = first & 3, (first >> 2) & 3
    if kind < 2:
        if form in (0, 2):
            size, pos = first >> 3, pos + 1
        elif form == 1:
            size, pos = (first >> 4) + (data[pos + 1] << 4), pos + 2
        else:
            size, pos = (first >> 4) + (data[pos + 1] << 4) + (data[pos + 2] << 12), pos + 3
        if kind == 0:
            return data[pos:pos + size], pos + size
        return data[pos:pos + 1] * size, pos + 1
    width, bits = ((3, 10), (3, 10), (4, 14), (5, 18))[form]
    head = int.from_bytes(data[pos:pos + width], 'little')
    size, compressed = (head >> 4) & ((1 << bits) - 1), (head >> (4 + bits)) & ((1 << bits) - 1)
    pos += width
    end = pos + compressed
    if kind == 2:
        state['huffman'], pos = _huffman(data, pos)
    elif state.get('huffman') is None:
        _fail('repeated Huffman table without a previous one')
    tree = state['huffman']
    if size >= 32768 and tree[3] is None:
        tree[3] = _literal_lookup(*tree[:3])
    out = bytearray()
    if form == 0:
        _huffman_stream(data[pos:end], size, state['huffman'], out)
    else:
        sizes = [int.from_bytes(data[pos + 2 * i:pos + 2 * i + 2], 'little') for i in range(3)]
        pos += 6
        sizes.append(end - pos - sum(sizes))
        part = (size + 3) // 4
        for i, length in enumerate(sizes):
            _huffman_stream(data[pos:pos + length], part if i < 3 else size - 3 * part, state['huffman'], out)
            pos += length
    if len(out) != size:
        _fail('literal size mismatch')
    return bytes(out), end


def _block(data, pos, end, state, out):
    literals, pos = _literals(data, pos, state)
    first = data[pos]
    if first < 128:
        count, pos = first, pos + 1
    elif first < 255:
        count, pos = ((first - 128) << 8) + data[pos + 1], pos + 2
    else:
        count, pos = data[pos + 1] + (data[pos + 2] << 8) + 0x7F00, pos + 3
    if not count:
        out += literals
        return
    modes = data[pos]
    pos += 1
    tables = []
    for shift, name, max_log, max_symbol in ((6, 'll', 9, 35), (4, 'of', 8, 31), (2, 'ml', 9, 52)):
        mode = (modes >> shift) & 3
        if mode == 0:
            table = DEFAULTS[name]
        elif mode == 1:
            table, pos = ([data[pos]], [0], [0], 0), pos + 1
        elif mode == 2:
            log, counts, pos = _counts(data, pos, max_log, max_symbol)
            table = _table(log, counts)
        else:
            table = state.get(name)
            if table is None:
                _fail('repeated table without a previous one')
        state[name] = table
        tables.append(table)
    (l_sym, l_bits, l_base, l_log), (o_sym, o_bits, o_base, o_log), (m_sym, m_bits, m_base, m_log) = tables
    stream = _Back(data[pos:end])
    read = stream.read
    ls, os_, ms = read(l_log), read(o_log), read(m_log)
    rep, at = state['rep'], 0
    for i in range(count):
        oc, mc, lc = o_sym[os_], m_sym[ms], l_sym[ls]
        value = (1 << oc) + read(oc)
        match = ML_BASE[mc] + read(ML_BITS[mc])
        length = LL_BASE[lc] + read(LL_BITS[lc])
        if value > 3:
            offset = value - 3
            rep[2], rep[1], rep[0] = rep[1], rep[0], offset
        else:
            index = value - 1 if length else value
            if index == 0:
                offset = rep[0]
            elif index == 1:
                offset = rep[1]
                rep[1], rep[0] = rep[0], offset
            elif index == 2:
                offset = rep[2]
                rep[2], rep[1], rep[0] = rep[1], rep[0], offset
            else:
                offset = rep[0] - 1
                rep[2], rep[1], rep[0] = rep[1], rep[0], offset
        if i < count - 1:
            ls = l_base[ls] + read(l_bits[ls])
            ms = m_base[ms] + read(m_bits[ms])
            os_ = o_base[os_] + read(o_bits[os_])
        if length:
            out += literals[at:at + length]
            at += length
        start = len(out) - offset
        if start < 0 or offset <= 0:
            _fail('match before start of data')
        if match <= offset:
            out += out[start:start + match]
        else:
            chunk = out[start:]
            whole, part = divmod(match, offset)
            out += chunk * whole + chunk[:part]
    if stream.over or at > len(literals):
        _fail('corrupt sequences')
    out += literals[at:]


def decompress(data):
    """All frames of `data`, decompressed. Corrupt or truncated input raises ValueError."""
    try:
        return _frames(bytes(data))
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError('zstd: corrupt or truncated data') from error


def _frames(data):
    if not data:
        _fail('empty compressed file')
    out, pos = bytearray(), 0
    def need(size):
        if pos + size > len(data):
            _fail('truncated frame')
    while pos < len(data):
        need(4)
        magic = int.from_bytes(data[pos:pos + 4], 'little')
        if 0x184D2A50 <= magic <= 0x184D2A5F:
            need(8)
            size = int.from_bytes(data[pos + 4:pos + 8], 'little')
            need(8 + size)
            pos += 8 + size
            continue
        if magic != MAGIC:
            _fail('not a zstd frame')
        need(5)
        flags = data[pos + 4]
        if flags & 8:
            _fail('reserved frame flag')
        pos += 5
        single = flags & 0x20
        if not single:
            need(1)
            pos += 1
        dictionary = (0, 1, 2, 4)[flags & 3]
        content_size_bytes = ((1 if single else 0), 2, 4, 8)[flags >> 6]
        need(dictionary + content_size_bytes)
        if dictionary and int.from_bytes(data[pos:pos + dictionary], 'little'):
            _fail('dictionaries are not supported')
        pos += dictionary
        content_size = int.from_bytes(data[pos:pos + content_size_bytes], 'little') if content_size_bytes else None
        if content_size_bytes == 2:
            content_size += 256
        pos += content_size_bytes
        frame, state = bytearray(), dict(rep=[1, 4, 8])
        while True:
            need(3)
            head = int.from_bytes(data[pos:pos + 3], 'little')
            kind, size = (head >> 1) & 3, head >> 3
            pos += 3
            if size > 131072:
                _fail('block too large')
            need(1 if kind == 1 else size)
            previous_size = len(frame)
            if kind == 0:
                frame += data[pos:pos + size]
                pos += size
            elif kind == 1:
                frame += data[pos:pos + 1] * size
                pos += 1
            elif kind == 2:
                _block(data[pos:pos + size], 0, size, state, frame)
                pos += size
            else:
                _fail('reserved block type')
            if len(frame) - previous_size > 131072:
                _fail('decoded block too large')
            if head & 1:
                break
        if flags & 4:
            need(4)
            if int.from_bytes(data[pos:pos + 4], 'little') != xxh64(frame) & 0xFFFFFFFF:
                _fail('content checksum mismatch')
            pos += 4
        if content_size is not None and len(frame) != content_size:
            _fail('content size mismatch')
        out += frame
    return bytes(out)
