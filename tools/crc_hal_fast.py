# crc_hal_fast.py  (STM32 HAL_CRC-compatible, fast table version)

# Powershell #
# python crc_hal_fast.py FW.BIN

# If you want it to compute CRC over payload only (skipping your 0x200 header), run:
# python -c "import sys; import crc_hal_fast as c; d=open('FW.BIN','rb').read(); print(f'0x{c.crc_hal(d[0x200:]):08X}')"

import sys, struct

POLY = 0x04C11DB7

def make_table():
    t = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ POLY) & 0xFFFFFFFF if (c & 0x80000000) else (c << 1) & 0xFFFFFFFF
        t.append(c)
    return t

T = make_table()

def crc32_mpeg2_bytes(data: bytes) -> int:
    """CRC-32/MPEG-2 style (init=0xFFFFFFFF, xorout=0, no reflect), byte-wise update."""
    crc = 0xFFFFFFFF
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ T[((crc >> 24) ^ b) & 0xFF]
    return crc

def crc_hal(data: bytes) -> int:
    """
    Match STM32 HAL_CRC when feeding 32-bit words.
    We pack payload into little-endian words and update per byte in the same order those words represent in memory.
    Final partial word padded with 0xFF bytes.
    """
    pad = (-len(data)) & 3
    data += b'\xFF' * pad

    # Feed as little-endian 32-bit words, but CRC unit processes bits MSB-first;
    # The effective stream for our packing method is the bytes as stored in memory.
    return crc32_mpeg2_bytes(data)

if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    print(f"HAL CRC32 = 0x{crc_hal(data):08X}")