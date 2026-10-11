import struct

def is_pakd(b):
    return len(b) >= 16 and b[:4] == b'pakd'

def parse_pakd(b):
    """Retourne (entries[(rawid, data)], has_ids, total_size)."""
    n = struct.unpack_from('<I', b, 4)[0]
    offs = list(struct.unpack_from('<%dI' % n, b, 8))
    total = struct.unpack_from('<I', b, 8 + 4 * n)[0]
    ids = [0] * n
    if n:
        hsz = 4 + 4 + 4 * n + 4 + 4
        idsz = offs[0] - hsz
        k = 0
        while k < n and k * 4 < idsz:
            ids[k] = struct.unpack_from('<I', b, 12 + 4 * n + 4 * k)[0]; k += 1
    ends = offs[1:] + [total]
    return [(ids[i], b[offs[i]:ends[i]]) for i in range(n)], any(ids), total

def build_pakd(entries, align=16):
    """entries: [(rawid, data)]. Layout identique à l'original (alignement 16)."""
    n = len(entries)
    has_ids = any(e[0] for e in entries)
    hsz = 4 + 4 + 4 * n + 4 + (4 * n if has_ids else 0) + 4
    hsz = (hsz + 15) & ~15
    offs, body, pos = [], bytearray(), hsz
    for _, d in entries:
        offs.append(pos)
        body += d
        pad = (-len(d)) % align
        body += b'\0' * pad
        pos += len(d) + pad
    h = bytearray(b'pakd' + struct.pack('<I', n) + struct.pack('<%dI' % n, *offs) + struct.pack('<I', pos))
    if has_ids:
        h += struct.pack('<%dI' % n, *[e[0] for e in entries])
    h += b'\0' * (hsz - len(h))
    return bytes(h + body)
