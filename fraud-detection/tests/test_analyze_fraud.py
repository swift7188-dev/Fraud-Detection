from pathlib import Path

import pandas as pd
import pytest

from analyze_fraud import score_transactions, summarize_results

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_scored(
    ids=None,
    labels=None,
    amounts=None,
):
    """Minimal scored DataFrame for testing summarize_results."""
    ids = ids or [1, 2, 3, 4, 5]
    labels = labels or ["high", "high", "medium", "low", "low"]
    amounts = amounts or [500.0, 300.0, 200.0, 100.0, 50.0]
    return pd.DataFrame({
        "transaction_id": ids,
        "risk_label": labels,
        "amount_usd": amounts,
    })


def make_chargebacks(transaction_ids):
    return pd.DataFrame({"transaction_id": transaction_ids})


def make_txns(**overrides):
    data = {
        "transaction_id": [1],
        "account_id": [100],
        "amount_usd": [50.0],
        "device_risk_score": [10],
        "is_international": [0],
        "velocity_24h": [1],
        "failed_logins_24h": [0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def make_accounts(**overrides):
    data = {"account_id": [100], "prior_chargebacks": [0]}
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# summarize_results — column presence
# ---------------------------------------------------------------------------

def test_summary_has_required_columns():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    for col in ["risk_label", "transactions", "total_amount_usd", "avg_amount_usd",
                "chargebacks", "chargeback_rate"]:
        assert col in summary.columns, f"Missing column: {col}"


def test_summary_has_one_row_per_risk_label():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    assert set(summary["risk_label"]) == {"high", "medium", "low"}


# ---------------------------------------------------------------------------
# summarize_results — transaction counts
# ---------------------------------------------------------------------------

def test_transaction_count_high():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["transactions"] == 2


def test_transaction_count_low():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "low"].iloc[0]
    assert row["transactions"] == 2


def test_transaction_count_medium():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "medium"].iloc[0]
    assert row["transactions"] == 1


# ---------------------------------------------------------------------------
# summarize_results — dollar metrics
# ---------------------------------------------------------------------------

def test_total_amount_usd_high():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["total_amount_usd"] == pytest.approx(800.0)


def test_total_amount_usd_low():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "low"].iloc[0]
    assert row["total_amount_usd"] == pytest.approx(150.0)


def test_avg_amount_usd_high():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["avg_amount_usd"] == pytest.approx(400.0)


def test_avg_amount_usd_low():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "low"].iloc[0]
    assert row["avg_amount_usd"] == pytest.approx(75.0)


# ---------------------------------------------------------------------------
# summarize_results — chargeback counts
# ---------------------------------------------------------------------------

def test_chargeback_count_when_all_high_are_fraud():
    summary = summarize_results(make_scored(), make_chargebacks([1, 2]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["chargebacks"] == 2


def test_chargeback_count_partial():
    summary = summarize_results(make_scored(), make_chargebacks([1]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["chargebacks"] == 1


def test_chargeback_count_zero_when_none():
    summary = summarize_results(make_scored(), make_chargebacks([]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["chargebacks"] == 0


def test_chargeback_lands_in_correct_bucket():
    """A chargeback on a low-risk transaction counts in the low bucket, not high."""
    summary = summarize_results(make_scored(), make_chargebacks([4]))
    low_row = summary[summary["risk_label"] == "low"].iloc[0]
    high_row = summary[summary["risk_label"] == "high"].iloc[0]
    assert low_row["chargebacks"] == 1
    assert high_row["chargebacks"] == 0


# ---------------------------------------------------------------------------
# summarize_results — chargeback rate
# ---------------------------------------------------------------------------

def test_chargeback_rate_is_one_when_all_fraud():
    summary = summarize_results(make_scored(), make_chargebacks([1, 2]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["chargeback_rate"] == pytest.approx(1.0)


def test_chargeback_rate_is_zero_when_no_fraud():
    summary = summarize_results(make_scored(), make_chargebacks([1, 2]))
    row = summary[summary["risk_label"] == "low"].iloc[0]
    assert row["chargeback_rate"] == pytest.approx(0.0)


def test_chargeback_rate_is_half():
    summary = summarize_results(make_scored(), make_chargebacks([1]))
    row = summary[summary["risk_label"] == "high"].iloc[0]
    assert row["chargeback_rate"] == pytest.approx(0.5)


def test_chargeback_rate_equals_chargebacks_over_transactions():
    """Verify the formula: rate = chargebacks / transactions for each label."""
    summary = summarize_results(make_scored(), make_chargebacks([1, 2]))
    for _, row in summary.iterrows():
        if row["transactions"] > 0:
            expected = row["chargebacks"] / row["transactions"]
            assert row["chargeback_rate"] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# score_transactions — output shape and columns
# ---------------------------------------------------------------------------

def test_score_transactions_adds_risk_score_column():
    scored = score_transactions(make_txns(), make_accounts())
    assert "risk_score" in scored.columns


def test_score_transactions_adds_risk_label_column():
    scored = score_transactions(make_txns(), make_accounts())
    assert "risk_label" in scored.columns


def test_score_transactions_preserves_all_rows():
    txns = pd.DataFrame({
        "transaction_id": [1, 2, 3],
        "account_id": [100, 100, 100],
        "amount_usd": [50.0, 100.0, 200.0],
        "device_risk_score": [10, 10, 10],
        "is_international": [0, 0, 0],
        "velocity_24h": [1, 1, 1],
        "failed_logins_24h": [0, 0, 0],
    })
    scored = score_transactions(txns, make_accounts())
    assert len(scored) == 3


def test_score_transactions_risk_label_valid_values():
    scored = score_transactions(make_txns(), make_accounts())
    assert scored["risk_label"].iloc[0] in {"low", "medium", "high"}


def test_score_transactions_score_in_range():
    scored = score_transactions(make_txns(), make_accounts())
    assert 0 <= scored["risk_score"].iloc[0] <= 100


# ---------------------------------------------------------------------------
# score_transactions — prior_chargebacks joined from accounts
# ---------------------------------------------------------------------------

def test_prior_chargebacks_from_account_raises_score():
    """prior_chargebacks lives in accounts.csv — verify the join feeds scoring."""
    clean = make_accounts(prior_chargebacks=[0])
    repeat = make_accounts(prior_chargebacks=[2])
    score_clean = score_transactions(make_txns(), clean)["risk_score"].iloc[0]
    score_repeat = score_transactions(make_txns(), repeat)["risk_score"].iloc[0]
    assert score_repeat > score_clean


def test_prior_chargebacks_two_adds_20_via_pipeline():
    score_clean = score_transactions(make_txns(), make_accounts(prior_chargebacks=[0]))["risk_score"].iloc[0]
    score_repeat = score_transactions(make_txns(), make_accounts(prior_chargebacks=[2]))["risk_score"].iloc[0]
    assert score_repeat - score_clean == 20


# ---------------------------------------------------------------------------
# Integration — real data regression
# ---------------------------------------------------------------------------

def load_real_data():
    accounts = pd.read_csv(DATA_DIR / "accounts.csv")
    transactions = pd.read_csv(DATA_DIR / "transactions.csv")
    chargebacks = pd.read_csv(DATA_DIR / "chargebacks.csv")
    return accounts, transactions, chargebacks


def test_seven_of_eight_chargebacks_score_high():
    """7 of 8 confirmed chargebacks land in 'high'. The exception is tx 50008
    (device_risk=68, velocity=5) which sits just below both high-tier thresholds
    and correctly scores 50 (medium) under the current rules."""
    accounts, transactions, chargebacks = load_real_data()
    scored = score_transactions(transactions, accounts)
    fraud_ids = set(chargebacks["transaction_id"])
    fraud_rows = scored[scored["transaction_id"].isin(fraud_ids)]
    high_count = (fraud_rows["risk_label"] == "high").sum()
    assert high_count == 7


def test_borderline_chargeback_scores_medium_not_low():
    """tx 50008 (device=68, velocity=5) is a confirmed chargeback that scores
    medium. It must not fall into 'low' where it would be invisible to the
    fraud team."""
    accounts, transactions, chargebacks = load_real_data()
    scored = score_transactions(transactions, accounts)
    row = scored[scored["transaction_id"] == 50008].iloc[0]
    assert row["risk_label"] == "medium"
    assert row["risk_score"] == 50


def test_high_bucket_chargeback_rate_is_one():
    accounts, transactions, chargebacks = load_real_data()
    scored = score_transactions(transactions, accounts)
    summary = summarize_results(scored, chargebacks)
    high_row = summary[summary["risk_label"] == "high"].iloc[0]
    assert high_row["chargeback_rate"] == pytest.approx(1.0)


def test_low_bucket_chargeback_rate_is_zero():
    accounts, transactions, chargebacks = load_real_data()
    scored = score_transactions(transactions, accounts)
    summary = summarize_results(scored, chargebacks)
    low_row = summary[summary["risk_label"] == "low"].iloc[0]
    assert low_row["chargeback_rate"] == pytest.approx(0.0)


def test_real_data_total_fraud_loss():
    """Total confirmed loss across all chargebacks matches the CSV."""
    _, _, chargebacks = load_real_data()
    assert chargebacks["loss_amount_usd"].sum() == pytest.approx(4854.98)


def test_real_data_high_bucket_fraud_dollars():
    """$4,234.98 of confirmed fraud loss sits in the high-risk bucket.
    The remaining $620 (tx 50008, medium) is accounted for separately."""
    accounts, transactions, chargebacks = load_real_data()
    scored = score_transactions(transactions, accounts)
    fraud_ids = set(chargebacks["transaction_id"])
    fraud_in_high = scored[
        scored["transaction_id"].isin(fraud_ids) & (scored["risk_label"] == "high")
    ]
    captured = fraud_in_high.merge(
        chargebacks[["transaction_id", "loss_amount_usd"]], on="transaction_id"
    )
    assert captured["loss_amount_usd"].sum() == pytest.approx(4234.98)


def test_real_data_medium_bucket_fraud_dollars():
    """tx 50008 ($620) is the only chargeback in the medium bucket."""
    accounts, transactions, chargebacks = load_real_data()
    scored = score_transactions(transactions, accounts)
    fraud_ids = set(chargebacks["transaction_id"])
    fraud_in_medium = scored[
        scored["transaction_id"].isin(fraud_ids) & (scored["risk_label"] == "medium")
    ]
    captured = fraud_in_medium.merge(
        chargebacks[["transaction_id", "loss_amount_usd"]], on="transaction_id"
    )
    assert captured["loss_amount_usd"].sum() == pytest.approx(620.0)
