from pathlib import Path

from agent_harness.cli.doctor import run_doctor
from agent_harness.cli.main import main


class FakeCredentialManager:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value


def _write_base_files(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "agent-harness.yaml").write_text("workspace_root: .\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")


def _write_mock_profile(tmp_path: Path) -> Path:
    profile = tmp_path / "config" / "mock-profile.yaml"
    profile.write_text(
        """
workspace_root: .
llm:
  provider: mock
  model: gpt-4
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return profile


def _write_openai_profile(tmp_path: Path) -> Path:
    profile = tmp_path / "config" / "openai.yaml"
    profile.write_text(
        """
workspace_root: .
llm:
  provider: openai
  model: example-model
  base_url: https://example.test/v1
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return profile


def test_doctor_safe_mock_profile_passes(tmp_path, monkeypatch):
    _write_base_files(tmp_path)
    profile = _write_mock_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_doctor(
        config_path="config/agent-harness.yaml",
        profile_path=str(profile),
        credential_manager=FakeCredentialManager(None),
    )

    rendered = report.render()
    assert report.ok
    assert "python" in rendered
    assert "provider" in rendered
    assert "mock" in rendered
    assert "run_shell is not registered" in rendered


def test_doctor_openai_credential_failure_reports_warn(tmp_path, monkeypatch):
    _write_base_files(tmp_path)
    profile = _write_openai_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_doctor(
        config_path="config/agent-harness.yaml",
        profile_path=str(profile),
        credential_manager=FakeCredentialManager(None),
    )

    rendered = report.render()
    assert "credential" in rendered
    assert "not configured" in rendered


def test_doctor_configured_credential_is_redacted(tmp_path, monkeypatch):
    _write_base_files(tmp_path)
    profile = _write_openai_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_doctor(
        config_path="config/agent-harness.yaml",
        profile_path=str(profile),
        credential_manager=FakeCredentialManager("private-test-token"),
    )

    rendered = report.render()
    assert "configured; secret not displayed" in rendered
    assert "private-test-token" not in rendered


def test_doctor_cli_command_prints_report(tmp_path, monkeypatch, capsys):
    _write_base_files(tmp_path)
    profile = _write_mock_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "--config", "config/agent-harness.yaml", "--profile", str(profile)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "agent-harness doctor" in captured.out
    assert "result=ok" in captured.out


def test_doctor_does_not_expose_credential_exception_details(tmp_path, monkeypatch):
    class FailingCredentialManager:
        def get(self):
            raise RuntimeError("credential backend rejected secret-token")

    _write_base_files(tmp_path)
    profile = _write_openai_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_doctor(
        config_path="config/agent-harness.yaml",
        profile_path=str(profile),
        credential_manager=FailingCredentialManager(),
    )

    rendered = report.render()
    assert not report.ok
    assert "lookup failed; inspect secure local logs" in rendered
    assert "secret-token" not in rendered
