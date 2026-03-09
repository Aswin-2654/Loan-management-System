from app.modules.manager.router import router


def test_manager_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
