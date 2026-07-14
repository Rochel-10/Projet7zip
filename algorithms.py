"""
algorithms.py — Moteur de compression du Projet7Zip
Méthodes : RLE, LZ77, LZW, Arithmétique (codage entier précis)
"""

import os
import struct
import time

import zipfile
import tempfile


# ══════════════════════════════════════════════════════════════
#  1. RLE — Run Length Encoding
# ══════════════════════════════════════════════════════════════

def rle_compress(data: bytes) -> bytes:

    if not data:
        return b""

    result = bytearray()

    i = 0
    n = len(data)

    while i < n:

        # longueur de répétition
        run = 1

        while (
            i + run < n
            and data[i + run] == data[i]
            and run < 255
        ):
            run += 1

        # On compresse uniquement à partir de 3 répétitions
        if run >= 3:

            result.append(1)      # bloc compressé
            result.append(run)
            result.append(data[i])

            i += run

        else:

            start = i

            while i < n:

                run = 1

                while (
                    i + run < n
                    and data[i + run] == data[i]
                    and run < 255
                ):
                    run += 1

                if run >= 3:
                    break

                i += 1

                if i - start == 255:
                    break

            length = i - start

            result.append(0)      # bloc brut
            result.append(length)
            result.extend(data[start:i])

    return bytes(result)


def rle_decompress(data: bytes) -> bytes:

    if not data:
        return b""

    result = bytearray()

    i = 0

    while i < len(data):

        block_type = data[i]
        i += 1

        length = data[i]
        i += 1

        if block_type == 1:

            value = data[i]
            i += 1

            result.extend([value] * length)

        else:

            result.extend(data[i:i + length])

            i += length

    return bytes(result)


# ══════════════════════════════════════════════════════════════
#  2. LZ77 — Lempel-Ziv 1977
# ══════════════════════════════════════════════════════════════

def lz77_compress(data: bytes, window=255, lookahead=15) -> bytes:
    if not data:
        return b""
    result = []
    pos = 0
    n = len(data)
    while pos < n:
        search_start = max(0, pos - window)
        search_buf = data[search_start:pos]
        best_dist = 0
        best_len  = 0
        max_match = min(lookahead, n - pos - 1)
        for length in range(max_match, 0, -1):
            target = data[pos:pos+length]
            for idx in range(len(search_buf)-1, -1, -1):
                dist = len(search_buf) - idx
                match = True
                for k in range(length):
                    sb_idx = idx + (k % dist)
                    if sb_idx >= len(search_buf) or search_buf[sb_idx] != data[pos+k]:
                        match = False; break
                if match:
                    best_dist = dist
                    best_len  = length
                    break
            if best_len > 0:
                break
        next_pos = pos + best_len
        char = data[next_pos] if next_pos < n else 0
        result.extend([best_dist, best_len, char])
        pos += best_len + (1 if next_pos < n else 0)
        if best_len == 0 and next_pos >= n:
            break
    return bytes(result)


def lz77_decompress(data: bytes) -> bytes:
    if not data:
        return b""
    result = bytearray()
    i = 0
    while i + 2 < len(data):
        dist   = data[i]
        length = data[i+1]
        char   = data[i+2]
        i += 3
        if length > 0 and dist > 0:
            start = len(result) - dist
            for k in range(length):
                result.append(result[start + (k % dist)])
        result.append(char)
    return bytes(result)


# ══════════════════════════════════════════════════════════════
#  3. LZW — Lempel-Ziv-Welch
# ══════════════════════════════════════════════════════════════

def lzw_compress(data: bytes) -> bytes:
    if not data:
        return b""
    dict_size = 256
    dictionary = {bytes([i]): i for i in range(dict_size)}
    result = []
    w = bytes([data[0]])
    for byte in data[1:]:
        c = bytes([byte])
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            if dict_size < 65536:
                dictionary[wc] = dict_size
                dict_size += 1
            w = c
    result.append(dictionary[w])
    return struct.pack(f"<{len(result)}H", *result)


def lzw_decompress(data: bytes) -> bytes:
    if not data:
        return b""
    n_codes = len(data) // 2
    codes = list(struct.unpack(f"<{n_codes}H", data[:n_codes*2]))
    dict_size = 256
    dictionary = {i: bytes([i]) for i in range(dict_size)}
    result = bytearray()
    w = dictionary[codes[0]]
    result.extend(w)
    for code in codes[1:]:
        if code in dictionary:
            entry = dictionary[code]
        elif code == dict_size:
            entry = w + bytes([w[0]])
        else:
            raise ValueError(f"Code LZW invalide : {code}")
        result.extend(entry)
        if dict_size < 65536:
            dictionary[dict_size] = w + bytes([entry[0]])
            dict_size += 1
        w = entry
    return bytes(result)


# ══════════════════════════════════════════════════════════════
#  4. Codage Arithmétique — précision entière (32 bits)
# ══════════════════════════════════════════════════════════════

def arithmetic_compress(data: bytes) -> bytes:
    if not data:
        return b""
    n = len(data)
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    symbols = sorted(freq.keys())
    total = n
    cumul = {}
    cum = 0
    for s in symbols:
        cumul[s] = (cum, cum + freq[s])
        cum += freq[s]

    PREC = 1 << 32
    low = 0; high = PREC
    result_bits = []
    pending = 0

    def emit(bit):
        nonlocal pending
        result_bits.append(bit)
        for _ in range(pending):
            result_bits.append(1 - bit)
        pending = 0

    for byte in data:
        lo_s, hi_s = cumul[byte]
        rng = high - low
        high = low + rng * hi_s // total
        low  = low + rng * lo_s // total
        while True:
            if high <= PREC // 2:
                emit(0); low *= 2; high *= 2
            elif low >= PREC // 2:
                emit(1); low = (low-PREC//2)*2; high = (high-PREC//2)*2
            elif low >= PREC//4 and high <= 3*PREC//4:
                pending += 1; low = (low-PREC//4)*2; high = (high-PREC//4)*2
            else:
                break

    pending += 1
    if low < PREC // 4:
        emit(0)
    else:
        emit(1)

    while len(result_bits) % 8 != 0:
        result_bits.append(0)

    comp_bytes = bytearray()
    for i in range(0, len(result_bits), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | result_bits[i+j]
        comp_bytes.append(byte_val)

    header = struct.pack("<I", len(symbols))
    for s in symbols:
        header += struct.pack("<BI", s, freq[s])
    header += struct.pack("<I", n)
    header += struct.pack("<I", len(result_bits))
    return header + bytes(comp_bytes)


def arithmetic_decompress(data: bytes) -> bytes:
    if not data:
        return b""
    offset = 0
    n_symbols = struct.unpack_from("<I", data, offset)[0]; offset += 4
    freq = {}
    for _ in range(n_symbols):
        sym, count = struct.unpack_from("<BI", data, offset)
        freq[sym] = count; offset += 5
    n       = struct.unpack_from("<I", data, offset)[0]; offset += 4
    nbits   = struct.unpack_from("<I", data, offset)[0]; offset += 4
    comp_bytes = data[offset:]

    bits = []
    for byte in comp_bytes:
        for j in range(7, -1, -1):
            bits.append((byte >> j) & 1)

    total = sum(freq.values())
    symbols = sorted(freq.keys())
    cumul = {}
    cum = 0
    for s in symbols:
        cumul[s] = (cum, cum + freq[s])
        cum += freq[s]

    PREC = 1 << 32
    low = 0; high = PREC
    val = 0
    bit_idx = 0
    for _ in range(32):
        bit = bits[bit_idx] if bit_idx < len(bits) else 0
        bit_idx += 1
        val = (val << 1) | bit

    result = bytearray()
    for _ in range(n):
        rng = high - low
        scaled = ((val - low + 1) * total - 1) // rng
        found = symbols[-1]
        for s in symbols:
            lo_s, hi_s = cumul[s]
            if lo_s <= scaled < hi_s:
                found = s; break
        result.append(found)
        lo_s, hi_s = cumul[found]
        high = low + rng * hi_s // total
        low  = low + rng * lo_s // total
        while True:
            if high <= PREC // 2:
                low *= 2; high *= 2
                val = val*2 | (bits[bit_idx] if bit_idx < len(bits) else 0); bit_idx += 1
            elif low >= PREC // 2:
                low=(low-PREC//2)*2; high=(high-PREC//2)*2
                val=(val-PREC//2)*2 | (bits[bit_idx] if bit_idx < len(bits) else 0); bit_idx += 1
            elif low >= PREC//4 and high <= 3*PREC//4:
                low=(low-PREC//4)*2; high=(high-PREC//4)*2
                val=(val-PREC//4)*2 | (bits[bit_idx] if bit_idx < len(bits) else 0); bit_idx += 1
            else:
                break
    return bytes(result)


# ══════════════════════════════════════════════════════════════
#  5. Dispatcher
# ══════════════════════════════════════════════════════════════

METHODS = {
    "RLE":          (rle_compress,          rle_decompress),
    "LZ77":         (lz77_compress,         lz77_decompress),
    "LZW":          (lzw_compress,          lzw_decompress),
    "Arithmétique": (arithmetic_compress,   arithmetic_decompress),
}

MAGIC      = b"P7Z\x01"
METHOD_IDS = {"RLE": 1, "LZ77": 2, "LZW": 3, "Arithmétique": 4}
ID_METHODS = {v: k for k, v in METHOD_IDS.items()}

def create_folder_archive(folder_path):
    """
    Transforme un dossier en fichier temporaire ZIP
    """

    temp = tempfile.NamedTemporaryFile(
        suffix=".zip",
        delete=False
    )

    temp.close()

    with zipfile.ZipFile(temp.name, "w",
                         zipfile.ZIP_DEFLATED) as archive:

        for root, dirs, files in os.walk(folder_path):

            for file in files:

                full_path = os.path.join(root, file)

                relative_path = os.path.relpath(
                    full_path,
                    folder_path
                )

                archive.write(
                    full_path,
                    relative_path
                )

    return temp.name


def compress_file(src_path: str, dst_path: str, method: str,
                  progress_cb=None) -> dict:
    t0 = time.time()
    #with open(src_path, "rb") as f:
        #data = f.read()
    # Nouveau : gestion dossier
    if os.path.isdir(src_path):

        original_name = os.path.basename(src_path)

        src_path = create_folder_archive(src_path)

        is_folder = True

    else:
        original_name = os.path.basename(src_path)
        is_folder = False

    with open(src_path, "rb") as f:
        data = f.read()

    orig_size = len(data)
    print("Taille originale :", orig_size)

    if progress_cb:
        progress_cb(20, f"Lecture de {os.path.basename(src_path)}…")
    compress_fn = METHODS[method][0]
    if progress_cb:
        progress_cb(40, "Compression en cours…")
    compressed = compress_fn(data)
    if progress_cb:
        progress_cb(85, "Écriture du fichier .p7z…")
    #name_bytes = os.path.basename(src_path).encode("utf-8")
    name_bytes = original_name.encode("utf-8")
    with open(dst_path, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<B", METHOD_IDS[method]))
        f.write(struct.pack("<I", orig_size))
        f.write(struct.pack("<I", len(name_bytes)))
        f.write(name_bytes)
        f.write(compressed)
        print("Taille compressée :", len(compressed))
        print("Taille fichier .p7z :", os.path.getsize(dst_path))
    comp_size = os.path.getsize(dst_path)
    elapsed   = time.time() - t0
    if progress_cb:
        progress_cb(100, "Terminé !")
    ratio = (1 - comp_size / orig_size) * 100 if orig_size > 0 else 0
    return {"orig_size": orig_size, "comp_size": comp_size,
            "ratio": ratio, "method": method,
            "elapsed": elapsed, "orig_name": os.path.basename(src_path)}

def decompress_file(src_path: str, dst_dir: str,
                    progress_cb=None) -> dict:
    t0 = time.time()
    with open(src_path, "rb") as f:
        raw = f.read()
    offset = 0
    magic = raw[offset:offset+4]; offset += 4
    if magic != MAGIC:
        raise ValueError("Fichier .p7z invalide ou corrompu.")
    method_id = struct.unpack_from("<B", raw, offset)[0]; offset += 1
    orig_size  = struct.unpack_from("<I", raw, offset)[0]; offset += 4
    name_len   = struct.unpack_from("<I", raw, offset)[0]; offset += 4
    orig_name  = raw[offset:offset+name_len].decode("utf-8"); offset += name_len
    compressed = raw[offset:]
    method     = ID_METHODS.get(method_id, "LZW")
    if progress_cb:
        progress_cb(30, f"Décompression ({method}) en cours…")
    decompress_fn = METHODS[method][1]
    restored = decompress_fn(compressed)
    if progress_cb:
        progress_cb(85, "Écriture du fichier restauré…")
    out_path = os.path.join(dst_dir, orig_name)
    with open(out_path, "wb") as f:
        f.write(restored)
    elapsed = time.time() - t0
    if progress_cb:
        progress_cb(100, "Terminé !")
    ratio = (1 - len(compressed) / len(restored)) * 100 if len(restored) > 0 else 0
    return {"orig_size": len(restored), "comp_size": len(compressed),
            "ratio": ratio, "method": method, "elapsed": elapsed,
            "out_path": out_path, "orig_name": orig_name}