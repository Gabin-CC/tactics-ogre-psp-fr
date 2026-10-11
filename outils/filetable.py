"""FILETABLE.BIN parser/writer (Tactics Ogre PSP), d'après Gibbed.LetUsClingTogether."""
import struct
ENTRY_SIZES = {2: 4, 3: 6, 4: 6, 5: 8}
BLOCK = 0x800

class FileTable:
    def __init__(self, data):
        sig, ncount, dcount, u6, self.ft_off, self.total = struct.unpack_from('<HHHHII', data, 0)
        assert sig == 0x1EF1 and u6 == 4
        self.head = data[0x10:0x44]  # title ids, flags, crypto key
        o = 0x44
        self.names = [struct.unpack_from('<IHH', data, o + i * 8) for i in range(ncount)]
        o += ncount * 8
        self.dirs = []
        for i in range(dcount):
            did, enc, bs, base, u8, inst, bc, ntc, nti, bto, ibase = struct.unpack_from('<HBBIBBHHHII', data, o)
            o += 24
            self.dirs.append(dict(id=did, enc=enc, bs=bs, base=base, inst=inst, bc=bc, ntc=ntc, nti=nti, bto=bto, ibase=ibase, files=[]))
        nb = sum(d['bc'] for d in self.dirs)
        self.batches = []
        for i in range(nb):
            bid, cnt, raw = struct.unpack_from('<HHI', data, o); o += 8
            self.batches.append((bid, cnt, raw & 0x1FFFFFFF, raw >> 29))
        assert o == self.ft_off
        for d in self.dirs:
            for b in range(d['bc']):
                bid, cnt, fto, fl = self.batches[d['bto'] // 8 + b]
                p = self.ft_off + fto
                fmt = {2: '<HH', 3: '<HI', 4: '<IH', 5: '<II'}[fl]
                for j in range(cnt):
                    bo, sz = struct.unpack_from(fmt, data, p); p += ENTRY_SIZES[fl]
                    d['files'].append(dict(id=bid + j, bo=bo, size=sz, flags=fl, entry_pos=p - ENTRY_SIZES[fl]))

    def offset(self, d, f):
        return d['base'] + (f['bo'] << d['bs']) * BLOCK

    def dir(self, did):
        return next(d for d in self.dirs if d['id'] == did)

    def serialize(self, orig):
        """Re-sérialise en gardant les batches d'origine ; ajuste les flags si nécessaire."""
        out = bytearray(orig[:0x44])
        for nh in self.names:
            out += struct.pack('<IHH', *nh)
        ftab = bytearray(); batches = []
        for d in self.dirs:
            files = d['files']; k = 0
            for b in range(d['bc']):
                bid, cnt, _, fl = self.batches[d['bto'] // 8 + b]
                fs = files[k:k + cnt]; k += cnt
                big_off = any(f['bo'] > 0xFFFF for f in fs)
                big_sz = any(f['size'] > 0xFFFF for f in fs)
                if big_off and big_sz:
                    nfl = 5
                elif big_off:
                    nfl = max(fl, 4) if fl != 3 else 5
                elif big_sz:
                    nfl = 3 if fl == 2 else fl
                else:
                    nfl = fl
                batches.append((bid, cnt, len(ftab), nfl))
                fmt = {2: '<HH', 3: '<HI', 4: '<IH', 5: '<II'}[nfl]
                for f in fs:
                    ftab += struct.pack(fmt, f['bo'], f['size'])
        for d in self.dirs:
            out += struct.pack('<HBBIBBHHHII', d['id'], d['enc'], d['bs'], d['base'], 0, d['inst'], d['bc'],
                               d['ntc'], d['nti'], d['bto'], d['ibase'])
        for bid, cnt, off, fl in batches:
            out += struct.pack('<HHI', bid, cnt, off | (fl << 29))
        ft_off = len(out)
        out += ftab
        struct.pack_into('<II', out, 8, ft_off, len(out))
        return bytes(out)
