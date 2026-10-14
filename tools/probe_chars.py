#!/usr/bin/env python3
"""
Brute-force probe: find correct TX/RX characteristic pair on fe2c service.

Known characteristics from live scan:
  fe2c1235 [write, notify]
  fe2c1236 [write]
  fe2c1237 [write, notify]
  fe2c1239 [read]
  fe2c123a [read, write, notify]
  fe2c1233 [read]
  fe2c1234 [write, notify]

Strategy:
  1. Connect to device
  2. Subscribe to all notify chars
  3. For each writable char, write CMD_BATTERY packet
  4. Collect all notifications for 3s
  5. Print which chars produced a 0x55-prefixed response

Run: python3 tools/probe_chars.py
"""
import asyncio
import struct
import sys

sys.path.insert(0, "/home/uday/Documents/NothingEarbuds")

from bleak import BleakClient, BleakScanner
from cmf_control.protocol.codec import Message, _crc16
from cmf_control.protocol.constants import CMD_BATTERY

BLE_NAME    = "Buds Pro 2"
SERVICE_UUID = "0000fe2c-0000-1000-8000-00805f9b34fb"

# Full UUIDs — bleak needs these
CHARS = {
    "1233": "fe2c1233-8366-4814-8eb0-01de32100bea",
    "1234": "fe2c1234-8366-4814-8eb0-01de32100bea",
    "1235": "fe2c1235-8366-4814-8eb0-01de32100bea",
    "1236": "fe2c1236-8366-4814-8eb0-01de32100bea",
    "1237": "fe2c1237-8366-4814-8eb0-01de32100bea",
    "1239": "fe2c1239-8366-4814-8eb0-01de32100bea",
    "123a": "fe2c123a-8366-4814-8eb0-01de32100bea",
}

WRITE_CHARS  = ["1234", "1235", "1236", "1237", "123a"]
NOTIFY_CHARS = ["1234", "1235", "1237", "123a"]


async def probe():
    print("Scanning for CMF Buds Pro 2...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, _: BLE_NAME in (d.name or ""), timeout=15
    )
    if not device:
        print("Device not found. Put buds in ears and ensure BT on.")
        return

    print(f"Found: {device.name} @ {device.address}")

    notifications: list[tuple[str, bytes]] = []  # (char_short, data)

    async with BleakClient(device.address) as client:
        # Discover actual services/chars on the device
        print("\n=== Discovered services ===")
        for svc in client.services:
            if "fe2c" in svc.uuid.lower():
                print(f"SVC: {svc.uuid}")
                for ch in svc.characteristics:
                    print(f"  CHAR: {ch.uuid}  props={ch.properties}")

        print("\n=== Subscribing to notify chars ===")
        for short, uuid in CHARS.items():
            try:
                char = client.services.get_characteristic(uuid)
                if char and "notify" in char.properties:
                    def make_handler(s):
                        def handler(_, data):
                            notifications.append((s, data))
                            prefix = "0x55 SOF ✓" if data[0] == 0x55 else f"SOF={data[0]:#04x}"
                            print(f"  NOTIFY {s}: {data.hex()}  [{prefix}]")
                        return handler
                    await client.start_notify(uuid, make_handler(short))
                    print(f"  Subscribed to {short}")
            except Exception as e:
                print(f"  {short}: subscribe failed — {e}")

        print("\n=== Probing write chars with CMD_BATTERY ===")
        pkt = Message(command=CMD_BATTERY, payload=b"", fsn=0).encode()
        print(f"Packet: {pkt.hex()}")

        for short in WRITE_CHARS:
            uuid = CHARS[short]
            try:
                char = client.services.get_characteristic(uuid)
                if not char:
                    print(f"  {short}: char not found on device")
                    continue
                if "write" not in char.properties and "write-without-response" not in char.properties:
                    print(f"  {short}: not writable (props={char.properties})")
                    continue
                print(f"\n  Writing to {short}...")
                notifications.clear()
                await client.write_gatt_char(uuid, pkt, response=True)
                await asyncio.sleep(3.0)
                if notifications:
                    print(f"  → Got {len(notifications)} notification(s) after writing to {short}")
                    for n_char, n_data in notifications:
                        sof_ok = "✓ VALID SOF" if n_data[0] == 0x55 else "✗ bad SOF"
                        print(f"     from {n_char}: {n_data.hex()}  {sof_ok}")
                else:
                    print(f"  → No notifications after writing to {short}")
            except Exception as e:
                print(f"  {short}: write failed — {e}")

        print("\n=== Also trying write-without-response chars ===")
        for short in WRITE_CHARS:
            uuid = CHARS[short]
            try:
                char = client.services.get_characteristic(uuid)
                if char and "write-without-response" in char.properties:
                    print(f"\n  Writing (no-response) to {short}...")
                    notifications.clear()
                    await client.write_gatt_char(uuid, pkt, response=False)
                    await asyncio.sleep(3.0)
                    if notifications:
                        for n_char, n_data in notifications:
                            sof_ok = "✓ VALID SOF" if n_data[0] == 0x55 else "✗ bad SOF"
                            print(f"     from {n_char}: {n_data.hex()}  {sof_ok}")
            except Exception as e:
                print(f"  {short} (no-resp): {e}")

    print("\n=== Done ===")


if __name__ == "__main__":
    asyncio.run(probe())
