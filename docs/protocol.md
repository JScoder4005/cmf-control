# CMF Buds Pro 2 — Bluetooth Protocol

> Status: partially reverse-engineered. Verify bytes with tools/sniff.py on your device.

## Transport

Bluetooth Classic RFCOMM, SPP profile. UUID: `00001101-0000-1000-8000-00805f9b34fb`

## Packet Format

```
[AA BB] [CMD] [SEQ] [LEN_HI LEN_LO] [PAYLOAD...] [CHECKSUM]
```

- Magic: `0xAA 0xBB`
- CMD: command byte (see below)
- SEQ: sequence number, incremented per request, wraps at 0xFF
- LEN: 2-byte big-endian payload length
- CHECKSUM: sum of bytes from CMD to end of PAYLOAD, masked to 0xFF

## Known Commands

| CMD  | Direction | Description       |
|------|-----------|-------------------|
| 0x05 | host→buds | Get battery       |
| 0x06 | host→buds | Set ANC mode      |
| 0x07 | host→buds | Get ANC mode      |
| 0x08 | host→buds | Set EQ preset     |
| 0x09 | host→buds | Get EQ preset     |
| 0x0A | host→buds | Set gesture map   |
| 0x0B | host→buds | Get gesture map   |

## Battery Response Payload (CMD 0x05 response)

```
[LEFT%] [RIGHT%] [CASE%]
```

> ⚠️ All command bytes are UNVERIFIED. Use tools/sniff.py to confirm.
