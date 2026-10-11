"""Codec texte Tactics Ogre PSP (police EN) <-> chaîne lisible avec balises {..}."""
import json, os, re

_m = json.load(open(os.path.join(os.path.dirname(__file__), 'charmap_en.json')))
B2U = {}
for k, v in _m.items():
    b = bytes.fromhex(k)
    if len(b) == 1 and b[0] < 0xEF:
        B2U[b[0]] = chr(v)
for c in range(0x20, 0x7F):
    B2U[c] = chr(c)
U2B = {v: k for k, v in B2U.items()}

# nombre d'octets d'arguments par macro FF xx
FF_ARGS = {0x80: 0, 0x81: 2, 0x82: 4, 0x83: 5, 0x84: 3, 0x85: 2, 0x86: 0, 0x87: 1, 0x88: 1, 0x89: 1,
           0x8A: 1, 0x8B: 2, 0x8C: 1, 0x8D: 2, 0x8E: 2, 0x8F: 2, 0x90: 2, 0x91: 0, 0x92: 0, 0x93: 0,
           0x94: 0, 0x95: 3, 0x96: 0, 0x97: 0, 0x98: 2, 0x99: 2, 0x9A: 1, 0x9B: 0, 0x9C: 2, 0x9D: 1,
           0x9E: 0, 0x9F: 0}
for _i in range(0xA0, 0xAA):
    FF_ARGS[_i] = 0
NAMED = {0x93: 'hero', 0x94: 'order', 0x86: 'pp', 0xA9: 'np', 0x9F: 'uc', 0x9B: 'colreset',
         0x9E: 'palreset', 0x96: '/if'}
NAMED_R = {v: k for k, v in NAMED.items()}


class DecodeError(Exception):
    pass


def decode(b, pos=0):
    """Décode depuis pos jusqu'au 0 final. Retourne (texte, pos après le 0)."""
    out = []
    n = len(b)
    while True:
        if pos >= n:
            raise DecodeError('eof')
        c = b[pos]
        if c == 0:
            return ''.join(out), pos + 1
        if c < 0x20:
            out.append('{c%02X%02X}' % (c, b[pos + 1])); pos += 2
        elif c < 0xFC:
            ch = B2U.get(c)
            if ch is None:
                out.append('{b%02X}' % c)
            elif ch == '{':
                out.append('{{')
            elif ch == '}':
                out.append('}}')
            else:
                out.append(ch)
            pos += 1
        elif c == 0xFC:
            fl, w1, w2, cc, uu = b[pos + 1:pos + 6]
            pos += 6
            vars_ = []
            if fl & 1:
                while True:
                    v = b[pos:pos + 6]; vars_.append(v.hex()); pos += 6
                    if not (v[0] & 1):
                        break
            out.append('{span %02x %02x%02x %02x %02x%s}' % (fl, w1, w2, cc, uu, ''.join(' ' + v for v in vars_)))
        elif c == 0xFD:
            out.append('{FD %02X}' % b[pos + 1]); pos += 2
        elif c == 0xFF:
            op = b[pos + 1]
            if op not in FF_ARGS:
                raise DecodeError('op %02X @%d' % (op, pos))
            na = FF_ARGS[op]
            args = b[pos + 2:pos + 2 + na]
            pos += 2 + na
            if op == 0x80:
                out.append('\n')
            elif op == 0x81:
                out.append('{w}' if args == b'\x01\x01' else '{w %s}' % args.hex())
            elif op in NAMED:
                out.append('{%s}' % NAMED[op])
            elif op == 0x95:
                out.append('{if %02X}' % args[0])
            elif op == 0x8A:
                out.append('{icon %d}' % args[0])
            elif op == 0x8C:
                out.append('{select %d}' % args[0])
            elif op == 0x9D:
                out.append('{pal %d}' % args[0])
            elif op == 0x82:
                out.append('{color %s}' % args.hex())
            else:
                out.append('{FF %02X%s}' % (op, (' ' + args.hex()) if na else ''))
        else:
            raise DecodeError('byte %02X @%d' % (c, pos))


TAG = re.compile(r'\{\{|\}\}|\{([^{}]*)\}|\n|.', re.S)


def encode(s, autowrap=False):
    """Encode une chaîne balisée (sans le 0 final). autowrap: insère {w} après chaque espace."""
    out = bytearray()
    stack = []  # positions des {if}
    for m in TAG.finditer(s):
        t = m.group(0)
        if t == '{{':
            out.append(U2B['{'])
        elif t == '}}':
            out.append(U2B['}'])
        elif t == '\n':
            out += b'\xff\x80'
        elif m.group(1) is not None:
            p = m.group(1).split(' ')
            k = p[0]
            if k == 'w':
                out += b'\xff\x81' + (bytes.fromhex(p[1]) if len(p) > 1 else b'\x01\x01')
            elif k in NAMED_R:
                out += bytes([0xFF, NAMED_R[k]])
                if k == '/if':
                    st = stack.pop()
                    ln = len(out) - st
                    for l1 in range(1, 256):
                        l2 = ln + 256 - 255 * l1
                        if 1 <= l2 <= 255:
                            break
                    else:
                        raise ValueError('if too long')
                    out[st - 2] = l1; out[st - 1] = l2
            elif k == 'if':
                out += bytes([0xFF, 0x95, int(p[1], 16), 0, 0]); stack.append(len(out))
            elif k == 'icon':
                out += bytes([0xFF, 0x8A, int(p[1])])
            elif k == 'select':
                out += bytes([0xFF, 0x8C, int(p[1])])
            elif k == 'pal':
                out += bytes([0xFF, 0x9D, int(p[1])])
            elif k == 'color':
                out += b'\xff\x82' + bytes.fromhex(p[1])
            elif k == 'FF':
                out += bytes([0xFF, int(p[1], 16)]) + (bytes.fromhex(p[2]) if len(p) > 2 else b'')
            elif k == 'FD':
                out += bytes([0xFD, int(p[1], 16)])
            elif k == 'span':
                out += bytes([0xFC, int(p[1], 16)]) + bytes.fromhex(p[2]) + bytes([int(p[3], 16), int(p[4], 16)])
                out += b''.join(bytes.fromhex(v) for v in p[5:] if v)
            elif re.fullmatch(r'c[0-9A-F]{4}', k):
                out += bytes.fromhex(k[1:])
            elif re.fullmatch(r'b[0-9A-F]{2}', k):
                out += bytes.fromhex(k[1:])
            else:
                raise ValueError('balise inconnue: {%s}' % m.group(1))
        else:
            ch = t
            if ch not in U2B:
                ch = FALLBACK.get(ch)
                if ch is None:
                    raise ValueError('caractère non supporté: %r' % t)
            out.append(U2B[ch] if len(ch) == 1 else 0)
            if autowrap and t == ' ':
                nxt = s[m.end():m.end() + 1]
                prv = s[m.start() - 1:m.start()]
                if nxt not in ('?', '!', ':', ';', '»') and prv != '«':
                    out += b'\xff\x81\x01\x01'
    return bytes(out), None


FALLBACK = {'’': "'", '‘': "'", ' ': ' ', ' ': ' ', ' ': ' ', 'Œ': 'Œ'}
