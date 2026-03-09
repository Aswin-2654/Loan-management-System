from app.modules.emi.router import router


def test_emi_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
