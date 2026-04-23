import pandas as pd
import pytest

from features import build_model_frame


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_transactions(**overrides):
    data = {
        "transaction_id": [1],
        "account_id": [100],
        "amount_usd": [50.0],
        "failed_logins_24h": [0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def make_accounts(**overrides):
    data = {
        "account_id": [100],
        "prior_chargebacks": [0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# is_large_amount flag
# ---------------------------------------------------------------------------

def test_is_large_amount_set_at_1000():
    df = build_model_frame(make_transactions(amount_usd=[1000.0]), make_accounts())
    assert df["is_large_amount"].iloc[0] == 1


def test_is_large_amount_not_set_below_1000():
    df = build_model_frame(make_transactions(amount_usd=[999.99]), make_accounts())
    assert df["is_large_amount"].iloc[0] == 0


def test_is_large_amount_set_above_1000():
    df = build_model_frame(make_transactions(amount_usd=[2500.0]), make_accounts())
    assert df["is_large_amount"].iloc[0] == 1


def test_is_large_amount_not_set_for_small_amount():
    df = build_model_frame(make_transactions(amount_usd=[45.0]), make_accounts())
    assert df["is_large_amount"].iloc[0] == 0


# ---------------------------------------------------------------------------
# login_pressure categories
# ---------------------------------------------------------------------------

def test_login_pressure_none_at_zero():
    df = build_model_frame(make_transactions(failed_logins_24h=[0]), make_accounts())
    assert str(df["login_pressure"].iloc[0]) == "none"


def test_login_pressure_low_at_one():
    df = build_model_frame(make_transactions(failed_logins_24h=[1]), make_accounts())
    assert str(df["login_pressure"].iloc[0]) == "low"


def test_login_pressure_low_at_two():
    df = build_model_frame(make_transactions(failed_logins_24h=[2]), make_accounts())
    assert str(df["login_pressure"].iloc[0]) == "low"


def test_login_pressure_high_at_three():
    df = build_model_frame(make_transactions(failed_logins_24h=[3]), make_accounts())
    assert str(df["login_pressure"].iloc[0]) == "high"


def test_login_pressure_high_at_large_value():
    df = build_model_frame(make_transactions(failed_logins_24h=[10]), make_accounts())
    assert str(df["login_pressure"].iloc[0]) == "high"


# ---------------------------------------------------------------------------
# Account merge behaviour
# ---------------------------------------------------------------------------

def test_all_transactions_preserved_after_merge():
    txns = pd.DataFrame({
        "transaction_id": [1, 2, 3],
        "account_id": [100, 100, 100],
        "amount_usd": [50.0, 100.0, 200.0],
        "failed_logins_24h": [0, 0, 0],
    })
    df = build_model_frame(txns, make_accounts())
    assert len(df) == 3


def test_account_prior_chargebacks_joined():
    accounts = pd.DataFrame({"account_id": [100], "prior_chargebacks": [3]})
    df = build_model_frame(make_transactions(), accounts)
    assert df["prior_chargebacks"].iloc[0] == 3


def test_multiple_accounts_joined_correctly():
    txns = pd.DataFrame({
        "transaction_id": [1, 2],
        "account_id": [100, 200],
        "amount_usd": [50.0, 50.0],
        "failed_logins_24h": [0, 0],
    })
    accounts = pd.DataFrame({
        "account_id": [100, 200],
        "prior_chargebacks": [0, 5],
    })
    df = build_model_frame(txns, accounts)
    assert df.loc[df["account_id"] == 100, "prior_chargebacks"].iloc[0] == 0
    assert df.loc[df["account_id"] == 200, "prior_chargebacks"].iloc[0] == 5
