from agent_harness.cli.main import main
from agent_harness.cli.run import run_goal


def test_run_goal_returns_structured_result():
    result = run_goal("say done", trace_path=".harness/runs/test-run.jsonl")

    assert result.answer == "done"
    assert result.halt_reason == "done"
    assert result.steps == 1
    assert result.trace_path == ".harness/runs/test-run.jsonl"


def test_run_command_executes_goal(capsys):
    exit_code = main(["run", "say done", "--trace", ".harness/runs/test-cli.jsonl"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "done" in captured.out
    assert "trace=.harness/runs/test-cli.jsonl" in captured.out


def test_run_command_with_openai_config_without_key_exits_safely(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr(
        "agent_harness.runtime.factory.CredentialManager",
        lambda: type("EmptyCredentialManager", (), {"get": lambda self: None})(),
    )
    config_path = tmp_path / "agent-harness.yaml"
    config_path.write_text(
        "\n".join(
            [
                "max_steps: 3",
                "llm:",
                "  provider: openai",
                "  model: custom-model",
                "  temperature: 0.2",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["run", "say done", "--config", str(config_path), "--trace", str(tmp_path / "trace.jsonl")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "API key not configured" in captured.out


def test_run_goal_writes_trace_file(tmp_path):
    trace_path = tmp_path / "trace.jsonl"

    result = run_goal("say done", trace_path=str(trace_path))

    assert result.trace_path == str(trace_path)
    assert trace_path.exists()
    assert "done" in trace_path.read_text(encoding="utf-8")


def test_run_command_accepts_profile(tmp_path, capsys):
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text("max_steps: 2\nmemory:\n  enabled: true\n", encoding="utf-8")

    exit_code = main(
        [
            "run",
            "say done",
            "--profile",
            str(profile_path),
            "--trace",
            str(tmp_path / "trace.jsonl"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "done" in captured.out
