"""Return paired BT devices matching CMF/Nothing name pattern (macOS)."""
try:
    from IOBluetooth import IOBluetoothDevice
    _IOBT_AVAILABLE = True
except ImportError:
    _IOBT_AVAILABLE = False

from cmf_control.bt.scanner import BTDevice, CMF_NAME_PATTERN


def scan_devices(timeout: int = 8) -> list[BTDevice]:
    """timeout is unused on mac — pairedDevices() lists already-bonded
    devices instantly, same semantics as the Linux `bluetoothctl devices`
    call this mirrors (no active discovery, just known devices)."""
    if not _IOBT_AVAILABLE:
        raise RuntimeError(
            "pyobjc-framework-IOBluetooth required.\n"
            "Run: pip install pyobjc-framework-IOBluetooth"
        )
    devices = []
    for dev in IOBluetoothDevice.pairedDevices():
        name = dev.name() or ""
        if CMF_NAME_PATTERN.search(name):
            devices.append(BTDevice(address=dev.addressString(), name=name))
    return devices
