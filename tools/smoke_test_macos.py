#!/usr/bin/env python3
"""
Manual connect + battery smoke test for the macOS IOBluetooth backend.

Usage:
  python tools/smoke_test_macos.py [AA:BB:CC:DD:EE:FF]
"""
import sys
from cmf_control.bt.session_macos import BTSession
from cmf_control.features.battery import get_battery


def main():
    address = sys.argv[1] if len(sys.argv) > 1 else None
    session = BTSession(address) if address else BTSession()
    print(f"Connecting to {session.address}...")
    session.connect()
    print("Connected. Requesting battery...")
    print(get_battery(session))
    session.disconnect()


if __name__ == "__main__":
    main()
