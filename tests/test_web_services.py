from agent_harness.governance.hitl import HITLManager
from agent_harness.hitl.store import HITLStore
from agent_harness.models import AgentAction
from agent_harness.web.services import (
    approve_and_continue_hitl_request,
    approve_hitl_request,
    deny_hitl_request,
    hitl_summary,
    list_hitl_requests,
    list_trace_runs,
    run_task,
    runtime_overview,
    trace_summary,
)


def test_run_task_returns_result_and_trace(tmp_path):
    trace_path = tmp_path / "trace.jsonl"

    result = run_task("say done", trace_path=str(trace_path))

    assert result.answer == "done"
    assert result.trace_path == str(trace_path)
    assert trace_path.exists()


def test_trace_summary_reads_trace_file(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    run_task("say done", trace_path=str(trace_path))

    summary = trace_summary(str(trace_path))

    assert summary["steps"] == 1


def test_list_trace_runs_returns_jsonl_summaries(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    run_task("say done", trace_path=str(first))
    run_task("say done", trace_path=str(second))

    rows = list_trace_runs(str(tmp_path))

    assert {row["name"] for row in rows} == {"first.jsonl", "second.jsonl"}
    assert all(row["summary"]["steps"] == 1 for row in rows)
    assert all(row["path"].endswith(".jsonl") for row in rows)


def test_list_and_deny_hitl_requests(tmp_path):
    store_path = tmp_path / "requests.json"
    manager = HITLManager(store=HITLStore(store_path))
    request = manager.create_request(AgentAction(type="call_tool", tool="read_file"), "review")

    rows = list_hitl_requests(str(store_path))
    result = deny_hitl_request(request.id, str(store_path))

    assert rows[0]["id"] == request.id
    assert rows[0]["status"] == "pending"
    assert result.status == "denied"
    assert HITLStore(store_path).load()[0].status == "denied"


def test_hitl_summary_counts_statuses(tmp_path):
    store_path = tmp_path / "requests.json"
    manager = HITLManager(store=HITLStore(store_path))
    pending = manager.create_request(AgentAction(type="call_tool", tool="read_file"), "review")
    denied = manager.create_request(AgentAction(type="call_tool", tool="write_file"), "review")
    manager.deny(denied.id)

    summary = hitl_summary(str(store_path))

    assert pending.status == "pending"
    assert summary == {
        "total": 2,
        "pending": 1,
        "approved": 0,
        "denied": 1,
        "timed_out": 0,
    }


def test_runtime_overview_reports_safe_status(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    store_path = tmp_path / "requests.json"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""workspace_root: {tmp_path}
llm:
  provider: mock
permission:
  rules:
    - name: ask writes
      pattern: .*
      verdict: ask
      rule_type: path
memory:
  enabled: true
""",
        encoding="utf-8",
    )
    run_task("say done", config_path=str(config_path), trace_path=str(trace_path))
    manager = HITLManager(store=HITLStore(store_path))
    manager.create_request(AgentAction(type="call_tool", tool="write_file"), "review")

    overview = runtime_overview(
        config_path=str(config_path),
        profile_path=None,
        trace_path=str(trace_path),
        hitl_store_path=str(store_path),
    )

    assert overview["provider"] == "mock"
    assert overview["workspace_root"] == str(tmp_path)
    assert overview["trace_exists"] is True
    assert overview["trace_summary"]["steps"] == 1
    assert overview["hitl"]["pending"] == 1
    assert overview["permission_rules"] == 1
    assert overview["memory_enabled"] is True
    assert overview["tools"]["run_shell_registered"] is False
    assert "run_shell" not in overview["tools"]["names"]


def test_approve_hitl_request_executes_pending_action(tmp_path):
    store_path = tmp_path / "requests.json"
    target = tmp_path / "note.txt"
    manager = HITLManager(store=HITLStore(store_path))
    request = manager.create_request(
        AgentAction(
            type="call_tool",
            tool="write_file",
            args={"path": str(target), "content": "hello"},
        ),
        "review",
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"workspace_root: {tmp_path}\nllm:\n  provider: mock\n", encoding="utf-8")

    result = approve_hitl_request(request.id, config_path=str(config_path), store_path=str(store_path))

    assert result.success is True
    assert target.read_text(encoding="utf-8") == "hello"
    assert HITLStore(store_path).load()[0].status == "approved"


def test_approve_and_continue_hitl_request_resumes_task(tmp_path):
    store_path = tmp_path / "requests.json"
    target = tmp_path / "note.txt"
    manager = HITLManager(store=HITLStore(store_path))
    request = manager.create_request(
        AgentAction(
            type="call_tool",
            tool="write_file",
            args={"path": str(target), "content": "hello"},
        ),
        "review",
        context=[
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "write note"},
        ],
        step=1,
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"workspace_root: {tmp_path}\nllm:\n  provider: mock\n", encoding="utf-8")

    result = approve_and_continue_hitl_request(
        request.id,
        config_path=str(config_path),
        store_path=str(store_path),
    )

    assert result.halt_reason == "done"
    assert result.answer == "done"
    assert target.read_text(encoding="utf-8") == "hello"
    assert HITLStore(store_path).load()[0].status == "approved"
