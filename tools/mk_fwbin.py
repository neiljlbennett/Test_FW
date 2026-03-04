#!/usr/bin/env python3
import argparse
import struct
from pathlib import Path

IMG_MAGIC = 0x48474D49  # 'IMGH'
IMG_HDR_SIZE = 0x200

POLY = 0x04C11DB7

def crc32_mpeg2_words_le(data: bytes) -> int:
    """
    Compute CRC matching STM32F4 HAL_CRC when fed with 32-bit words via HAL_CRC_Accumulate.
    - init = 0xFFFFFFFF
    - poly = 0x04C11DB7
    - no reflect
    - no xorout
    - data is packed into little-endian 32-bit words
    - final partial word padded with 0xFF bytes
    """
    crc = 0xFFFFFFFF

    # pad to 4 bytes with 0xFF
    pad_len = (-len(data)) & 3
    data_padded = data + (b"\xFF" * pad_len)

    # process each 32-bit word (little-endian)
    for i in range(0, len(data_padded), 4):
        w = struct.unpack_from("<I", data_padded, i)[0]
        # hardware CRC effectively XORs top bits with input word then shifts MSB-first
        crc ^= w
        for _ in range(32):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ POLY) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF

    return crc & 0xFFFFFFFF

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("payload_bin", help="Input app payload .bin (vector table at start)")
    ap.add_argument("out_fwbin", help="Output FW.BIN (0x200 header + payload)")
    ap.add_argument("--exec-load", required=True, help="e.g. 0x0800C200")
    ap.add_argument("--fw-version", type=int, default=0)
    ap.add_argument("--hdr-version", type=int, default=1)
    args = ap.parse_args()

    payload = Path(args.payload_bin).read_bytes()
    img_size = len(payload)
    crc = crc32_mpeg2_words_le(payload)
    exec_load = int(args.exec_load, 16)

    header = bytearray(b"\xFF" * IMG_HDR_SIZE)
    struct.pack_into("<IIIIII", header, 0,
                     IMG_MAGIC,
                     args.hdr_version,
                     exec_load,
                     img_size,
                     crc,
                     args.fw_version)

    Path(args.out_fwbin).write_bytes(bytes(header) + payload)

    print(f"Created {args.out_fwbin}")
    print(f"  payload size : {img_size} bytes")
    print(f"  crc32        : 0x{crc:08X}")
    print(f"  exec_load    : 0x{exec_load:08X}")

if __name__ == "__main__":
    main()