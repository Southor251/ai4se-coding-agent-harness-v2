from agent_harness.models import AgentAction, TraceRecord
from agent_harness.models import Feedback, ToolResult
from agent_harness.trace.store import TraceStore
from agent_harness.web.theater import load_trace_for_display, summarize_trace


def test_load_trace_for_display(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    store = TraceStore(trace_path)
    store.record(
        TraceRecord(
            step=1,
            llm_text="done",
            llm_action=AgentAction(type="done"),
            permission_verdict="allow",
        )
    )

    rows = load_trace_for_display(trace_path)

    assert rows == [
        {
            "step": 1,
            "llm": "done",
            "action": "done",
            "tool": "",
            "permission": "allow",
            "hitl_status": "",
            "tool_success": "",
            "feedback": "",
        }
    ]


def test_load_trace_for_display_includes_tool_hitl_and_feedback(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    store = TraceStore(trace_path)
    store.record(
        TraceRecord(
            step=1,
            llm_text="write",
            llm_action=AgentAction(type="call_tool", tool="write_file"),
            permission_verdict="ask",
            hitl_status="pending",
            tool_result=ToolResult(success=True, output="ok"),
            feedback=Feedback(category="success", message="ok", raw="ok"),
        )
    )

    row = load_trace_for_display(trace_path)[0]

    assert row["tool"] == "write_file"
    assert row["hitl_status"] == "pending"
    assert row["tool_success"] is True
    assert row["feedback"] == "success"


def test_summarize_trace_counts_key_events():
    records = [
        {
            "step": 1,
            "llm_action": {"type": "call_tool", "tool": "read_file"},
            "permission_verdict": "allow",
            "feedback": {"category": "success"},
        },
        {
            "step": 2,
            "llm_action": {"type": "call_tool", "tool": "write_file"},
            "permission_verdict": "ask",
            "hitl_status": "pending",
            "feedback": None,
        },
        {
            "step": 3,
            "llm_action": {"type": "call_tool", "tool": "write_file"},
            "permission_verdict": "deny",
            "feedback": None,
        },
        {
            "step": 4,
            "llm_action": {"type": "done"},
            "permission_verdict": "allow",
            "feedback": None,
        },
    ]

    summary = summarize_trace(records)

    assert summary == {
        "steps": 4,
        "tool_calls": 3,
        "denials": 1,
        "hitl_pending": 1,
        "feedback_events": 1,
    }


def test_summarize_trace_accepts_dataclass_records():
    records = [
        TraceRecord(
            step=1,
            llm_text="tool",
            llm_action=AgentAction(type="call_tool", tool="read_file"),
            permission_verdict="allow",
            feedback=Feedback(category="success", message="ok", raw="ok"),
        )
    ]

    summary = summarize_trace(records)

    assert summary["steps"] == 1
    assert summary["tool_calls"] == 1
    assert summary["feedback_events"] == 1
