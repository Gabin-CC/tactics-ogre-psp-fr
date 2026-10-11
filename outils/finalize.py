"""Fusionne les traductions, corrige automatiquement la mise en page, produit tr/final.json + rapport."""
import sys, os, json, re, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import pages, max_lines, width as dwidth, BOX_W
from check import problems, nwidth, tags

S = sys.argv[1]


def split_page(page_text):
    """Coupe une page trop longue en plusieurs pages (≤3 lignes) aux fins de phrase si possible."""
    out = []
    rest = page_text
    while True:
        lines = pages('{np}' + rest)[0] if rest else []
        if len(lines) <= 3:
            out.append(rest); break
        # chercher la dernière fin de phrase qui tient dans 3 lignes
        best = None
        for m in re.finditer(r'[.!?…](?:\.\.)?["»]?\s+(?=\S)', rest):
            head = rest[:m.end()].rstrip()
            if len(pages('{np}' + head)[0]) <= 3:
                best = m.end()
        if best is None:
            # couper au mot qui termine la 3e ligne
            l3 = pages('{np}' + rest)[0][:3]
            n = len(' '.join(l3)) if '\n' not in rest[:len(' '.join(l3)) + 1] else None
            if n is None:
                out.append(rest); break
            best = n + 1
        out.append(rest[:best].rstrip())
        rest = rest[best:].lstrip()
        if not rest:
            break
    return out


def fix_emes(src, fr):
    from check import SPECIAL
    if SPECIAL(src):
        return fr
    if max_lines(fr) <= 3:
        return fr
    m = re.match(r'^((?:\{np\})?(?:\{[^}]*\})*)', fr)
    # traiter page par page
    parts = re.split(r'(\{pp\}\n?)', fr[len('{np}'):] if fr.startswith('{np}') else fr)
    res = []
    for p in parts:
        if p.startswith('{pp}'):
            res.append(p); continue
        if p and len(pages('{np}' + p)[0]) > 3 and '\n' not in p.strip():
            res.append('{pp}'.join(split_page(p)))
        elif p and len(pages('{np}' + p)[0]) > 3:
            # avec \n : remplacer les \n par des espaces puis redécouper
            res.append('{pp}'.join(split_page(p.replace('\n', ' '))))
        else:
            res.append(p)
    return ('{np}' if fr.startswith('{np}') else '') + ''.join(res)


def rewrap_xlc(src, fr):
    sl, fl = src.split('\n'), fr.split('\n')
    if len(sl) <= 1 and len(fl) <= 1:
        return fr
    lim = max(nwidth(l) for l in sl) * 1.04 + 6
    if all(nwidth(l) <= lim for l in fl):
        return fr
    # paragraphes : séparés par lignes vides ou lignes commençant par un espace/puce/balise
    paras, cur = [], []
    for l in fl:
        if l.strip() == '' or re.match(r'^(\s|•|-|\{(?!w))', l):
            if cur: paras.append(' '.join(cur))
            cur = [l] if l.strip() else []
            if not l.strip(): paras.append('')
        else:
            cur.append(l)
    if cur: paras.append(' '.join(cur))
    out = []
    for p in paras:
        if not p:
            out.append(''); continue
        words = p.split(' ')
        line = ''
        for w in words:
            cand = (line + ' ' + w) if line else w
            if line and nwidth(cand) > lim:
                out.append(line); line = w
            else:
                line = cand
        out.append(line)
    return '\n'.join(out)


def main():
    units = {u['k']: u for u in json.load(open(os.path.join(S, 'tr', 'units.json')))}
    tr = {}
    for f in sorted(glob.glob(os.path.join(S, 'tr', 'out', '*.part*.json'))):
        tr.update(json.load(open(f)))
    final, report = {}, collections.Counter()
    bad = []
    for k, fr in tr.items():
        u = units.get(k)
        if not u:
            report['clé inconnue'] += 1; continue
        if fr == u['src']:
            report['inchangé'] += 1
            continue
        if u['kind'] == 'emes':
            fr2 = fix_emes(u['src'], fr)
        else:
            fr2 = rewrap_xlc(u['src'], fr)
        if fr2 != fr:
            report['corrigé auto'] += 1
        pr = problems(u['src'], fr2, u['kind'])
        hard = [p for p in pr if p.startswith(('balises', 'doit commencer', 'encodage'))]
        if hard:
            report['rejeté'] += 1; bad.append((k, hard, u['src'][:120], fr2[:120])); continue
        if pr:
            report['avertissement'] += 1
        final[k] = fr2
    json.dump(final, open(os.path.join(S, 'tr', 'final.json'), 'w'), ensure_ascii=False)
    print(dict(report), 'final:', len(final), '/ unités:', len(units))
    for b in bad[:30]:
        print('REJET', b)


if __name__ == '__main__':
    main()
