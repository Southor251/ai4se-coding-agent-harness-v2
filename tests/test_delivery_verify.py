from pathlib import Path

from scripts.verify_delivery import build_checks


def test_delivery_verify_builds_expected_checks():
    checks = build_checks()
    names = [check.name for check in checks]

    assert names == [
        "pytest",
        "ruff",
        "doctor",
        "cli_run",
        "hitl_list",
        "hitl_write_demo",
        "secret_scan",
    ]
    assert checks[0].command[1:3] == ["-m", "pytest"]
    assert checks[2].command[1:3] == ["-m", "agent_harness.cli.main"]


def test_docker_distribution_starts_the_web_ui():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "EXPOSE 8501" in dockerfile
    assert '"streamlit"' in dockerfile
    assert '"src/agent_harness/web/theater.py"' in dockerfile
    assert '"--server.address=0.0.0.0"' in dockerfile
    assert '"--server.port=8501"' in dockerfile

def test_github_ci_smoke_tests_the_container_web_ui():
    workflow = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "docker run --detach" in workflow
    assert "curl --fail --silent --show-error http://127.0.0.1:8501" in workflow
    assert "docker logs ai4se-agent-harness-ci" in workflow
