import subprocess
import re
from dataclasses import dataclass

CMF_NAME_PATTERN = re.compile(r"cmf|nothing", re.IGNORECASE)

@dataclass
class BTDevice:
    address: str
    name: str

def scan_devices(timeout: int = 8) -> list[BTDevice]:
    """Return paired BT devices matching CMF/Nothing name pattern."""
    result = subprocess.run(
        ["bluetoothctl", "devices"],
        capture_output=True, text=True, timeout=timeout
    )
    devices = []
    for line in result.stdout.splitlines():
        # Format: "Device AA:BB:CC:DD:EE:FF Device Name"
        parts = line.strip().split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            addr, name = parts[1], parts[2]
            if CMF_NAME_PATTERN.search(name):
                devices.append(BTDevice(address=addr, name=name))
    return devices
