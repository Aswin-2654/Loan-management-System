from app.modules.admin.router import router


def test_admin_router_importable():
    assert router is not None
    assert hasattr(router, "routes")
