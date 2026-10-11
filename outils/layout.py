"""Simulation de mise en page des bulles de dialogue (police dialogue, retour auto)."""
import os, re
from font import Font
from codec import U2B, FALLBACK

_F = Font(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dialogue.font'), 'rb').read())
BOX_W = 337
HERO_W = 60   # largeur supposée de {hero} (Denam ≈ 50)


def _codes(s):
    out = []
    for c in s:
        if c in U2B:
            out.append(U2B[c])
        elif c in FALLBACK:
            out.append(U2B[FALLBACK[c]])
    return out


def width(s):
    s2 = s.replace('{hero}', '\x01').replace('{order}', '\x02')
    s2 = re.sub(r'\{[^}]*\}', '', s2)
    extra = s2.count('\x01') * HERO_W + s2.count('\x02') * 100 + len(re.findall(r'\{FF 83', s)) * 80 + len(re.findall(r'\{FF 84', s)) * 20
    return _F.width_bytes(_codes(s2.replace('\x01', '').replace('\x02', ''))) + extra


def pages(text):
    """Découpe en pages ({np}/{pp}) puis lignes (\\n + retour auto). Retourne liste de listes de lignes."""
    res = []
    for page in re.split(r'\{pp\}\n?|\{np\}', text):
        if page == '' and not res:
            continue
        lines = []
        for para in page.split('\n'):
            words = para.split(' ')
            cur = ''
            for wd in words:
                cand = (cur + ' ' + wd) if cur else wd
                if cur and width(cand) > BOX_W:
                    lines.append(cur); cur = wd
                else:
                    cur = cand
            lines.append(cur)
        res.append(lines)
    return res


def max_lines(text):
    p = pages(text)
    return max((len(x) for x in p), default=0)
