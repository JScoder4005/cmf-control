import subprocess


def pause_all_players() -> int:
    """Send pause to all active MPRIS players. Returns count of players paused."""
    try:
        out = subprocess.run(
            ["playerctl", "-l"], capture_output=True, text=True, timeout=2
        ).stdout
    except Exception:
        return 0
    paused = 0
    for name in out.splitlines():
        name = name.strip()
        if not name:
            continue
        try:
            subprocess.run(
                ["playerctl", "-p", name, "pause"],
                capture_output=True, timeout=2, check=False
            )
            paused += 1
        except Exception:
            pass
    return paused


def playerctl_available() -> bool:
    try:
        subprocess.run(["playerctl", "--version"], capture_output=True, timeout=1)
        return True
    except Exception:
        return False
