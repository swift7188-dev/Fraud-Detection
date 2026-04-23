from risk_rules import label_risk, score_transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def base_tx(**overrides):
    """Low-risk baseline transaction. Override individual fields per test."""
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 50.0,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    tx.update(overrides)
    return tx


# ---------------------------------------------------------------------------
# label_risk thresholds
# ---------------------------------------------------------------------------

def test_label_risk_low():
    assert label_risk(0) == "low"
    assert label_risk(29) == "low"


def test_label_risk_medium():
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"


def test_label_risk_high():
    assert label_risk(60) == "high"
    assert label_risk(100) == "high"


# ---------------------------------------------------------------------------
# Device risk score
# ---------------------------------------------------------------------------

def test_high_device_risk_adds_score():
    low = score_transaction(base_tx(device_risk_score=10))
    high = score_transaction(base_tx(device_risk_score=75))
    assert high > low


def test_high_device_risk_adds_25():
    score_no_device = score_transaction(base_tx(device_risk_score=10))
    score_high_device = score_transaction(base_tx(device_risk_score=70))
    assert score_high_device - score_no_device == 25


def test_medium_device_risk_adds_10():
    score_low = score_transaction(base_tx(device_risk_score=10))
    score_medium = score_transaction(base_tx(device_risk_score=50))
    assert score_medium - score_low == 10


def test_low_device_risk_adds_nothing():
    score_a = score_transaction(base_tx(device_risk_score=0))
    score_b = score_transaction(base_tx(device_risk_score=39))
    assert score_a == score_b


# ---------------------------------------------------------------------------
# International flag
# ---------------------------------------------------------------------------

def test_international_adds_risk():
    domestic = score_transaction(base_tx(is_international=0))
    international = score_transaction(base_tx(is_international=1))
    assert international > domestic


def test_international_adds_15():
    domestic = score_transaction(base_tx(is_international=0))
    international = score_transaction(base_tx(is_international=1))
    assert international - domestic == 15


# ---------------------------------------------------------------------------
# Transaction amount
# ---------------------------------------------------------------------------

def test_large_amount_adds_risk():
    low = score_transaction(base_tx(amount_usd=100))
    high = score_transaction(base_tx(amount_usd=1200))
    assert high >= low + 25


def test_medium_amount_adds_10():
    below = score_transaction(base_tx(amount_usd=100))
    medium = score_transaction(base_tx(amount_usd=600))
    assert medium - below == 10


def test_large_amount_adds_25():
    below = score_transaction(base_tx(amount_usd=100))
    large = score_transaction(base_tx(amount_usd=1000))
    assert large - below == 25


# ---------------------------------------------------------------------------
# Transaction velocity
# ---------------------------------------------------------------------------

def test_high_velocity_adds_risk():
    low = score_transaction(base_tx(velocity_24h=1))
    high = score_transaction(base_tx(velocity_24h=8))
    assert high > low


def test_high_velocity_adds_20():
    low = score_transaction(base_tx(velocity_24h=1))
    high = score_transaction(base_tx(velocity_24h=6))
    assert high - low == 20


def test_medium_velocity_adds_5():
    low = score_transaction(base_tx(velocity_24h=1))
    medium = score_transaction(base_tx(velocity_24h=4))
    assert medium - low == 5


def test_low_velocity_adds_nothing():
    score_a = score_transaction(base_tx(velocity_24h=1))
    score_b = score_transaction(base_tx(velocity_24h=2))
    assert score_a == score_b


# ---------------------------------------------------------------------------
# Failed logins
# ---------------------------------------------------------------------------

def test_high_failed_logins_adds_20():
    none = score_transaction(base_tx(failed_logins_24h=0))
    high = score_transaction(base_tx(failed_logins_24h=5))
    assert high - none == 20


def test_medium_failed_logins_adds_10():
    none = score_transaction(base_tx(failed_logins_24h=0))
    medium = score_transaction(base_tx(failed_logins_24h=3))
    assert medium - none == 10


# ---------------------------------------------------------------------------
# Prior chargebacks
# ---------------------------------------------------------------------------

def test_prior_chargebacks_two_or_more_adds_risk():
    clean = score_transaction(base_tx(prior_chargebacks=0))
    repeat = score_transaction(base_tx(prior_chargebacks=2))
    assert repeat > clean


def test_prior_chargebacks_two_adds_20():
    clean = score_transaction(base_tx(prior_chargebacks=0))
    repeat = score_transaction(base_tx(prior_chargebacks=2))
    assert repeat - clean == 20


def test_prior_chargebacks_one_adds_5():
    clean = score_transaction(base_tx(prior_chargebacks=0))
    one = score_transaction(base_tx(prior_chargebacks=1))
    assert one - clean == 5


# ---------------------------------------------------------------------------
# Score clamping
# ---------------------------------------------------------------------------

def test_score_minimum_is_zero():
    assert score_transaction(base_tx()) == 0


def test_score_maximum_is_100():
    score = score_transaction(base_tx(
        device_risk_score=90,
        is_international=1,
        amount_usd=5000,
        velocity_24h=10,
        failed_logins_24h=10,
        prior_chargebacks=5,
    ))
    assert score == 100


# ---------------------------------------------------------------------------
# Exact threshold boundary crossings
# Verify the scoring step-change at each tier boundary.
# ---------------------------------------------------------------------------

def test_device_risk_boundary_40():
    below = score_transaction(base_tx(device_risk_score=39))
    at = score_transaction(base_tx(device_risk_score=40))
    assert at - below == 10


def test_device_risk_boundary_70():
    below = score_transaction(base_tx(device_risk_score=69))
    at = score_transaction(base_tx(device_risk_score=70))
    assert at - below == 15  # jumps from +10 to +25


def test_amount_boundary_500():
    below = score_transaction(base_tx(amount_usd=499.99))
    at = score_transaction(base_tx(amount_usd=500.0))
    assert at - below == 10


def test_amount_boundary_1000():
    below = score_transaction(base_tx(amount_usd=999.99))
    at = score_transaction(base_tx(amount_usd=1000.0))
    assert at - below == 15  # jumps from +10 to +25


def test_velocity_boundary_3():
    below = score_transaction(base_tx(velocity_24h=2))
    at = score_transaction(base_tx(velocity_24h=3))
    assert at - below == 5


def test_velocity_boundary_6():
    below = score_transaction(base_tx(velocity_24h=5))
    at = score_transaction(base_tx(velocity_24h=6))
    assert at - below == 15  # jumps from +5 to +20


def test_failed_logins_boundary_2():
    below = score_transaction(base_tx(failed_logins_24h=1))
    at = score_transaction(base_tx(failed_logins_24h=2))
    assert at - below == 10


def test_failed_logins_boundary_5():
    below = score_transaction(base_tx(failed_logins_24h=4))
    at = score_transaction(base_tx(failed_logins_24h=5))
    assert at - below == 10  # jumps from +10 to +20


def test_prior_chargebacks_boundary_1():
    below = score_transaction(base_tx(prior_chargebacks=0))
    at = score_transaction(base_tx(prior_chargebacks=1))
    assert at - below == 5


def test_prior_chargebacks_boundary_2():
    below = score_transaction(base_tx(prior_chargebacks=1))
    at = score_transaction(base_tx(prior_chargebacks=2))
    assert at - below == 15  # jumps from +5 to +20


# ---------------------------------------------------------------------------
# Exact score for known transactions (regression anchors)
# ---------------------------------------------------------------------------

def test_exact_score_all_zero_signals():
    assert score_transaction(base_tx()) == 0


def test_exact_score_fully_loaded_high_risk():
    # device>=70 (+25), international (+15), amount>=1000 (+25),
    # velocity>=6 (+20), failed_logins>=5 (+20), prior_chargebacks>=2 (+20)
    # = 125, clamped to 100
    score = score_transaction(base_tx(
        device_risk_score=85,
        is_international=1,
        amount_usd=1400,
        velocity_24h=8,
        failed_logins_24h=7,
        prior_chargebacks=3,
    ))
    assert score == 100


def test_exact_score_medium_signals():
    # device 40-69 (+10), amount 500-999 (+10), velocity 3-5 (+5) = 25
    score = score_transaction(base_tx(
        device_risk_score=55,
        amount_usd=750,
        velocity_24h=4,
    ))
    assert score == 25


# ---------------------------------------------------------------------------
# Combined high-risk transaction (mirrors real chargeback cases)
# ---------------------------------------------------------------------------

def test_combined_high_risk_scores_high():
    score = score_transaction({
        "device_risk_score": 85,
        "is_international": 1,
        "amount_usd": 1400,
        "velocity_24h": 8,
        "failed_logins_24h": 7,
        "prior_chargebacks": 1,
    })
    assert label_risk(score) == "high"


def test_combined_low_risk_scores_low():
    score = score_transaction({
        "device_risk_score": 8,
        "is_international": 0,
        "amount_usd": 45.0,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    })
    assert label_risk(score) == "low"
