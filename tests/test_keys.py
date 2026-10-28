import json

import keyring
import pytest
from keyring.backend import KeyringBackend

from dottide import keys

KEY = {
    "type": "service_account",
    "client_email": "r@p.iam.gserviceaccount.com",
    "private_key": "x" * 1700,
}


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.store = {}

    def get_password(self, service, username):
        return self.store.get((service, username))

    def set_password(self, service, username, password):
        assert len(password) <= keys.CHUNK
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        self.store.pop((service, username), None)


@pytest.fixture
def other_os(monkeypatch):
    monkeypatch.setattr(keys.sys, "platform", "linux")
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    return backend


def test_store_and_read_in_chunks(tmp_path, other_os):
    path = tmp_path / "key.json"
    path.write_text(json.dumps(KEY))
    path.chmod(0o600)
    assert keys.store("dottide-main", str(path)) == KEY["client_email"]
    assert int(other_os.store[("dottide-main", "chunks")]) > 1
    assert keys.read("dottide-main") == KEY


def test_missing_item_says_how_to_fix(other_os):
    with pytest.raises(PermissionError, match="import-key"):
        keys.read("nothing-here")


def test_readable_key_file_warns(tmp_path, capsys):
    path = tmp_path / "key.json"
    path.write_text(json.dumps(KEY))
    path.chmod(0o644)
    assert keys.read_file(str(path)) == KEY
    assert "chmod 600" in capsys.readouterr().err
