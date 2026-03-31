import pytest
from datetime import datetime, timedelta
from app.services.rfm import RFMAnalyzer, RFMResult


@pytest.fixture
def sample_orders():
    """Sample order data for testing."""
    today = datetime.now()
    return [
        {"user_id": "u1", "event_time": (today - timedelta(days=1)).isoformat(), "amount": 500},
        {"user_id": "u1", "event_time": (today - timedelta(days=5)).isoformat(), "amount": 300},
        {"user_id": "u2", "event_time": (today - timedelta(days=10)).isoformat(), "amount": 200},
        {"user_id": "u3", "event_time": (today - timedelta(days=60)).isoformat(), "amount": 100},
        {"user_id": "u4", "event_time": (today - timedelta(days=90)).isoformat(), "amount": 50},
    ]


def test_rfm_basic(sample_orders):
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(sample_orders)

    assert "segment_distribution" in result
    assert "customers" in result
    assert "summary" in result
    assert result["summary"]["total_customers"] == 4  # u1 has 2 orders but is 1 customer


def test_rfm_champions_segment(sample_orders):
    """u1 has recent, frequent, high-value purchases - should be champion."""
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(sample_orders)

    u1 = next((c for c in result["customers"] if c["user_id"] == "u1"), None)
    assert u1 is not None
    assert u1["segment"] in ["champions", "loyal", "potential_loyalist"]


def test_rfm_lost_segment(sample_orders):
    """u4 has very old purchase - should be in low engagement segment."""
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(sample_orders)

    u4 = next((c for c in result["customers"] if c["user_id"] == "u4"), None)
    assert u4 is not None
    # u4 should not be high-value customer
    assert u4["segment"] not in ["champions", "loyal"]


def test_rfm_rfm_scores_range():
    """RFM scores should be 1-5."""
    orders = [
        {"user_id": "u1", "event_time": datetime.now().isoformat(), "amount": 1000},
    ]
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(orders)

    u1 = result["customers"][0]
    r, f, m = u1["rfm_score"]
    assert 1 <= r <= 5
    assert 1 <= f <= 5
    assert 1 <= m <= 5


def test_rfm_empty_orders():
    """Empty orders should return empty result."""
    analyzer = RFMAnalyzer()
    result = analyzer.analyze([])

    assert result["summary"]["total_customers"] == 0
    assert len(result["customers"]) == 0