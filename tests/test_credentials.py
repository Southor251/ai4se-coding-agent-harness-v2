from agent_harness.credentials.manager import CredentialManager


class FakeBackend:
    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


def test_credentials_status_hides_secret():
    backend = FakeBackend()
    manager = CredentialManager(backend=backend)
    manager.update("sample-token")

    status = manager.show_status()

    assert "configured" in status
    assert "sample-token" not in status


def test_credentials_clear_removes_secret():
    backend = FakeBackend()
    manager = CredentialManager(backend=backend)
    manager.update("sample-token")
    manager.clear()

    assert manager.get() is None
    assert manager.show_status() == "not configured"

def test_credentials_prefers_runtime_environment_over_stored_value(monkeypatch):
    backend = FakeBackend()
    manager = CredentialManager(backend=backend)
    manager.update("stored-token")
    monkeypatch.setenv("OPENAI_API_KEY", "runtime-token")

    assert manager.get() == "runtime-token"
