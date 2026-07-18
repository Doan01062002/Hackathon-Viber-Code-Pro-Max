from types import SimpleNamespace

from backend import redis_client


def test_get_redis_client_skips_network_in_test(monkeypatch):
    monkeypatch.setattr(
        redis_client,
        "get_settings",
        lambda: SimpleNamespace(app_env="test", redis_url="redis://should-not-connect"),
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Redis network client must not be created in test mode")

    monkeypatch.setattr(redis_client.redis.Redis, "from_url", fail_if_called)

    client = redis_client.get_redis_client()

    assert client is redis_client.MockRedis.get_mock_instance()
