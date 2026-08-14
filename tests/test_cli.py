from agent_harness.cli.main import main


def test_cli_help(capsys):
    exit_code = main(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "agent-harness" in captured.out


def test_cli_credentials_show(capsys):
    exit_code = main(["credentials", "show"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "configured" in captured.out or "not configured" in captured.out

def test_cli_credentials_update_uses_hidden_input_and_does_not_echo_secret(capsys, monkeypatch):
    class FakeCredentialManager:
        def __init__(self):
            self.updated = None

        def update(self, secret):
            self.updated = secret

    manager = FakeCredentialManager()
    monkeypatch.setattr("agent_harness.cli.credentials.CredentialManager", lambda: manager)
    monkeypatch.setattr("agent_harness.cli.credentials.getpass", lambda prompt: "test-secret")

    exit_code = main(["credentials", "update"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert manager.updated == "test-secret"
    assert "test-secret" not in captured.out


def test_cli_credentials_clear_requires_confirmation(capsys, monkeypatch):
    class FakeCredentialManager:
        def __init__(self):
            self.cleared = False

        def clear(self):
            self.cleared = True

    manager = FakeCredentialManager()
    monkeypatch.setattr("agent_harness.cli.credentials.CredentialManager", lambda: manager)
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    exit_code = main(["credentials", "clear"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert manager.cleared is False
    assert "cancelled" in captured.out
