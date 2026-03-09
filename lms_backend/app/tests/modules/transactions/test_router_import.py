from app.modules.transactions.router import router


def test_transactions_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
