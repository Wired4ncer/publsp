"""
Regression tests for OrderResponse default fields.

`order_id` and `created_at` were declared with `Field(default=...)`, whose
argument is evaluated once at class-definition time. Every OrderResponse built
without an explicit value therefore shared a single frozen order_id and a single
frozen creation timestamp. These tests assert the defaults are produced per
instance (i.e. via default_factory).
"""
from datetime import datetime, timezone

from publsp.blip51.order import OrderResponse, OrderState
from publsp.blip51.payment import Bolt11, HodlInvoiceState, Payment


def _make_response() -> OrderResponse:
    bolt11 = Bolt11(
        state=HodlInvoiceState.EXPECT_PAYMENT,
        expires_at=datetime.now(timezone.utc),
        fee_total_sat=100,
        order_total_sat=1000,
        invoice="lnbc10n1pdummyinvoice",
    )
    return OrderResponse(
        lsp_balance_sat=1000,
        client_balance_sat=0,
        required_channel_confirmations=0,
        funding_confirms_within_blocks=6,
        channel_expiry_blocks=4320,
        announce_channel=True,
        order_state=OrderState.CREATED,
        payment=Payment(bolt11=bolt11),
    )


def test_order_id_is_unique_per_instance():
    a = _make_response()
    b = _make_response()
    # frozen import-time default would make these equal
    assert a.order_id != b.order_id


def test_created_at_is_evaluated_per_instance():
    before = datetime.now(timezone.utc)
    resp = _make_response()
    after = datetime.now(timezone.utc)
    # frozen import-time default would fall outside this window
    assert before <= resp.created_at <= after
