from pathlib import Path
from dataclasses import asdict, is_dataclass
from typing import Any

from agent_harness.trace.store import TraceStore


def load_trace_for_display(path: str | Path) -> list[dict]:
    rows = []
    for record in TraceStore.load(path):
        action = record.get("llm_action") or {}
        feedback = record.get("feedback") or {}
        tool_result = record.get("tool_result") or {}
        rows.append(
            {
                "step": record.get("step"),
                "llm": record.get("llm_text", ""),
                "action": action.get("type", ""),
                "tool": action.get("tool") or "",
                "permission": record.get("permission_verdict", ""),
                "hitl_status": record.get("hitl_status") or "",
                "tool_success": tool_result.get("success", "") if isinstance(tool_result, dict) else "",
                "feedback": feedback.get("category", "") if isinstance(feedback, dict) else "",
            }
        )
    return rows


def summarize_trace(records: list[Any]) -> dict:
    normalized = [_to_dict(record) for record in records]
    return {
        "steps": len(normalized),
        "tool_calls": sum(
            1 for record in normalized if (record.get("llm_action") or {}).get("type") == "call_tool"
        ),
        "denials": sum(1 for record in normalized if record.get("permission_verdict") == "deny"),
        "hitl_pending": sum(1 for record in normalized if record.get("hitl_status") == "pending"),
        "feedback_events": sum(1 for record in normalized if record.get("feedback")),
    }


def _to_dict(record: Any) -> dict:
    if is_dataclass(record):
        return asdict(record)
    return record


def main(path: str = ".harness/runs/latest.jsonl"):
    import streamlit as st

    from agent_harness.web.services import (
        DEFAULT_CONFIG_PATH,
        DEFAULT_HITL_STORE_PATH,
        DEFAULT_PROFILE_PATH,
        DEFAULT_TRACE_DIR,
        approve_and_continue_hitl_request,
        approve_hitl_request,
        deny_hitl_request,
        list_hitl_requests,
        list_trace_runs,
        run_task,
        runtime_overview,
    )

    st.title("Agent Loop Theater")

    with st.sidebar:
        goal = st.text_area("Goal", value="say done")
        config_path = st.text_input("Config path", value=DEFAULT_CONFIG_PATH)
        profile_path = st.text_input("Profile path", value=DEFAULT_PROFILE_PATH)
        trace_path = st.text_input("Trace path", value=path)
        trace_runs = list_trace_runs(DEFAULT_TRACE_DIR)
        if trace_runs:
            selected_trace = st.selectbox("Trace history", trace_runs, format_func=lambda row: row["name"])
            if selected_trace:
                trace_path = selected_trace["path"]
        hitl_store_path = st.text_input("HITL store", value=DEFAULT_HITL_STORE_PATH)

        st.subheader("Runtime status")
        overview = runtime_overview(
            config_path=config_path,
            profile_path=profile_path or None,
            trace_path=trace_path,
            hitl_store_path=hitl_store_path,
        )
        status_cols = st.columns(2)
        status_cols[0].metric("Provider", overview["provider"])
        status_cols[1].metric("Pending HITL", overview["hitl"]["pending"])
        st.caption(
            f"Workspace: `{overview['workspace_root']}` · Trace exists: {overview['trace_exists']} · "
            f"run_shell registered: {overview['tools']['run_shell_registered']}"
        )
        with st.expander("Runtime details"):
            st.write(overview)

        if st.button("Run"):
            result = run_task(
                goal,
                config_path=config_path,
                profile_path=profile_path or None,
                trace_path=trace_path,
            )
            st.session_state["run_result"] = result

    result = st.session_state.get("run_result")
    if result:
        st.subheader("Run")
        st.write(
            {
                "answer": result.answer,
                "halt_reason": result.halt_reason,
                "steps": result.steps,
                "trace_path": result.trace_path,
            }
        )

    st.subheader("Trace")
    rows = load_trace_for_display(trace_path)
    if not rows:
        st.info("No trace records found.")
    else:
        summary = summarize_trace(TraceStore.load(trace_path))
        st.write(summary)
        selected = st.slider("Step", 1, len(rows), 1)
        row = rows[selected - 1]
        st.subheader(f"Step {row['step']}")
        st.markdown(f"**LLM decision:** {row['llm']}")
        st.markdown(f"**Action:** {row['action']}")
        if row["tool"]:
            st.markdown(f"**Tool:** {row['tool']}")
        st.markdown(f"**Permission:** {row['permission']}")
        if row["hitl_status"]:
            st.markdown(f"**HITL:** {row['hitl_status']}")
        if row["tool_success"] != "":
            st.markdown(f"**Tool success:** {row['tool_success']}")
        if row["feedback"]:
            st.markdown(f"**Feedback:** {row['feedback']}")

    st.subheader("HITL")
    requests = list_hitl_requests(hitl_store_path)
    if requests:
        st.dataframe(requests)
    else:
        st.info("No HITL requests found.")
    request_id = st.text_input("Request id")
    approve_col, continue_col, deny_col = st.columns(3)
    with approve_col:
        if st.button("Approve") and request_id:
            approval = approve_hitl_request(
                request_id,
                config_path=config_path,
                profile_path=profile_path or None,
                store_path=hitl_store_path,
            )
            st.write({"success": approval.success, "output": approval.output, "error": approval.error})
    with continue_col:
        if st.button("Approve + Continue") and request_id:
            continued = approve_and_continue_hitl_request(
                request_id,
                config_path=config_path,
                profile_path=profile_path or None,
                store_path=hitl_store_path,
            )
            st.session_state["run_result"] = continued
            st.write(
                {
                    "answer": continued.answer,
                    "halt_reason": continued.halt_reason,
                    "steps": continued.steps,
                }
            )
    with deny_col:
        if st.button("Deny") and request_id:
            denied = deny_hitl_request(request_id, hitl_store_path)
            st.write({"id": denied.id, "status": denied.status})


if __name__ == "__main__":
    main()
