from app.modules.payments.router import router


def test_payments_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
