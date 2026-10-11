"""Arborescence des fichiers du jeu : FILETABLE -> BIN -> pakd imbriqués."""
import os, struct
from filetable import FileTable
from pakd import is_pakd, parse_pakd


class Game:
    def __init__(self, usrdir):
        self.u = usrdir
        self._orig_ft = open(os.path.join(usrdir, 'FILETABLE.BIN'), 'rb').read()
        self.ft = FileTable(self._orig_ft)
        self._bins = {}

    def bin(self, did):
        if did not in self._bins:
            self._bins[did] = open(os.path.join(self.u, '%04X.BIN' % did), 'rb').read()
        return self._bins[did]

    def files(self):
        for d in self.ft.dirs:
            raw = self.bin(d['id'])
            for f in d['files']:
                o = self.ft.offset(d, f)
                yield d['id'], f['id'], raw[o:o + f['size']]

    def leaves(self):
        """Yield (path tuple, data) pour chaque feuille (non-pakd)."""
        def walk(b, path):
            if is_pakd(b):
                ents, _, _ = parse_pakd(b)
                for i, (rid, d) in enumerate(ents):
                    yield from walk(d, path + (i,))
            else:
                yield path, b
        for did, fid, b in self.files():
            yield from walk(b, (did, fid))


def parse_emes(b):
    """Retourne (ids, slots, tail). slots: liste ordonnée par offset de dict(off, nid, text_end, gap)."""
    from codec import decode
    count = struct.unpack_from('<H', b, 4)[0]
    ids = struct.unpack_from('<%dH' % count, b, 8)
    o = (8 + 2 * count + 3) & ~3
    offs = struct.unpack_from('<%dI' % count, b, o)
    uniq = sorted(set(offs))
    slots = []
    for off in uniq:
        nid = struct.unpack_from('<H', b, off)[0]
        s, end = decode(b, off + 2)
        slots.append(dict(off=off, nid=nid, text=s, start=off + 2, end=end))
    for a, c in zip(slots, slots[1:]):
        a['gap'] = b[a['end']:c['off']]
    tail = b[slots[-1]['end']:] if slots else b''
    if slots:
        slots[-1]['gap'] = b''
    idx = {s['off']: i for i, s in enumerate(slots)}
    return [(ids[i], idx[offs[i]]) for i in range(count)], slots, tail, b[8 + 2 * count:o]


def build_emes(idmap, slots, tail, idpad, encoded):
    """encoded[i]: octets encodés du slot i (sans 0 final)."""
    count = len(idmap)
    h = bytearray(b'EMES' + struct.pack('<Hh', count, -1) + struct.pack('<%dH' % count, *[x[0] for x in idmap]))
    h += idpad
    dp = len(h) + 4 * count
    data = bytearray(); offs = []
    for s, enc in zip(slots, encoded):
        offs.append(dp + len(data))
        data += struct.pack('<H', s['nid']) + enc + b'\0' + s['gap']
    data += tail
    return bytes(h + struct.pack('<%dI' % count, *[offs[x[1]] for x in idmap]) + data)
