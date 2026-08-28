from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from mochi.constants import CITY_TZ
from mochi.desktop import active_window, app_name, document_name


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
