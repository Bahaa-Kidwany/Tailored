import pytest

from tailored_kit.feature_flags.client import FeatureFlagClient


@pytest.mark.asyncio
async def test_feature_flags_overrides_and_percentage_bucketing():
    client = FeatureFlagClient(
        defaults={
            "ai.ambient.proactive_nudges": {
                "enabled": True,
                "rollout_percent": 50,
                "overrides": {"vip-user": True, "blocked-user": False},
            },
            "billing.paymob": {"enabled": False, "rollout_percent": 100},
        }
    )

    assert await client.is_enabled("ai.ambient.proactive_nudges", user_id="vip-user") is True
    assert await client.is_enabled("ai.ambient.proactive_nudges", user_id="blocked-user") is False
    assert await client.is_enabled("billing.paymob", user_id="vip-user") is False
    assert await client.is_enabled("unknown.flag", default=True) is True

    # Deterministic stability for same user across calls
    first = await client.is_enabled("ai.ambient.proactive_nudges", user_id="regular-user-77")
    second = await client.is_enabled("ai.ambient.proactive_nudges", user_id="regular-user-77")
    assert first == second
