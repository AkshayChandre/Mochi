from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from mochi.constants import (
    FORECAST_URL,
    GEOCODE_URL,
    NEWS_FEEDS,
    NEWS_LIMIT,
    OFFLINE_REPLY,
    USER_AGENT,
    WEATHER_CODES,
    WIKI_MAX_CHARS,
    WIKI_SEARCH_URL,
    WIKI_SUMMARY_URL,
    WORLD_TIMEOUT,
)


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=WORLD_TIMEOUT) as resp:
        return resp.read()


def fetch_json(url: str):
    return json.loads(fetch(url))


def describe(code: int) -> str:
    return WEATHER_CODES.get(int(code), "hard to describe")


def weather(place: str) -> str:
    try:
        hits = fetch_json(GEOCODE_URL.format(q=quote(place.strip()))).get("results") or []
    except OSError:
        return OFFLINE_REPLY
    if not hits:
        return f"I couldn't find anywhere called {place}."
    spot = hits[0]
    try:
        data = fetch_json(
            FORECAST_URL.format(lat=spot["latitude"], lon=spot["longitude"])
        )
    except (OSError, KeyError):
        return OFFLINE_REPLY
    now, day = data.get("current", {}), data.get("daily", {})
    where = ", ".join(filter(None, (spot.get("name"), spot.get("country"))))
    sky = describe(now.get("weather_code", -1))
    parts = [f"{where}: {round(now.get('temperature_2m', 0))} degrees, {sky}"]
    highs, lows = day.get("temperature_2m_max") or [], day.get("temperature_2m_min") or []
    if highs and lows:
        parts.append(f"today {round(lows[0])} to {round(highs[0])}")
    if (feels := now.get("apparent_temperature")) is not None:
        parts.append(f"feels like {round(feels)}")
    return ", ".join(parts)


def headlines(limit: int = NEWS_LIMIT) -> str:
    per = max(1, limit // max(1, len(NEWS_FEEDS)))
    out: list[str] = []
    for feed in NEWS_FEEDS:
        try:
            root = ElementTree.fromstring(fetch(feed))
        except (OSError, ElementTree.ParseError):
            continue
        titles = [t.strip() for item in root.iter("item") if (t := item.findtext("title"))]
        out.extend(titles[:per])
    return "; ".join(out[:limit]) if out else OFFLINE_REPLY


def shorten(text: str) -> str:
    if len(text) <= WIKI_MAX_CHARS:
        return text
    cut = text[:WIKI_MAX_CHARS]
    return cut[: cut.rfind(".") + 1] or cut


def look_up(topic: str) -> str:
    topic = topic.strip()
    try:
        summary = fetch_json(WIKI_SUMMARY_URL.format(t=quote(topic.replace(" ", "_"))))
        if extract := summary.get("extract"):
            return shorten(extract)
    except OSError:
        pass
    try:  # the exact title missed, so let the search index pick one
        hits = fetch_json(WIKI_SEARCH_URL.format(q=quote(topic)))["query"]["search"]
        if not hits:
            return f"I couldn't find anything about {topic}."
        best = fetch_json(WIKI_SUMMARY_URL.format(t=quote(hits[0]["title"].replace(" ", "_"))))
        return shorten(best.get("extract") or f"I couldn't find anything about {topic}.")
    except (OSError, KeyError, IndexError):
        return OFFLINE_REPLY
