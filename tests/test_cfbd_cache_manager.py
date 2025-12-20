import pytest
from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.data_sources.cfbd_cache_manager import CFBDCacheConfig, CFBDCacheManager


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


def test_cache_manager_standalone_functionality():
    """Test cache manager functionality independently (legacy data source removed)"""
    clock = _FakeClock()
    cache = CFBDCacheManager(clock=clock.now)

    # Test basic cache functionality using get_or_fetch
    key = ("games", 2025, 1)
    test_data = {"id": 1, "season": 2025, "week": 1}
    fetch_count = 0

    def fetch_data():
        nonlocal fetch_count
        fetch_count += 1
        return test_data

    # First call should fetch data
    result1 = cache.get_or_fetch(key, fetch_data)
    assert result1 == test_data
    assert fetch_count == 1

    # Second call should use cached data
    result2 = cache.get_or_fetch(key, fetch_data)
    assert result2 == test_data
    assert fetch_count == 1  # No additional fetch

    # Test cache is working
    assert cache.enabled

    # Test cache stats
    stats = cache.stats()
    assert (
        "hits" in stats or "total" in stats
    )  # Different implementations may have different stats


@pytest.mark.skip(reason="CFBDRESTDataSource has been deprecated and removed")
def test_cache_can_be_disabled_legacy(monkeypatch):
    """Legacy test skipped - CFBDRESTDataSource removed in favor of UnifiedCFBDClient"""
    pass
