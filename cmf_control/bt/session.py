"""
BTSession: BLE connection to CMF Buds Pro 2.

Service:    0000fe2c-0000-1000-8000-00805f9b34fb
Write+RX:   fe2c123a-8366-4814-8eb0-01de32100bea  (read/write/notify)
"""
import asyncio
import threading
from bleak import BleakClient, BleakScanner

from cmf_control.protocol.codec import Message
from cmf_control.protocol.constants import CMD_BATTERY

# Backward-compat alias
Packet = Message

BLE_NAME       = "Buds Pro 2"
WRITE_CHAR     = "fe2c123a-8366-4814-8eb0-01de32100bea"
RECV_TIMEOUT   = 5.0


def _find_ble_address(known_classic_mac: str = "2C:BE:EE:F0:00:3C") -> str:
    """Scan BLE and return address of CMF Buds Pro 2."""
    async def _scan():
        devices = await BleakScanner.discover(timeout=10)
        for d in devices:
            if BLE_NAME in (d.name or ""):
                return d.address
            if d.address.upper() == known_classic_mac.upper():
                return d.address
        raise ConnectionError(
            f"CMF Buds Pro 2 not found in BLE scan. "
            "Put buds in ears and ensure Bluetooth is on."
        )
    return asyncio.get_event_loop().run_until_complete(_scan())


class BTSession:
    def __init__(self, address: str):
        # address can be classic MAC or BLE MAC
        self.address = address
        self._ble_address: str | None = None
        self._client: BleakClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._fsn = 0
        self._pending: dict[int, asyncio.Future] = {}

    # ------------------------------------------------------------------ #
    #  Public sync API (used by feature modules)                           #
    # ------------------------------------------------------------------ #

    def connect(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        fut = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        fut.result(timeout=20)

    def disconnect(self) -> None:
        if self._loop and self._client:
            fut = asyncio.run_coroutine_threadsafe(
                self._client.disconnect(), self._loop
            )
            try:
                fut.result(timeout=5)
            except Exception:
                pass
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def send(self, cmd: int, payload: bytes = b"") -> Message:
        if not self._loop or not self._client:
            raise ConnectionError("Not connected")
        fsn = self._fsn
        self._fsn = (self._fsn + 1) & 0xFF
        msg = Message(command=cmd, payload=payload, fsn=fsn)
        fut = asyncio.run_coroutine_threadsafe(
            self._async_send(msg), self._loop
        )
        return fut.result(timeout=RECV_TIMEOUT + 1)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ------------------------------------------------------------------ #
    #  Async internals                                                     #
    # ------------------------------------------------------------------ #

    async def _async_connect(self) -> None:
        # Try direct connect first (works if device was previously seen by BlueZ)
        # then fall back to scan-by-name
        ble_addr = self.address
        try:
            client = BleakClient(ble_addr)
            await client.connect(timeout=8)
        except Exception:
            # Scan to find BLE address by name
            devices = await BleakScanner.discover(timeout=12)
            ble_addr = None
            for d in devices:
                name = d.name or ""
                if BLE_NAME in name or "CMF" in name or "Nothing" in name:
                    ble_addr = d.address
                    break
            if not ble_addr:
                raise ConnectionError(
                    "Could not find CMF Buds Pro 2 in BLE scan.\n"
                    "Put buds in ears, ensure BT on."
                )
            client = BleakClient(ble_addr)
            await client.connect(timeout=10)
        self._ble_address = ble_addr
        self._client = client
        await self._client.start_notify(WRITE_CHAR, self._on_notify)

    def _on_notify(self, handle, data: bytes) -> None:
        try:
            msg = Message.decode(data)
        except ValueError:
            return
        fut = self._pending.pop(msg.command, None)
        if fut and not fut.done():
            fut.set_result(msg)

    async def _async_send(self, msg: Message) -> Message:
        fut: asyncio.Future = self._loop.create_future()
        self._pending[msg.command] = fut
        await self._client.write_gatt_char(WRITE_CHAR, msg.encode())
        try:
            return await asyncio.wait_for(fut, timeout=RECV_TIMEOUT)
        except asyncio.TimeoutError:
            self._pending.pop(msg.command, None)
            # Return empty message so app doesn't crash — real data not parsed yet
            return Message(command=msg.command, payload=b"")
