from __future__ import annotations

import ctypes
import sys
from datetime import datetime

from mochi.constants import OWN_WINDOW_PREFIX, WINDOW_TITLE_MAX

_last_other = ""

def active_window() -> str:
    """Mochi's own window is skipped: when you talk to it, its window is
    often focused, and 'you're in Mochi' is useless."""
    title = foreground_window()
    global _last_other
    if title and not title.startswith(OWN_WINDOW_PREFIX):
        _last_other = title
    return _last_other

def foreground_window() -> str:
    if not sys.platform.startswith("win"):
        return ""
    try:
        user32 = ctypes.windll.user32
        handle = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(handle)
        if not length:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(handle, buf, length + 1)
        return buf.value[:WINDOW_TITLE_MAX]
    except Exception:
        return ""

def app_name(title: str) -> str:
    # window titles are usually "document - App Name"
    return title.rsplit(" - ", 1)[-1].strip() if " - " in title else title

def document_name(title: str) -> str:
    """The file or page, which apps put FIRST: 'README.md - Mochi - VS Code'."""
    if " - " not in title:
        return ""
    # editors prefix unsaved files with a dot or star
    return title.split(" - ", 1)[0].strip().lstrip("*●•").strip()

def context_note() -> str:
    now = datetime.now()
    parts = [f"It is {now:%A %d %B %Y, %I:%M %p}."]
    if title := active_window():
        parts.append(f"The screen currently shows {title!r} (app: {app_name(title)}).")
    return " ".join(parts)
