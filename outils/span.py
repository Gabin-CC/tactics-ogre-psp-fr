"""Recalcul de l'en-tête FC (span) : FC fl w1 w2 cc uu [vars].
largeur = 20 + 2 * max(largeur_ligne_px)  -> fl = 2*(1 + largeur//256) | var, w1 = largeur % 256
compte  = nb glyphes visibles (hors \\n) + 1 -> w2 = 1 + (compte-1)//63 (+0x40 si \\n ou macro), cc = (compte-1)%63 + 1
uu      = 8 * nb lignes
"""
import os, re
from codec import U2B, TAG
from font import Font

_F = None


def font():
    global _F
    if _F is None:
        _F = Font(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'normal.font'), 'rb').read())
    return _F


def measure(body):
    """Retourne (lignes, glyphes, a_macro, largeur_px_max)."""
    lines = [[]]
    glyphs = 0
    macro = False
    wide = False
    extra = [0]
    for m in TAG.finditer(body):
        t = m.group(0)
        if t == '\n':
            lines.append([]); extra.append(0); continue
        if t in ('{{', '}}'):
            lines[-1].append(U2B[t[0]]); glyphs += 1; continue
        if m.group(1) is not None:
            k = m.group(1).split(' ')[0]
            if re.fullmatch(r'c[0-9A-F]{4}', k):
                glyphs += 1; extra[-1] += 13; wide = wide or int(k[3:5], 16) >= 0x20
            elif re.fullmatch(r'b[0-9A-F]{2}', k):
                lines[-1].append(int(k[1:], 16)); glyphs += 1
            elif k == 'w':
                pass
            else:
                macro = True
                if k == 'icon':
                    extra[-1] += 12
            continue
        c = U2B.get(t)
        if c is None:
            from codec import FALLBACK
            c = U2B[FALLBACK[t]]
        lines[-1].append(c); glyphs += 1
    F = font()
    wmax = max(F.width_bytes(l) + e for l, e in zip(lines, extra))
    return len(lines), glyphs, macro, wmax, wide


def make_header(hdr, body, mode='recompute'):
    p = hdr[1:-1].split(' ')
    fl, w, cc, uu = int(p[1], 16), bytes.fromhex(p[2]), int(p[3], 16), int(p[4], 16)
    vars_ = b''.join(bytes.fromhex(v) for v in p[5:])
    if mode == 'keep':
        return bytes([0xFC, fl]) + w + bytes([cc, uu]) + vars_
    nlines, glyphs, macro, wpx, wide = measure(body)
    width = 20 + 2 * wpx
    nfl = 2 * (1 + width // 256) | (fl & 1)
    w1 = width % 256
    count = glyphs + 1
    w2 = 1 + (count - 1) // 63
    if nlines > 1 or macro or (fl & 1):
        w2 |= 0x40
    ncc = (count - 1) % 63 + 1
    if wide or (cc & 0x80):
        ncc |= cc & 0x80
    nuu = (8 * nlines) & 0xFF
    if fl & 1 and vars_:
        # variables : on garde la structure, on aligne le dernier marqueur sur la nouvelle largeur
        vb = bytearray(vars_)
        last = len(vb) - 6
        vb[last] = (vb[last] & 1) | (nfl & ~1)
        vb[last + 1] = (w1 + 1) & 0xFF
        vars_ = bytes(vb)
    return bytes([0xFC, nfl, w1, w2, ncc, nuu]) + vars_
