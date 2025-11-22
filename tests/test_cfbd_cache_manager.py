import pytest

from src.data_sources.cfbd_cache_manager import CFBDCacheManager, CFBDCacheConfig
from src.data_sources.cfbd_client import CFBDRESTDataSource, CFBDClientConfig


class _FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def advance(self, amount: float) -> None:
        self.value += amount


def test_cache_manager_respects_ttl(monkeypatch):
    clock = _FakeClock()
    config = CFBDCacheConfig(
        enabled=True,
        default_ttl_seconds=60,
        ttl_overrides={"games": 10},
    )
    manager = CFBDCacheManager(config=config, clock=clock.now)

    calls = {"count": 0}

    def _fetch():
        calls["count"] += 1
        return {"value": calls["count"]}

    params = {"year": 2025, "week": 1}

    first = manager.get_or_fetch("games", params, _fetch)
    second = manager.get_or_fetch("games", params, _fetch)
    assert first == second
    assert calls["count"] == 1

    clock.advance(11)
    third = manager.get_or_fetch("games", params, _fetch)
    assert third["value"] == 2
    assert calls["count"] == 2


class _FakeClient:
    def __init__(self):
        self.calls = 0

    def get_games(self, **kwargs):
        self.calls += 1
        return {"payload": self.calls, "params": kwargs}


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("CFBD_API_KEY", "test-token")


def test_rest_data_source_uses_cache(monkeypatch):
    clock = _FakeClock()
    cache = CFBDCacheManager(clock=clock.now)
    client = _FakeClient()

    ds = CFBDRESTDataSource(client=client, config=CFBDClientConfig(api_key="token"), cache_manager=cache)

    result_one = ds.fetch_games(year=2025, week=1)
    result_two = ds.fetch_games(year=2025, week=1)
    assert result_one == result_two
    assert client.calls == 1

    clock.advance(20 * 60)  # exceed default TTL
    result_three = ds.fetch_games(year=2025, week=1)
    assert result_three != result_one
    assert client.calls == 2


def test_cache_can_be_disabled(monkeypatch):
    monkeypatch.setenv("CFBD_CACHE_DISABLED", "1")
    client = _FakeClient()
    ds = CFBDRESTDataSource(client=client, config=CFBDClientConfig(api_key="token"))

    ds.fetch_games(year=2025, week=1)
    ds.fetch_games(year=2025, week=1)
    assert client.calls == 2

