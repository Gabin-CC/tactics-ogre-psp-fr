"""Construit les fichiers modifiés (BIN + FILETABLE) à partir de feuilles modifiées."""
import struct
from pakd import is_pakd, parse_pakd, build_pakd

UNIT = 0x800


class Builder:
    def __init__(self, game):
        self.g = game
        self.leaf_mods = {}  # (did, fid) -> {subpath tuple: bytes}

    def set_leaf(self, path, data):
        self.leaf_mods.setdefault(path[:2], {})[path[2:]] = data

    def _rebuild(self, b, sub, mods):
        if sub in mods:
            return mods[sub]
        if not any(k[:len(sub)] == sub for k in mods):
            return b
        assert is_pakd(b)
        ents, _, _ = parse_pakd(b)
        new = [(rid, self._rebuild(d, sub + (i,), mods)) for i, (rid, d) in enumerate(ents)]
        return build_pakd(new)

    def file_bytes(self, did, fid):
        """Contenu reconstruit d'un fichier de premier niveau (avant toute relocalisation)."""
        ft = self.g.ft
        d = ft.dir(did)
        f = next(x for x in d['files'] if x['id'] == fid)
        o = ft.offset(d, f)
        raw = self.g.bin(did)[o:o + f['size']]
        mods = self.leaf_mods.get((did, fid))
        return self._rebuild(raw, (), mods) if mods else raw

    def build(self):
        """Retourne {nom_fichier_USRDIR: bytes}. Les BIN modifiés sont reconstruits de façon compacte."""
        ft = self.g.ft
        out = {}
        dirs = sorted(set(did for did, _ in self.leaf_mods))
        for did in dirs:
            d = ft.dir(did)
            raw = self.g.bin(did)
            unit = UNIT << d['bs']
            # contenu de chaque fichier (nouveau ou original), regroupé par offset d'origine
            order = sorted(d['files'], key=lambda f: (ft.offset(d, f), f['id']))
            placed = {}
            bb = bytearray()
            for f in order:
                o = ft.offset(d, f)
                data = self.file_bytes(did, f['id']) if (did, f['id']) in self.leaf_mods else raw[o:o + f['size']]
                key = (o, f['size'], (did, f['id']) in self.leaf_mods and f['id'])
                if f['size'] == 0 and (did, f['id']) not in self.leaf_mods:
                    newpos = o if o <= len(bb) else len(bb)
                elif key in placed:
                    newpos = placed[key]
                else:
                    newpos = (len(bb) + unit - 1) // unit * unit
                    bb += b'\0' * (newpos - len(bb))
                    bb += data
                    placed[key] = newpos
                f['bo'] = (newpos - d['base']) // unit
                f['size'] = len(data)
            bb += b'\0' * ((-len(bb)) % UNIT)
            d['inst'] = 0
            out['%04X.BIN' % did] = bytes(bb)
        out['FILETABLE.BIN'] = ft.serialize(self.g._orig_ft)
        return out
