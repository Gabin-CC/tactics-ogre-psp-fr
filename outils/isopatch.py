"""Patch d'une image ISO9660 : remplace des fichiers (en place si la taille le permet, sinon ajout en fin)."""
import os, shutil, struct

SECTOR = 2048


def walk_iso(f):
    """Retourne {chemin: (pos_record, extent, size)} pour tous les fichiers."""
    f.seek(16 * SECTOR); pvd = f.read(SECTOR)
    root = pvd[156:156 + 34]
    res = {}

    def walk_dir(extent, size, prefix):
        f.seek(extent * SECTOR); data = f.read(size)
        o = 0
        while o < size:
            ln = data[o]
            if ln == 0:
                o = (o // SECTOR + 1) * SECTOR; continue
            ext, sz = struct.unpack_from('<I', data, o + 2)[0], struct.unpack_from('<I', data, o + 10)[0]
            flags = data[o + 25]; nl = data[o + 32]; name = data[o + 33:o + 33 + nl]
            if name not in (b'\0', b'\1'):
                nm = name.decode().split(';')[0]
                p = prefix + '/' + nm
                if flags & 2:
                    walk_dir(ext, sz, p)
                else:
                    res[p] = (extent * SECTOR + o, ext, sz)
            o += ln
    walk_dir(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '')
    return res


def patch_iso(src, dst, replacements):
    """replacements: {'/PSP_GAME/USRDIR/0385.BIN': bytes}"""
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
        shutil.copyfile(src, dst)
    else:
        shutil.copyfile(src, dst)
    with open(dst, 'r+b') as f:
        files = walk_iso(f)
        f.seek(0, 2); end = f.tell()
        assert end % SECTOR == 0
        for path, data in replacements.items():
            rec, ext, sz = files[path]
            alloc = (sz + SECTOR - 1) // SECTOR * SECTOR
            if len(data) <= alloc:
                pos = ext * SECTOR
            else:
                pos = end
                end += (len(data) + SECTOR - 1) // SECTOR * SECTOR
            f.seek(pos); f.write(data)
            pad = (-len(data)) % SECTOR
            if pad:
                f.write(b'\0' * pad)
            nsec = pos // SECTOR
            f.seek(rec + 2); f.write(struct.pack('<I', nsec) + struct.pack('>I', nsec) + struct.pack('<I', len(data)) + struct.pack('>I', len(data)))
        f.seek(0, 2); total = f.tell() // SECTOR
        f.seek(16 * SECTOR + 80); f.write(struct.pack('<I', total) + struct.pack('>I', total))


def walk_dirs(f):
    """Extents des répertoires."""
    f.seek(16 * SECTOR); pvd = f.read(SECTOR)
    root = pvd[156:156 + 34]
    res = []
    def walk_dir(extent, size):
        res.append((extent, size))
        f.seek(extent * SECTOR); data = f.read(size)
        o = 0
        while o < size:
            ln = data[o]
            if ln == 0:
                o = (o // SECTOR + 1) * SECTOR; continue
            ext, sz = struct.unpack_from('<I', data, o + 2)[0], struct.unpack_from('<I', data, o + 10)[0]
            if data[o + 25] & 2 and data[o + 33:o + 33 + data[o + 32]] not in (b'\0', b'\1'):
                walk_dir(ext, sz)
            o += ln
    walk_dir(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0])
    return res


def rebuild_iso(src, dst, replacements):
    """Réécrit l'ISO de façon compacte : fichiers dans l'ordre d'origine, remplacés si besoin."""
    with open(src, 'rb') as f:
        files = walk_iso(f)
        dirs = walk_dirs(f)
        order = sorted(files.items(), key=lambda kv: kv[1][1])
        first_moved = min(ext for p, (rec, ext, sz) in files.items() if p in replacements)
        maxdir = max(e + (s + SECTOR - 1) // SECTOR for e, s in dirs)
        assert maxdir <= first_moved, 'répertoires après les fichiers modifiés'
        with open(dst, 'wb') as o:
            # en-tête inchangé jusqu'au premier fichier modifié
            f.seek(0)
            remaining = first_moved * SECTOR
            while remaining:
                chunk = f.read(min(remaining, 64 << 20)); o.write(chunk); remaining -= len(chunk)
            pos = first_moved
            patches = []
            for p, (rec, ext, sz) in order:
                if ext < first_moved:
                    continue
                if p in replacements:
                    data = replacements[p]
                else:
                    f.seek(ext * SECTOR); data = None
                n = len(data) if data is not None else sz
                o.seek(pos * SECTOR)
                if data is not None:
                    o.write(data)
                else:
                    left = sz
                    while left:
                        chunk = f.read(min(left, 64 << 20)); o.write(chunk); left -= len(chunk)
                pad = (-n) % SECTOR
                if pad:
                    o.write(b'\0' * pad)
                patches.append((rec, pos, n))
                pos += (n + SECTOR - 1) // SECTOR
            o.truncate(pos * SECTOR)
            for rec, nsec, n in patches:
                o.seek(rec + 2)
                o.write(struct.pack('<I', nsec) + struct.pack('>I', nsec) + struct.pack('<I', n) + struct.pack('>I', n))
            o.seek(16 * SECTOR + 80); o.write(struct.pack('<I', pos) + struct.pack('>I', pos))
