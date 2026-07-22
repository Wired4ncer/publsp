"""
Regression tests: an order referencing an unknown or no-longer-active ad id must
be answered with an OrderErrorResponse rather than crashing the order task.

verify_order_and_connection previously did a bare
`self.ad_handler.active_ads.ads[order.d]`, which raised KeyError (unknown id) or
AttributeError (no ad published yet, active_ads is None). Because orders are
handled as fire-and-forget asyncio tasks, that exception was swallowed and the
requesting client got no response at all.

These construct an OrderHandler with stub dependencies; the guarded path returns
before any Lightning-node call, so no node/relay is required.
"""
from types import SimpleNamespace

import pytest

from publsp.blip51.order import Order, OrderErrorResponse
from publsp.marketplace.lsp import OrderHandler


def _order_handler(active_ads) -> OrderHandler:
    return OrderHandler(
        ln_backend=None,
        ad_handler=SimpleNamespace(active_ads=active_ads),
        rumor_handler=None,
        nostr_client=None,
    )


@pytest.mark.asyncio
async def test_no_ad_published_returns_error():
    # active_ads is None before any ad has been published
    handler = _order_handler(active_ads=None)
    result = await handler.verify_order_and_connection(Order(d="any-id"))
    assert isinstance(result, OrderErrorResponse)


@pytest.mark.asyncio
async def test_unknown_ad_id_returns_error():
    # an ad set exists but does not contain the requested id
    handler = _order_handler(active_ads=SimpleNamespace(ads={}))
    result = await handler.verify_order_and_connection(Order(d="does-not-exist"))
    assert isinstance(result, OrderErrorResponse)
