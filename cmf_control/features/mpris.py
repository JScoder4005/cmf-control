"""MPRIS now-playing watcher.

Subscribes to org.mpris.MediaPlayer2 PropertiesChanged signals via dbus-python,
so changes arrive in real-time with no polling. Emits a Qt signal on every
metadata or playback status change.

Picks the "active" player when multiple are present: the one currently
reporting status=Playing, with fallback to the first MPRIS name on the bus.
"""
from __future__ import annotations

import base64
import logging
import os
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import unquote, urlparse

try:
    import dbus
    import dbus.mainloop.glib
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

log = logging.getLogger("cmf_control.mpris")

MPRIS_PREFIX = "org.mpris.MediaPlayer2."


@dataclass
class NowPlaying:
    status: str = "Stopped"     # Playing | Paused | Stopped
    title: str = ""
    artist: str = ""
    album: str = ""
    art_path: str = ""           # local file path (fetched/decoded if needed)
    player: str = ""             # bus name (e.g. org.mpris.MediaPlayer2.spotify)
    has_player: bool = False


def _playerctl_cmd(action: str, player: str | None = None) -> None:
    cmd = ["playerctl"]
    if player:
        cmd += ["-p", player.replace(MPRIS_PREFIX, "")]
    cmd.append(action)
    try:
        subprocess.run(cmd, capture_output=True, timeout=2, check=False)
    except Exception:
        log.exception("playerctl failed")


def play_pause(player: str | None = None):
    _playerctl_cmd("play-pause", player)


def next_track(player: str | None = None):
    _playerctl_cmd("next", player)


def prev_track(player: str | None = None):
    _playerctl_cmd("previous", player)


def _resolve_art(url: str) -> str:
    """Return a local file path for the given mpris:artUrl, or '' on failure."""
    if not url:
        return ""
    if url.startswith("file://"):
        return unquote(urlparse(url).path)
    if url.startswith("data:"):
        # data:image/jpeg;base64,...
        try:
            header, b64 = url.split(",", 1)
            ext = "png"
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
            path = os.path.join(tempfile.gettempdir(), f"cmf-art-inline.{ext}")
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            return path
        except Exception:
            return ""
    if url.startswith(("http://", "https://")):
        # Remote fetch — do it synchronously, we're already on a background thread.
        try:
            import urllib.request
            cache_name = f"cmf-art-{abs(hash(url)) & 0xffffffff:08x}.img"
            path = os.path.join(tempfile.gettempdir(), cache_name)
            if not os.path.exists(path):
                req = urllib.request.Request(url, headers={"User-Agent": "cmf-control/1"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    with open(path, "wb") as f:
                        f.write(resp.read())
            return path
        except Exception:
            log.exception("album art fetch failed")
            return ""
    return ""


class MprisWatcher:
    """Subscribe to MPRIS PropertiesChanged. Call start() once, stop() on shutdown.

    Shares the global DBusGMainLoop that bt.session already installs at import
    time, so no extra event loop plumbing here.
    """

    def __init__(self, on_change: Callable[[NowPlaying], None]):
        self._on_change = on_change
        self._bus: "dbus.SystemBus | None" = None
        self._state = NowPlaying()
        self._session_bus = None
        self._active_player: str | None = None

    def start(self) -> None:
        if not _DBUS_AVAILABLE:
            log.warning("dbus not available; MPRIS disabled")
            return
        try:
            self._session_bus = dbus.SessionBus()
        except Exception:
            log.exception("could not get SessionBus")
            return
        # Watch for players appearing/disappearing
        self._session_bus.add_signal_receiver(
            self._on_name_owner_changed,
            signal_name="NameOwnerChanged",
            dbus_interface="org.freedesktop.DBus",
        )
        # Watch for property changes on ANY MPRIS player (filter by bus name later)
        self._session_bus.add_signal_receiver(
            self._on_properties_changed,
            signal_name="PropertiesChanged",
            dbus_interface="org.freedesktop.DBus.Properties",
            path="/org/mpris/MediaPlayer2",
            sender_keyword="sender",
        )
        # Initial scan: pick an active player if any
        threading.Thread(target=self._initial_scan, daemon=True).start()

    def _initial_scan(self):
        try:
            names = self._session_bus.list_names()
            players = [n for n in names if n.startswith(MPRIS_PREFIX)]
            if not players:
                return
            self._pick_active_player(players)
        except Exception:
            log.exception("initial scan failed")

    def _pick_active_player(self, candidates: list[str] | None = None) -> None:
        if candidates is None:
            try:
                candidates = [n for n in self._session_bus.list_names()
                              if n.startswith(MPRIS_PREFIX)]
            except Exception:
                return
        if not candidates:
            self._active_player = None
            self._state = NowPlaying()
            self._on_change(self._state)
            return
        # Prefer one reporting Playing
        for name in candidates:
            try:
                proxy = self._session_bus.get_object(name, "/org/mpris/MediaPlayer2")
                props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
                status = str(props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus"))
                if status == "Playing":
                    self._active_player = name
                    self._load_current(name)
                    return
            except Exception:
                continue
        # No one is actively playing — pick the first and show its last-known state
        self._active_player = candidates[0]
        self._load_current(candidates[0])

    def _load_current(self, player_name: str) -> None:
        try:
            proxy = self._session_bus.get_object(player_name, "/org/mpris/MediaPlayer2")
            props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
            status = str(props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus"))
            meta = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            self._apply(player_name, status, dict(meta))
        except Exception:
            log.exception("load_current failed")

    def _apply(self, player: str, status: str, meta: dict) -> None:
        title = str(meta.get("xesam:title", "") or "")
        artists = meta.get("xesam:artist", [])
        if isinstance(artists, (list, tuple)):
            artist = ", ".join(str(a) for a in artists)
        else:
            artist = str(artists or "")
        album = str(meta.get("xesam:album", "") or "")
        art_url = str(meta.get("mpris:artUrl", "") or "")
        self._state = NowPlaying(
            status=status, title=title, artist=artist, album=album,
            art_path="", player=player, has_player=True,
        )
        # Fire now with no art, resolve art asynchronously so UI appears instantly
        self._on_change(self._state)
        if art_url:
            threading.Thread(
                target=self._resolve_and_push, args=(art_url, title, artist),
                daemon=True,
            ).start()

    def _resolve_and_push(self, url: str, title: str, artist: str):
        path = _resolve_art(url)
        if not path:
            return
        # Only push if the track hasn't changed in the meantime
        if self._state.title == title and self._state.artist == artist:
            self._state.art_path = path
            self._on_change(self._state)

    def _on_properties_changed(self, interface, changed, invalidated, sender=None):
        if interface != "org.mpris.MediaPlayer2.Player":
            return
        # Resolve sender bus name to the owning MPRIS player name
        bus_name = self._name_for_sender(sender) if sender else self._active_player
        if not bus_name:
            self._pick_active_player()
            return
        # If this player wasn't the active one, decide whether to switch
        if bus_name != self._active_player:
            status = str(changed.get("PlaybackStatus", ""))
            if status == "Playing":
                self._active_player = bus_name
            else:
                return
        status = str(changed.get("PlaybackStatus", self._state.status))
        if "Metadata" in changed:
            self._apply(bus_name, status, dict(changed["Metadata"]))
        else:
            # Just a status change; keep metadata as-is
            self._state.status = status
            self._on_change(self._state)

    def _name_for_sender(self, sender: str) -> str | None:
        try:
            for name in self._session_bus.list_names():
                if not name.startswith(MPRIS_PREFIX):
                    continue
                owner = self._session_bus.get_name_owner(name)
                if owner == sender:
                    return name
        except Exception:
            pass
        return None

    def _on_name_owner_changed(self, name, old_owner, new_owner):
        if not str(name).startswith(MPRIS_PREFIX):
            return
        if str(new_owner) == "":  # player quit
            if name == self._active_player:
                self._active_player = None
                self._state = NowPlaying()
                self._on_change(self._state)
                self._pick_active_player()
        else:  # new player appeared
            if self._active_player is None:
                self._pick_active_player()
