from dataclasses import dataclass


@dataclass(frozen=True)
class EmiBreakdown:
    emi_cents: int
    total_payment_cents: int
    total_interest_cents: int


def calculate_emi(principal_cents: int, annual_interest_rate_bps: int, term_months: int) -> EmiBreakdown:
    """Standard reducing-balance EMI formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1),
    where r is the monthly interest rate and n is the term in months.

    Floating point is used for the amortization math itself (it's a computed estimate,
    not a ledger entry) but the result is rounded to integer cents before being returned,
    since that figure is what gets stored/displayed — money never stays a float past this
    boundary, same rule as everywhere else in the app.
    """
    if principal_cents <= 0:
        raise ValueError("principal_cents must be positive")
    if term_months <= 0:
        raise ValueError("term_months must be positive")
    if annual_interest_rate_bps < 0:
        raise ValueError("annual_interest_rate_bps must not be negative")

    monthly_rate = annual_interest_rate_bps / 10_000 / 12

    if monthly_rate == 0:
        emi = principal_cents / term_months
    else:
        factor = (1 + monthly_rate) ** term_months
        emi = principal_cents * monthly_rate * factor / (factor - 1)

    emi_cents = round(emi)
    total_payment_cents = emi_cents * term_months
    total_interest_cents = total_payment_cents - principal_cents

    return EmiBreakdown(
        emi_cents=emi_cents,
        total_payment_cents=total_payment_cents,
        total_interest_cents=total_interest_cents,
    )
