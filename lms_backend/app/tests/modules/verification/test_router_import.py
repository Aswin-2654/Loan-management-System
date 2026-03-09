from app.modules.verification.router import router


def test_verification_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
