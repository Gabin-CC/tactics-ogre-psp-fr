"""Exporte tous les textes traduisibles en JSON (dédupliqués)."""
import sys, json, re, hashlib, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import Game, parse_emes
from xlc import parse_xlc

SPAN = re.compile(r'^\{span ([0-9a-f]{2}) ([0-9a-f]{4}) ([0-9a-f]{2}) ([0-9a-f]{2})((?: [0-9a-f]{12})*)\}')


def split_span(t):
    m = SPAN.match(t)
    if not m:
        return None, t
    return m.group(0), t[m.end():]


def norm(t):
    """Texte présenté au traducteur : sans {w} si autowrap, sans en-tête span."""
    hdr, body = split_span(t)
    aw = '{w}' in body
    if aw:
        body = body.replace('{w}', '')
    return hdr, aw, body


def key(body):
    return hashlib.sha1(body.encode()).hexdigest()[:12]


def main(usrdir, outdir):
    g = Game(usrdir)
    units = collections.OrderedDict()
    def add(body, ctx, kind):
        if not re.search(r'[A-Za-z]', re.sub(r'\{[^}]*\}', '', body)):
            return
        k = key(body)
        u = units.get(k)
        if not u:
            u = units[k] = dict(k=k, src=body, kind=kind, ctx=[])
        if len(u['ctx']) < 3:
            u['ctx'].append(ctx)
        u['n'] = u.get('n', 0) + 1
    for path, b in g.leaves():
        if path[:2] == (0, 0):
            continue  # blob preload : copies d'autres fichiers
        if b[:4] == b'EMES':
            idmap, slots, tail, idpad = parse_emes(b)
            for s in slots:
                hdr, aw, body = norm(s['text'])
                add(body, '/'.join(map(str, path)) + ' nid=%d' % s['nid'], 'emes')
        elif b[:4] == b'xlce':
            info = parse_xlc(b)
            if not info:
                continue
            for s in info['slots']:
                hdr, aw, body = norm(s['text'])
                add(body, '/'.join(map(str, path)), 'xlc')
    json.dump(list(units.values()), open(os.path.join(outdir, 'units.json'), 'w'), ensure_ascii=False, indent=0)
    c = collections.Counter(u['kind'] for u in units.values())
    w = collections.Counter()
    for u in units.values():
        w[u['kind']] += len(re.sub(r'\{[^}]*\}', ' ', u['src']).split())
    print(len(units), c, w)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
