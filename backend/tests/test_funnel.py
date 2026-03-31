import pytest
from app.services.funnel import FunnelAnalyzer


@pytest.fixture
def sample_events():
    return [
        {"user_id": "u1", "event_type": "impression", "event_time": "2024-01-01"},
        {"user_id": "u1", "event_type": "click", "event_time": "2024-01-01"},
        {"user_id": "u1", "event_type": "add_to_cart", "event_time": "2024-01-01"},
        {"user_id": "u2", "event_type": "impression", "event_time": "2024-01-01"},
        {"user_id": "u2", "event_type": "click", "event_time": "2024-01-01"},
        {"user_id": "u3", "event_type": "impression", "event_time": "2024-01-01"},
    ]


def test_funnel_analyzer_basic(sample_events):
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze(sample_events)

    assert result["total_users"] == 3
    assert len(result["funnel"]) == 5  # 5 default steps

    # Step: impression - all 3 users
    impression_step = result["funnel"][0]
    assert impression_step["step"] == "impression"
    assert impression_step["user_count"] == 3
    assert impression_step["conversion_rate"] == 1.0

    # Step: click - 2 users (2/3 rounded to 4 decimals = 0.6667)
    click_step = result["funnel"][1]
    assert click_step["step"] == "click"
    assert click_step["user_count"] == 2
    assert click_step["conversion_rate"] == 0.6667

    # Step: add_to_cart - 1 user
    cart_step = result["funnel"][2]
    assert cart_step["step"] == "add_to_cart"
    assert cart_step["user_count"] == 1


def test_funnel_biggest_dropoff(sample_events):
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze(sample_events)

    # add_to_cart has biggest dropoff (1/2 = 50%)
    assert result["biggest_dropoff"] is not None
    assert result["biggest_dropoff"]["step"] == "add_to_cart"


def test_funnel_empty_events():
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze([])

    assert result["total_users"] == 0
    assert all(step["user_count"] == 0 for step in result["funnel"])


def test_funnel_custom_steps():
    custom_steps = ["impression", "purchase"]
    analyzer = FunnelAnalyzer(steps=custom_steps)

    events = [
        {"user_id": "u1", "event_type": "impression"},
        {"user_id": "u2", "event_type": "impression"},
    ]

    result = analyzer.analyze(events)
    assert len(result["funnel"]) == 2
    assert result["funnel"][0]["step"] == "impression"
    assert result["funnel"][1]["step"] == "purchase"