import pytest

from app.services.emi import calculate_emi


def test_zero_interest_is_exact_straight_line():
    result = calculate_emi(principal_cents=1200, annual_interest_rate_bps=0, term_months=12)
    assert result.emi_cents == 100
    assert result.total_payment_cents == 1200
    assert result.total_interest_cents == 0


def test_known_reference_value_10000_at_12_percent_for_12_months():
    # $10,000 principal, 12% APR, 12-month term — a standard textbook EMI example.
    result = calculate_emi(principal_cents=1_000_000, annual_interest_rate_bps=1200, term_months=12)
    assert result.emi_cents == 88849
    assert result.total_payment_cents == 1_066_188
    assert result.total_interest_cents == 66_188


def test_total_payment_equals_emi_times_term():
    result = calculate_emi(principal_cents=500_000, annual_interest_rate_bps=750, term_months=24)
    assert result.total_payment_cents == result.emi_cents * 24
    assert result.total_interest_cents == result.total_payment_cents - 500_000


def test_higher_rate_gives_higher_emi():
    low = calculate_emi(principal_cents=1_000_000, annual_interest_rate_bps=500, term_months=24)
    high = calculate_emi(principal_cents=1_000_000, annual_interest_rate_bps=1500, term_months=24)
    assert high.emi_cents > low.emi_cents


def test_longer_term_lowers_emi_but_raises_total_interest():
    short = calculate_emi(principal_cents=1_000_000, annual_interest_rate_bps=1000, term_months=12)
    long_ = calculate_emi(principal_cents=1_000_000, annual_interest_rate_bps=1000, term_months=36)
    assert long_.emi_cents < short.emi_cents
    assert long_.total_interest_cents > short.total_interest_cents


@pytest.mark.parametrize(
    "principal_cents,annual_interest_rate_bps,term_months",
    [
        (0, 1000, 12),
        (-100, 1000, 12),
        (100_000, 1000, 0),
        (100_000, 1000, -5),
        (100_000, -1, 12),
    ],
)
def test_rejects_invalid_inputs(principal_cents, annual_interest_rate_bps, term_months):
    with pytest.raises(ValueError):
        calculate_emi(principal_cents, annual_interest_rate_bps, term_months)
