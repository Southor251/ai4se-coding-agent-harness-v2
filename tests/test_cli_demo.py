from agent_harness.cli.demo import run_all_demos
from agent_harness.cli.main import main


def test_run_all_demos_returns_three_results():
    result = run_all_demos()

    assert set(result) == {"guardrail", "feedback", "hitl_write", "scope"}
    assert result["guardrail"]["status"] == "denied"
    assert result["feedback"]["status"] == "healed"
    assert result["hitl_write"]["status"] == "approved_and_written"
    assert result["scope"]["status"] == "scope_denied"


def test_demo_command_prints_results(capsys):
    exit_code = main(["demo"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "feedback" in captured.out
    assert "healed" in captured.out
