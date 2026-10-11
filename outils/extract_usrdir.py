"""Extrait PSP_GAME/USRDIR d'une ISO : python3 extract_usrdir.py jeu.iso dossier_sortie"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isopatch import walk_iso, SECTOR
iso, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
with open(iso, 'rb') as f:
    for p, (rec, ext, sz) in walk_iso(f).items():
        if p.startswith('/PSP_GAME/USRDIR/'):
            f.seek(ext * SECTOR)
            open(os.path.join(out, os.path.basename(p)), 'wb').write(f.read(sz))
print('ok')

# Polices nécessaires au calcul des largeurs (non distribuées : extraites de l'ISO)
from tree import Game
g = Game(out)
here = os.path.dirname(os.path.abspath(__file__))
for did, fid, b in g.files():
    if did == 600 and fid in (8, 9):
        open(os.path.join(here, 'normal.font' if fid == 8 else 'dialogue.font'), 'wb').write(b)
print('polices extraites')
