#!/usr/bin/env python3
"""
CMF BT protocol sniffer.

Usage:
  # On Android: enable "Bluetooth HCI snoop log" in Developer Options
  # Connect CMF buds to phone, use official app, then:
  adb pull /data/misc/bluetooth/logs/btsnoop_hci.log snoop.log

  # Then parse:
  python tools/sniff.py snoop.log [--filter-addr AA:BB:CC:DD:EE:FF]
"""
import sys
import struct
import argparse
from pathlib import Path

BTSNOOP_MAGIC = b"btsnoop\x00"
RFCOMM_PSM = 3  # Classic BT RFCOMM channel

def parse_btsnoop(path: Path, filter_addr: str | None):
    data = path.read_bytes()
    if not data.startswith(BTSNOOP_MAGIC):
        sys.exit(f"Not a btsnoop file: {path}")

    version, datalink = struct.unpack_from(">II", data, 8)
    print(f"btsnoop version={version} datalink={datalink}")

    offset = 16
    pkt_num = 0
    while offset < len(data):
        if offset + 24 > len(data):
            break
        orig_len, incl_len, flags, drops, ts_usec = struct.unpack_from(">IIIIq", data, offset)
        offset += 24
        payload = data[offset:offset + incl_len]
        offset += incl_len
        pkt_num += 1

        direction = "HOST→BT" if flags & 1 == 0 else "BT→HOST"
        # Print raw hex for RFCOMM-looking packets (heuristic: start with AA BB)
        if len(payload) > 4 and b"\xaa\xbb" in payload:
            idx = payload.index(b"\xaa\xbb")
            chunk = payload[idx:]
            print(f"\nPacket #{pkt_num} {direction} ts={ts_usec}")
            print(f"  Raw: {chunk.hex()}")
            if len(chunk) >= 7:
                cmd = chunk[2]
                seq = chunk[3]
                pay_len = int.from_bytes(chunk[4:6], "big")
                pay = chunk[6:6+pay_len]
                print(f"  CMD=0x{cmd:02x} SEQ={seq} PAYLOAD={pay.hex()}")

def main():
    ap = argparse.ArgumentParser(description="Parse CMF btsnoop HCI log")
    ap.add_argument("logfile", type=Path)
    ap.add_argument("--filter-addr", help="Filter by BT address (not yet implemented)")
    args = ap.parse_args()
    parse_btsnoop(args.logfile, args.filter_addr)

if __name__ == "__main__":
    main()
