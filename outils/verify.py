"""Extrait USRDIR d'une ISO patchée et vérifie que tout se relit."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isopatch import walk_iso, SECTOR
from tree import Game, parse_emes
from xlc import parse_xlc

iso, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
with open(iso, 'rb') as f:
    files = walk_iso(f)
    for p, (rec, ext, sz) in files.items():
        if p.startswith('/PSP_GAME/USRDIR/'):
            f.seek(ext * SECTOR)
            open(os.path.join(outdir, os.path.basename(p)), 'wb').write(f.read(sz))
g = Game(outdir)
pat = sys.argv[3] if len(sys.argv) > 3 else None
n = 0
for path, b in g.leaves():
    if b[:4] == b'EMES':
        texts = [s['text'] for s in parse_emes(b)[1]]
    elif b[:4] == b'xlce':
        i = parse_xlc(b); texts = [s['text'] for s in i['slots']] if i else []
    else:
        continue
    n += len(texts)
    if pat:
        for t in texts:
            if re.search(pat, t): print(path, repr(t[:150]))
print('ok, chaînes lues:', n)
