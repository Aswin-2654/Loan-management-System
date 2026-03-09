from app.modules.customer.router import router


def test_customer_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
