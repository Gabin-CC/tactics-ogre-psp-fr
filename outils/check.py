"""Vérifie une traduction : python3 check.py batch.json sortie1.json [sortie2.json ...]
Affiche les problèmes (balises, caractères, longueur, débordement de bulle)."""
import sys, os, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec import encode
from layout import max_lines
from font import Font

_NF = Font(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'normal.font'), 'rb').read())
from codec import U2B, FALLBACK


def nwidth(s):
    s = re.sub(r'\{[^}]*\}', '', s)
    return _NF.width_bytes([U2B.get(c, U2B.get(FALLBACK.get(c, ' '), 0x20)) for c in s])


def SPECIAL(s):
    return any(t in s for t in ('{FF 8D', '{FF 9A', '{FF 9C'))


def tags(s):
    return collections.Counter(t for t in re.findall(r'\{[^{}]*\}', s.replace('{{', '').replace('}}', '')))


def problems(src, fr, kind):
    p = []
    ts, tf = tags(src), tags(fr)
    if kind == 'emes' and not SPECIAL(src):
        ts.pop('{pp}', None); tf.pop('{pp}', None)
    if ts != tf:
        p.append('balises différentes: src=%s fr=%s' % (dict(tags(src)), dict(tags(fr))))
    if src.startswith('{np}') and not fr.startswith('{np}'):
        p.append('doit commencer par {np}')
    try:
        encode(fr, autowrap=True)
    except Exception as e:
        p.append('encodage: %s' % e)
    vis = re.sub(r'\{[^}]*\}', '', fr)
    if vis.isupper() is False and re.sub(r'[^A-Za-zÀ-ÿ]', '', re.sub(r'\{[^}]*\}', '', src)).isupper() and len(re.sub(r'[^A-Za-z]', '', src)) > 1:
        pass
    letters = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿŒœ]', '', vis)
    if letters and letters.upper() == letters and re.search(r'[ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŒ]', vis) and len(letters) > 1:
        p.append('libellé en MAJUSCULES : retirer les accents')
    if kind == 'emes':
        special = SPECIAL(src)
        ml_src, ml_fr = max_lines(src), max_lines(fr)
        lim = max(3, ml_src) if not special else ml_src + (1 if '{FF 9A' in src else 0)
        if ml_fr > lim:
            p.append('bulle trop longue : %d lignes (max %d) — raccourcir ou couper avec {pp}' % (ml_fr, lim))
    else:
        sl, fl = src.split('\n'), fr.split('\n')
        if len(sl) > 1 or len(fl) > 1:
            wmax = max(nwidth(l) for l in sl)
            over = [l for l in fl if nwidth(l) > wmax * 1.04 + 6]
            if over:
                p.append('ligne(s) trop large(s) (max ≈ %d car.) : %s' % (max(len(re.sub(r'\{[^}]*\}', '', l)) for l in sl), over[:2]))
            if len(fl) > len(sl) + 1:
                p.append('trop de lignes (%d, anglais %d)' % (len(fl), len(sl)))
        else:
            ws, wf = nwidth(src), nwidth(fr)
            words = len(re.sub(r'\{[^}]*\}', ' ', src).split())
            if words <= 6 and wf > ws * 1.35 + 12:
                p.append('libellé trop long (%.0f%% de l\'anglais)' % (100 * wf / max(ws, 1)))
            elif words > 6 and wf > ws * 1.25:
                p.append('texte trop long (%.0f%% de l\'anglais) — vise ≤ 120%%' % (100 * wf / max(ws, 1)))
    return p


def main():
    batch = json.load(open(sys.argv[1]))
    out = {}
    for f in sys.argv[2:]:
        if os.path.exists(f):
            out.update(json.load(open(f)))
    miss = 0; nprob = 0
    for x in batch:
        if x['k'] not in out:
            miss += 1
            continue
        pr = problems(x['src'], out[x['k']], x['kind'])
        if pr:
            nprob += 1
            print('[%s] %s\n   EN: %r\n   FR: %r' % (x['k'], ' | '.join(pr), x['src'][:300], out[x['k']][:300]))
    print('--- %d entrées, %d traduites, %d manquantes, %d avec problèmes' % (len(batch), len(batch) - miss, miss, nprob))


if __name__ == '__main__':
    main()
