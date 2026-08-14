from __future__ import annotations

from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from mochi.constants import CITY_TZ
from mochi.desktop import active_window, app_name, document_name


class Sensors(Protocol):
    """Where Mochi's senses live. Local today; a laptop agent reporting over
    the network can implement this same shape when the brain moves to a
    server, without the brain or tools changing."""

    def screen(self) -> tuple[str, str]: ...
    def clock(self, place: str = "") -> tuple[str, str]: ...

class LocalSensors:
    def screen(self) -> tuple[str, str]:
        title = active_window()
        return (app_name(title), document_name(title)) if title else ("", "")

    def clock(self, place: str = "") -> tuple[str, str]:
        key = place.lower().strip()
        for city, zone in CITY_TZ.items():
            if city in key:
                return datetime.now(ZoneInfo(zone)).strftime("%A %d %B, %I:%M %p"), city.title()
        return datetime.now().strftime("%A %d %B, %I:%M %p"), ""
