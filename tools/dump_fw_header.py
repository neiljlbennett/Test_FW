#!/usr/bin/env python3

# e.g. usage at cmd line
# python dump_fw_header.py FW.BIN


import sys
import struct

IMG_HDR_SIZE = 0x200
IMG_MAGIC = 0x48474D49  # 'IMGH'
POLY = 0x04C11DB7

def crc_hal(data: bytes) -> int:
    """CRC compatible with STM32F4 HAL_CRC when feeding 32-bit words; pad final word with 0xFF."""
    crc = 0xFFFFFFFF
    pad = (-len(data)) & 3
    data += b"\xFF" * pad

    for i in range(0, len(data), 4):
        w = struct.unpack_from("<I", data, i)[0]
        crc ^= w
        for _ in range(32):
            crc = ((crc << 1) ^ POLY) & 0xFFFFFFFF if (crc & 0x80000000) else (crc << 1) & 0xFFFFFFFF
    return crc & 0xFFFFFFFF

def as_ascii_magic(x: int) -> str:
    b = struct.pack("<I", x)
    return "".join(chr(c) if 32 <= c <= 126 else "." for c in b)

def main():
    if len(sys.argv) < 2:
        print("Usage: python dump_fw_header.py FW.BIN [--check-crc]")
        sys.exit(1)

    filename = sys.argv[1]
    check_crc = ("--check-crc" in sys.argv[2:])

    with open(filename, "rb") as f:
        hdr = f.read(IMG_HDR_SIZE)
        if len(hdr) < IMG_HDR_SIZE:
            raise SystemExit("File too small to contain header (need at least 0x200 bytes).")
        payload = f.read()  # rest of file

    # Header layout: <IIIIII> then reserved/padding
    magic, hdr_ver, exec_load, img_size, img_crc, fw_ver = struct.unpack_from("<IIIIII", hdr, 0)

    print(f"File              : {filename}")
    print(f"Header size       : 0x{IMG_HDR_SIZE:X} ({IMG_HDR_SIZE} bytes)")
    print(f"Magic             : 0x{magic:08X} ('{as_ascii_magic(magic)}')")
    print(f"Header version    : {hdr_ver}")
    print(f"Exec load addr    : 0x{exec_load:08X}")
    print(f"Image size        : {img_size} bytes")
    print(f"Image CRC32 (HAL) : 0x{img_crc:08X}")
    print(f"FW version        : {fw_ver}")

    # Quick sanity checks
    if magic != IMG_MAGIC:
        print("WARNING: Magic does not match expected 'IMGH' (0x48474D49).")

    if img_size > len(payload):
        print(f"WARNING: img_size ({img_size}) > payload bytes in file ({len(payload)}).")

    if check_crc:
        data = payload[:img_size]
        calc = crc_hal(data)
        print(f"Calculated CRC32  : 0x{calc:08X}")
        print("CRC match         : " + ("YES" if calc == img_crc else "NO"))

if __name__ == "__main__":
    main()