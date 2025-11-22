"""Regression tests for the CFBD client and dataset helpers."""
from __future__ import annotations

from typing import Any, Dict, List

import pytest
import responses

from cfbd_client import CFBDClient
from cfbd_client import client as client_module
from cfbd_client.datasets import (
    fetch_games,
    fetch_lines,
    fetch_ratings,
    fetch_recruiting,
    fetch_weather,
    fetch_media,
    fetch_predicted_points,
)

HOST_MAP = client_module.HOST_MAP


class FakeClock:
    def __init__(self) -> None:
        self.current = 1000.0
        self.sleep_calls: List[float] = []

    def monotonic(self) -> float:
        return self.current

    def sleep(self, duration: float) -> None:
        self.sleep_calls.append(duration)
        self.current += duration


@pytest.fixture
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    clock = FakeClock()
    monkeypatch.setattr(client_module, "time", clock)
    return clock


def test_missing_api_key_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CFBD_API_KEY", raising=False)
    with pytest.raises(ValueError, match="CFBD_API_KEY"):
        CFBDClient()


@pytest.mark.parametrize("host_key", ["production", "next"])
@responses.activate
def test_host_toggle(host_key: str) -> None:
    base_url = HOST_MAP[host_key]
    responses.add(
        responses.GET,
        f"{base_url}/games",
        json=[],
        status=200,
    )
    client = CFBDClient(api_key="test", host=host_key)
    client.get_games(year=2025)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url.startswith(f"{base_url}/games")


@responses.activate
def test_retry_on_500(monkeypatch: pytest.MonkeyPatch, fake_clock: FakeClock) -> None:
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", status=500)
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", status=500)
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", json=[], status=200)

    client = CFBDClient(api_key="test")
    client.get_games(year=2025)

    assert len(responses.calls) == 3
    # Backoff sleeps should include 1s and 2s entries (throttle sleeps are < 1s).
    long_sleeps = [delay for delay in fake_clock.sleep_calls if delay >= 1]
    assert long_sleeps == [1.0, 2.0]


@responses.activate
def test_rate_limit_retry_on_429(fake_clock: FakeClock) -> None:
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", status=429)
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", json=[], status=200)

    client = CFBDClient(api_key="test")
    client.get_games(year=2025)

    assert len(responses.calls) == 2
    assert any(pytest.approx(60.0) == delay for delay in fake_clock.sleep_calls)


@responses.activate
def test_throttling_enforced(fake_clock: FakeClock) -> None:
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", json=[], status=200)
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", json=[], status=200)

    client = CFBDClient(api_key="test")
    client.get_games(year=2025)
    # Advance fake clock by a small amount (< throttle interval) before next call.
    fake_clock.current += 0.05
    client.get_games(year=2025)

    # Expect at least one throttle sleep approximately (0.17 - 0.05) seconds.
    throttle_sleeps = [delay for delay in fake_clock.sleep_calls if delay < 1]
    assert any(pytest.approx(0.12, abs=1e-3) == delay for delay in throttle_sleeps)


@responses.activate
def test_metrics_snapshot(fake_clock: FakeClock) -> None:
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", status=500)
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", json=[], status=200)

    client = CFBDClient(api_key="test")
    client.get_games(year=2025)

    metrics = client.get_metrics()
    assert metrics["total_requests"] == 2
    assert metrics["successful_requests"] == 1
    assert metrics["server_errors"] == 1
    assert metrics["retries"] == 1


@responses.activate
def test_telemetry_hook_receives_events(fake_clock: FakeClock) -> None:
    responses.add(responses.GET, f"{HOST_MAP['production']}/games", json=[], status=200)
    events: List[Dict[str, Any]] = []

    client = CFBDClient(api_key="test", telemetry_hook=events.append)
    client.get_games(year=2025)

    assert len(events) == 1
    event = events[0]
    assert event["endpoint"] == "/games"
    assert event["outcome"] == "success"
    assert event["status"] == 200


@responses.activate
def test_fetch_games_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/games",
        json=[
            {
                "id": 1,
                "home_team": "Ohio State",
                "away_team": "Michigan State",
                "home_points": 35,
                "away_points": 21,
                "week": 11,
                "season": 2025,
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_games(client, year=2025, week=11)
    assert list(df.columns) == [
        "id",
        "home_team",
        "away_team",
        "home_points",
        "away_points",
        "week",
        "season",
        "fetched_at",
    ]
    assert df.iloc[0]["home_team"] == "ohio_state"


@responses.activate
def test_fetch_ratings_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/ratings",
        json=[
            {
                "team": "Ohio State",
                "conference": "Big Ten",
                "rating_type": "SP+",
                "rating": 30.5,
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_ratings(client, year=2025, week=11)
    assert list(df.columns) == [
        "team",
        "conference",
        "rating_type",
        "rating_value",
        "fetched_at",
    ]
    assert df.iloc[0]["rating_value"] == 30.5


@responses.activate
def test_fetch_lines_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/lines",
        json=[
            {
                "id": 123,
                "lines": [
                    {
                        "provider": "consensus",
                        "spread": -6.5,
                        "overUnder": 55.5,
                    }
                ],
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_lines(client, year=2025, week=11)
    assert list(df.columns) == [
        "game_id",
        "provider",
        "spread",
        "over_under",
        "fetched_at",
    ]
    assert df.iloc[0]["game_id"] == 123


@responses.activate
def test_fetch_recruiting_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/recruiting/teams",
        json=[
            {
                "team": "Ohio State",
                "rank": 1,
                "points": 312.5,
                "avgRating": 94.1,
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_recruiting(client, year=2025)
    assert list(df.columns) == [
        "team",
        "rank",
        "points",
        "avg_rating",
        "fetched_at",
    ]
    assert df.iloc[0]["avg_rating"] == 94.1


@responses.activate
def test_fetch_weather_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/game/weather",
        json=[
            {
                "game_id": 1,
                "home_team": "Ohio State",
                "away_team": "Michigan",
                "temperature": 65,
                "temperatureHigh": 70,
                "temperatureLow": 55,
                "windSpeed": 5,
                "condition": "Clear",
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_weather(client, year=2025, week=11)
    assert list(df.columns) == [
        "game_id",
        "home_team",
        "away_team",
        "temperature",
        "temperature_high",
        "temperature_low",
        "wind_speed",
        "weather_condition",
        "fetched_at",
    ]
    assert df.iloc[0]["weather_condition"] == "Clear"


@responses.activate
def test_fetch_media_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/game/media",
        json=[
            {
                "game_id": 10,
                "tv": "FOX",
                "radio": "OSU Radio",
                "satellite": "Ch 205",
                "internet": "FOX Sports",
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_media(client, year=2025, week=11)
    assert list(df.columns) == [
        "game_id",
        "tv",
        "radio",
        "satellite",
        "internet",
        "fetched_at",
    ]
    assert df.iloc[0]["tv"] == "FOX"


@responses.activate
def test_fetch_predicted_points_schema(fake_clock: FakeClock) -> None:
    responses.add(
        responses.GET,
        f"{HOST_MAP['production']}/ratings/predicted",
        json=[
            {
                "team": "Ohio State",
                "opponent": "Michigan",
                "predictedMargin": 7.5,
                "winProbability": 0.62,
                "isHome": True,
            }
        ],
        status=200,
    )

    client = CFBDClient(api_key="test")
    df = fetch_predicted_points(client, year=2025, week=11)
    assert list(df.columns) == [
        "team",
        "opponent",
        "predicted_margin",
        "win_probability",
        "is_home",
        "fetched_at",
    ]
    assert df.iloc[0]["predicted_margin"] == 7.5


