"""
Regression tests for lease-cost comparison tolerance.

`OrderResponseHandler.is_order_resp_valid` compared independently-computed sat
costs with strict `!=`. The LSP and the customer each recompute the lease cost
(and the customer additionally derives the invoice amount via
`round(float(amount) * 1e8)`), so a single-satoshi rounding difference — or a
marginally stale ad — would abort an otherwise-valid order. These tests pin the
`costs_match` helper that replaces the strict comparison with a bounded
tolerance.
"""
from publsp.blip51.utils import LEASE_COST_TOLERANCE_SAT, costs_match


def test_exact_match_within_tolerance():
    assert costs_match(1000, 1000)


def test_off_by_one_is_tolerated():
    # a single-sat rounding drift must not abort the order
    assert costs_match(1000, 1001)
    assert costs_match(1001, 1000)


def test_tolerance_is_symmetric():
    assert costs_match(1000, 1000 + LEASE_COST_TOLERANCE_SAT)
    assert costs_match(1000, 1000 - LEASE_COST_TOLERANCE_SAT)


def test_difference_beyond_tolerance_is_rejected():
    beyond = LEASE_COST_TOLERANCE_SAT + 1
    assert not costs_match(1000, 1000 + beyond)
    assert not costs_match(1000, 1000 - beyond)


def test_default_tolerance_is_one_sat():
    # documents the shipped default; change deliberately if the policy changes
    assert LEASE_COST_TOLERANCE_SAT == 1


def test_custom_tolerance_argument_is_honoured():
    assert costs_match(1000, 1005, tolerance=5)
    assert not costs_match(1000, 1006, tolerance=5)
    # zero tolerance restores strict equality
    assert costs_match(1000, 1000, tolerance=0)
    assert not costs_match(1000, 1001, tolerance=0)
