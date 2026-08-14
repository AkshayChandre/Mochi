import json

from mochi import world
from mochi.constants import OFFLINE_REPLY

GEO = {"results": [{"name": "Hyderabad", "country": "India", "latitude": 17.4, "longitude": 78.5}]}
FORECAST = {
    "current": {"temperature_2m": 28.4, "apparent_temperature": 31.0, "weather_code": 61},
    "daily": {"temperature_2m_max": [33.0], "temperature_2m_min": [24.0]},
}
RSS = b"""<?xml version="1.0"?><rss><channel>
<item><title>  First story  </title></item>
<item><title>Second story</title></item>
<item><title>Third story</title></item>
</channel></rss>"""


def route(monkeypatch, table):
    def fake(url):
        for key, payload in table.items():
            if key in url:
                return payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        raise OSError("unrouted")

    monkeypatch.setattr(world, "fetch", fake)


def test_weather_reads_like_speech_not_json(monkeypatch):
    route(monkeypatch, {"geocoding": GEO, "forecast": FORECAST})
    said = world.weather("Hyderabad")
    assert "Hyderabad, India" in said
    assert "28 degrees" in said and "raining lightly" in said
    assert "24 to 33" in said and "feels like 31" in said


def test_unknown_place_says_so_rather_than_guessing(monkeypatch):
    route(monkeypatch, {"geocoding": {"results": []}})
    assert "Nowhereville" in world.weather("Nowhereville")


def test_weather_offline_is_words_not_an_exception(monkeypatch):
    monkeypatch.setattr(world, "fetch", lambda url: (_ for _ in ()).throw(OSError("down")))
    assert world.weather("Hyderabad") == OFFLINE_REPLY
    assert world.headlines() == OFFLINE_REPLY


def test_headlines_are_trimmed_and_capped(monkeypatch):
    route(monkeypatch, {"http": RSS})
    out = world.headlines(limit=2)
    assert out.startswith("First story")
    assert len(out.split("; ")) == 2


def test_one_dead_feed_does_not_kill_the_rest(monkeypatch):
    def fake(url):
        if "thehindu" in url:
            raise OSError("down")
        return RSS

    monkeypatch.setattr(world, "fetch", fake)
    assert "First story" in world.headlines()


def test_look_up_falls_back_to_search_when_the_title_misses(monkeypatch):
    calls = []

    def fake(url):
        calls.append(url)
        if url.endswith("summary/Chandrayaan"):
            raise OSError("404")
        if "list=search" in url:
            return json.dumps({"query": {"search": [{"title": "Chandrayaan-3"}]}}).encode()
        return json.dumps({"extract": "An Indian lunar mission."}).encode()

    monkeypatch.setattr(world, "fetch", fake)
    assert world.look_up("Chandrayaan") == "An Indian lunar mission."
    assert any("list=search" in c for c in calls)


def test_shorten_cuts_on_a_sentence_boundary():
    long = ("Sentence one is here. " * 40).strip()
    out = world.shorten(long)
    assert len(out) <= 320 and out.endswith(".")
