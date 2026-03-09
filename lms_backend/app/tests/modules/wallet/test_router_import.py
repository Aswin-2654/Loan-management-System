from app.modules.wallet.router import router


def test_wallet_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
