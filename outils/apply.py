"""Applique les traductions (k -> texte FR) et produit l'ISO patchée."""
import sys, os, json, re, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import Game, parse_emes, build_emes
from xlc import parse_xlc, build_xlc
from codec import encode
from export import norm, key, SPAN
from build import Builder
import span as spanmod


def translate_text(orig, tr, mode):
    hdr, aw, body = norm(orig)
    k = key(body)
    if k not in tr:
        return None
    new = tr[k]
    enc_body, _ = encode(new, autowrap=aw)
    if hdr:
        return spanmod.make_header(hdr, new, mode) + enc_body
    return enc_body


def apply(usrdir, tr, mode='recompute', only=None):
    g = Game(usrdir)
    bl = Builder(g)
    blob_paths = set()
    nchg = 0
    for path, b in g.leaves():
        if path[:2] == (0, 0):
            continue
        if only and path[:2] not in only:
            continue
        if b[:4] == b'EMES':
            idmap, slots, tail, idpad = parse_emes(b)
            encs, chg = [], False
            for s in slots:
                e = translate_text(s['text'], tr, mode)
                if e is None:
                    e = encode(s['text'])[0]
                else:
                    chg = True; nchg += 1
                encs.append(e)
            if chg:
                bl.set_leaf(path, build_emes(idmap, slots, tail, idpad, encs))
        elif b[:4] == b'xlce':
            info = parse_xlc(b)
            if not info:
                continue
            encs, chg = [], False
            for s in info['slots']:
                e = translate_text(s['text'], tr, mode)
                if e is None:
                    e = encode(s['text'])[0]
                else:
                    chg = True; nchg += 1
                encs.append(e)
            if chg:
                bl.set_leaf(path, build_xlc(b, info, encs))
    # mettre à jour les copies dans le blob preload (0/0)
    blob = g.ft.dir(0)
    fb = blob['files'][0]
    raw0 = g.bin(0)[g.ft.offset(blob, fb):g.ft.offset(blob, fb) + fb['size']]
    n = struct.unpack_from('<I', raw0, 0)[0]
    ents = [list(struct.unpack_from('<II', raw0, 4 + 8 * i)) for i in range(n)]
    pos = 4 + 8 * n; datas = []
    for id_, sz in ents:
        datas.append(raw0[pos:pos + sz]); pos += sz
    changed = False
    for i, (id_, sz) in enumerate(ents):
        did, fid = id_ & 0xFFFF, id_ >> 16
        if (did, fid) in bl.leaf_mods:
            nb = bl.file_bytes(did, fid)
            datas[i] = nb; ents[i][1] = len(nb); changed = True
    if changed:
        nblob = struct.pack('<I', n) + b''.join(struct.pack('<II', *e) for e in ents) + b''.join(datas)
        bl.leaf_mods[(0, 0)] = {(): nblob}
    return bl.build(), nchg


if __name__ == '__main__':
    usrdir, trfile, iso_in, iso_out = sys.argv[1:5]
    mode = sys.argv[5] if len(sys.argv) > 5 else 'recompute'
    tr = json.load(open(trfile))
    out, nchg = apply(usrdir, tr, mode)
    from isopatch import rebuild_iso
    rebuild_iso(iso_in, iso_out, {'/PSP_GAME/USRDIR/' + k: v for k, v in out.items()})
    print('chaînes modifiées:', nchg, 'fichiers:', sorted(out))
