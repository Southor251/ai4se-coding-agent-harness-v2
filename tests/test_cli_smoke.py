from pathlib import Path

from agent_harness.cli.main import main
from agent_harness.cli.smoke import DEFAULT_PROVIDER_SMOKE_GOAL, run_provider_smoke
from agent_harness.runtime.result import RunResult


class FakeCredentialManager:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value


def _write_base_files(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent-harness.yaml").write_text("workspace_root: .\n", encoding="utf-8")


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


def test_provider_smoke_rejects_mock_provider(tmp_path, monkeypatch):
    _write_base_files(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_provider_smoke(
        "config/agent-harness.yaml",
        credential_manager=FakeCredentialManager("private-test-token"),
        runner=_runner_should_not_be_called,
    )

    assert not report.ok
    assert "requires llm.provider=openai" in report.render()


def test_provider_smoke_requires_credential(tmp_path, monkeypatch):
    _write_base_files(tmp_path)
    profile = _write_openai_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    report = run_provider_smoke(
        "config/agent-harness.yaml",
        str(profile),
        credential_manager=FakeCredentialManager(None),
        runner=_runner_should_not_be_called,
    )

    assert not report.ok
    assert "credential" in report.render()
    assert "not configured" in report.render()


def test_provider_smoke_runs_provider_task_and_writes_trace(tmp_path, monkeypatch):
    _write_base_files(tmp_path)
    profile = _write_openai_profile(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_runner(goal, config_path=None, trace_path=None, profile_path=None):
        assert goal == DEFAULT_PROVIDER_SMOKE_GOAL
        assert config_path == "config/agent-harness.yaml"
        assert profile_path == str(profile)
        trace = Path(trace_path)
        trace.parent.mkdir(parents=True, exist_ok=True)
        trace.write_text('{"step":1,"permission_verdict":"allow"}\n', encoding="utf-8")
        return RunResult(answer="provider ok", halt_reason="done", steps=1, trace_path=trace_path)

    report = run_provider_smoke(
        "config/agent-harness.yaml",
        str(profile),
        credential_manager=FakeCredentialManager("private-test-token"),
        runner=fake_runner,
    )

    rendered = report.render()
    assert report.ok
    assert "configured; secret not displayed" in rendered
    assert "private-test-token" not in rendered
    assert "trace" in rendered


def test_cli_smoke_provider_command_prints_preflight_failure(tmp_path, monkeypatch, capsys):
    _write_base_files(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["smoke", "provider", "--config", "config/agent-harness.yaml"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "agent-harness provider smoke" in captured.out
    assert "provider" in captured.out


def _runner_should_not_be_called(*args, **kwargs):
    raise AssertionError("runner should not be called")