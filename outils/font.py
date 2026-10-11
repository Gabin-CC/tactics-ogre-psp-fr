"""Métriques de la police normal.font (avance + crénage) pour calculer la largeur des spans."""
import struct, os
from codec import U2B


class Font:
    def __init__(self, b):
        h = struct.unpack_from('<5I', b, 0)
        nL = h[4]
        left = [struct.unpack_from('>H', b, 0x14 + 2 * i)[0] for i in range(nL)]
        ro = 0x14 + 2 * nL
        ranges = [struct.unpack_from('<HH', b, ro + 4 * i) for i in range(nL)]
        co = ro + 4 * nL
        nR = struct.unpack_from('<I', b, co)[0]
        right = [struct.unpack_from('>H', b, co + 4 + 2 * i)[0] for i in range(nR)]
        vo = co + 4 + 2 * nR
        vals = struct.unpack_from('%db' % nR, b, vo)
        self.kern = {}
        for i, l in enumerate(left):
            s, e = ranges[i]
            for j in range(s, e + 1):
                self.kern[(l, right[j])] = vals[j]
        wo = h[1] + 20
        self.adv = b[wo:wo + h[2]]

    def width_bytes(self, codes):
        """codes: liste de codes octets (encodage jeu) d'une ligne."""
        w = 0
        for i, c in enumerate(codes):
            w += self.adv[c - 0x20] if 0 <= c - 0x20 < len(self.adv) else 8
            if i + 1 < len(codes):
                w += self.kern.get((c, codes[i + 1]), 0)
        return w
