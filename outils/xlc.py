"""Feuilles compilées xlce : détection des colonnes de chaînes + reconstruction."""
import struct
from codec import decode, DecodeError


def parse_xlc(b):
    """Retourne None si pas de chaînes, sinon dict(n, es, hend, strcols, slots, tail)."""
    if b[:4] != b'xlce':
        return None
    n, do, es = struct.unpack_from('<III', b, 4)
    hend = 16 + n * es
    if hend >= len(b) or es < 4:
        return None
    cols = {}
    for c in range(0, es - 3, 4):
        cols[c] = [struct.unpack_from('<I', b, 16 + r * es + c)[0] for r in range(n)]
    strcols = []
    for c, vals in cols.items():
        nz = set(v for v in vals if v)
        if nz and all(hend <= v < len(b) and (v == hend or b[v - 1] == 0) for v in nz):
            try:
                for v in nz:
                    decode(b, v)
                strcols.append(c)
            except DecodeError:
                pass
    if not strcols:
        return None
    refs = sorted(set(v for c in strcols for v in cols[c] if v))
    slots = []
    for v in refs:
        s, e = decode(b, v)
        slots.append(dict(off=v, text=s, end=e))
    for a, c in zip(slots, slots[1:]):
        assert c['off'] >= a['end']
        a['gap'] = b[a['end']:c['off']]
    slots[-1]['gap'] = b''
    return dict(n=n, es=es, hend=hend, strcols=strcols, slots=slots,
                head=b[refs[0] - (refs[0] - hend):refs[0]] if refs[0] > hend else b'',
                tail=b[slots[-1]['end']:], cols=cols)


def build_xlc(b, info, encoded):
    """encoded[i] = octets du slot i sans 0 final."""
    hend = info['hend']
    out = bytearray(b[:hend]) + info['head']
    newoff = {}
    for s, enc in zip(info['slots'], encoded):
        newoff[s['off']] = len(out)
        out += enc + b'\0' + s['gap']
    out += info['tail']
    for c in info['strcols']:
        for r, v in enumerate(info['cols'][c]):
            if v:
                struct.pack_into('<I', out, 16 + r * info['es'] + c, newoff[v])
    return bytes(out)
