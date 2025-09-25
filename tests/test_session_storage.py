from bot_wb.storage.session import CookieStorage


def test_cookie_storage_crud(tmp_path):
    storage = CookieStorage(123, root=tmp_path)

    assert storage.load() == {}

    storage.save({"wbx-validation-key": "token"})
    assert storage.load() == {"wbx-validation-key": "token"}
    assert storage.cookies_path.exists()

    storage.clear()
    assert storage.load() == {}
    assert not storage.cookies_path.exists()
    assert not (tmp_path / "123").exists()
