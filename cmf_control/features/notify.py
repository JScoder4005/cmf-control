"""OS-native notification banner — mac (osascript) / Linux (notify-send)."""
import subprocess
import sys


def notify(title: str, message: str) -> None:
    try:
        if sys.platform == "darwin":
            script = (
                f'display notification "{_escape_applescript(message)}" '
                f'with title "{_escape_applescript(title)}"'
            )
            subprocess.run(["osascript", "-e", script], check=False)
        else:
            subprocess.run(["notify-send", title, message], check=False)
    except FileNotFoundError:
        pass


def _escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')
