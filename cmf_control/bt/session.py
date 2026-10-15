"""
BTSession: BLE GATT connection to CMF Buds Pro 2.

Service:  0000fe2c-0000-1000-8000-00805f9b34fb
TX char:  fe2c1236 [write] or fe2c123a [write,notify]
RX char:  fe2c1235 [notify] — device sends responses here

Note: BudsLink uses RFCOMM but requires system Python (gi/dbus).
This implementation uses bleak (pure Python, pyenv-compatible).
"""
import asyncio
import threading
from bleak import BleakClient, BleakScanner

from cmf_control.protocol.codec import Message

# Backward-compat alias
Packet = Message

BLE_NAME     = "Buds Pro 2"
# Write to fe2c1236 (write-only), listen on fe2c1235 (notify)
# fe2c123a is read/write/notify but responses come on fe2c1235
TX_CHAR      = "fe2c1236-8366-4814-8eb0-01de32100bea"
RX_CHAR      = "fe2c1235-8366-4814-8eb0-01de32100bea"
RECV_TIMEOUT = 5.0


class BTSession:
    def __init__(self, address: str):
        self.address = address
        self._ble_address: str | None = None
        self._client: BleakClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._fsn = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._rx_buf = b""

    # ------------------------------------------------------------------ #
    #  Public sync API                                                     #
    # ------------------------------------------------------------------ #

    def connect(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        fut = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        fut.result(timeout=25)

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
        ble_addr = self.address
        try:
            client = BleakClient(ble_addr)
            await client.connect(timeout=8)
        except Exception:
            devices = await BleakScanner.discover(timeout=12)
            ble_addr = None
            for d in devices:
                name = d.name or ""
                if BLE_NAME in name or "CMF" in name:
                    ble_addr = d.address
                    break
            if not ble_addr:
                raise ConnectionError(
                    "Could not find CMF Buds Pro 2.\n"
                    "Put buds in ears, ensure BT on."
                )
            client = BleakClient(ble_addr)
            await client.connect(timeout=10)

        self._ble_address = ble_addr
        self._client = client
        await self._client.start_notify(RX_CHAR, self._on_notify)

    def _on_notify(self, handle, data: bytes) -> None:
        self._rx_buf += data
        # Try to parse complete messages from buffer
        while len(self._rx_buf) >= 8:
            try:
                msg = Message.decode(self._rx_buf)
                self._rx_buf = self._rx_buf[msg.wire_size:]
                fut = self._pending.pop(msg.command, None)
                if fut and not fut.done():
                    fut.set_result(msg)
            except ValueError:
                # Incomplete packet — wait for more data
                break

    async def _async_send(self, msg: Message) -> Message:
        fut: asyncio.Future = self._loop.create_future()
        self._pending[msg.command] = fut
        await self._client.write_gatt_char(TX_CHAR, msg.encode(), response=False)
        try:
            return await asyncio.wait_for(fut, timeout=RECV_TIMEOUT)
        except asyncio.TimeoutError:
            self._pending.pop(msg.command, None)
            return Message(command=msg.command, payload=b"")
