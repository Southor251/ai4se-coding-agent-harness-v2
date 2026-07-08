from pathlib import Path

from agent_harness.cli.run import run_goal
from agent_harness.config.loader import load_config_with_profile
from agent_harness.governance.hitl import HITLManager
from agent_harness.hitl.resume import approve_and_execute, approve_execute_and_continue
from agent_harness.hitl.store import HITLStore
from agent_harness.models import HITLRequest
from agent_harness.runtime.factory import build_harness
from agent_harness.runtime.result import RunResult
from agent_harness.tools.base import ToolResult
from agent_harness.trace.store import TraceStore
from agent_harness.web.theater import summarize_trace


DEFAULT_CONFIG_PATH = "config/agent-harness.yaml"
DEFAULT_PROFILE_PATH = "config/personal-harness.yaml"
DEFAULT_TRACE_PATH = ".harness/runs/latest.jsonl"
DEFAULT_TRACE_DIR = ".harness/runs"
DEFAULT_HITL_STORE_PATH = ".harness/hitl/requests.json"


def run_task(
    goal: str,
    config_path: str = DEFAULT_CONFIG_PATH,
    profile_path: str | None = None,
    trace_path: str = DEFAULT_TRACE_PATH,
) -> RunResult:
    return run_goal(goal, config_path=config_path, profile_path=profile_path, trace_path=trace_path)


def trace_summary(trace_path: str = DEFAULT_TRACE_PATH) -> dict:
    return summarize_trace(TraceStore.load(trace_path))


def list_trace_runs(trace_dir: str = DEFAULT_TRACE_DIR) -> list[dict]:
    root = Path(trace_dir)
    if not root.exists():
        return []
    rows = []
    for path in sorted(root.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
        rows.append(
            {
                "name": path.name,
                "path": str(path),
                "updated_at": path.stat().st_mtime,
                "summary": trace_summary(str(path)),
            }
        )
    return rows


def list_hitl_requests(store_path: str = DEFAULT_HITL_STORE_PATH) -> list[dict]:
    rows = []
    for request in HITLStore(store_path).load():
        rows.append(_hitl_request_row(request))
    return rows


def hitl_summary(store_path: str = DEFAULT_HITL_STORE_PATH) -> dict:
    requests = HITLStore(store_path).load()
    return {
        "total": len(requests),
        "pending": sum(1 for request in requests if request.status == "pending"),
        "approved": sum(1 for request in requests if request.status == "approved"),
        "denied": sum(1 for request in requests if request.status == "denied"),
        "timed_out": sum(1 for request in requests if request.status == "timed_out"),
    }


def runtime_overview(
    config_path: str = DEFAULT_CONFIG_PATH,
    profile_path: str | None = DEFAULT_PROFILE_PATH,
    trace_path: str = DEFAULT_TRACE_PATH,
    hitl_store_path: str = DEFAULT_HITL_STORE_PATH,
) -> dict:
    """Return UI-safe runtime metadata for the Web theater sidebar.

    The overview intentionally reports only credential-independent configuration and
    filesystem state. It never reads or displays API key material.
    """
    config = load_config_with_profile(config_path, profile_path or None)
    trace = Path(trace_path)
    hitl = hitl_summary(hitl_store_path)
    harness = build_harness(config, trace_path=None, hitl_store_path=None)
    tool_names = sorted(tool.name for tool in harness.tools.list()) if harness.tools else []
    return {
        "config_path": str(config_path),
        "profile_path": str(profile_path or ""),
        "workspace_root": config.workspace_root,
        "provider": str(config.llm.get("provider", "mock")),
        "model": str(config.llm.get("model", "")),
        "base_url_configured": bool(config.llm.get("base_url")),
        "memory_enabled": bool(config.memory.get("enabled", False)),
        "permission_rules": len(config.permission.get("rules", [])),
        "trace_path": str(trace_path),
        "trace_exists": trace.exists(),
        "trace_summary": trace_summary(trace_path) if trace.exists() else summarize_trace([]),
        "hitl_store_path": str(hitl_store_path),
        "hitl": hitl,
        "tools": {
            "count": len(tool_names),
            "names": tool_names,
            "run_shell_registered": "run_shell" in tool_names,
        },
    }


def approve_hitl_request(
    request_id: str,
    config_path: str = DEFAULT_CONFIG_PATH,
    profile_path: str | None = None,
    store_path: str = DEFAULT_HITL_STORE_PATH,
) -> ToolResult:
    config = load_config_with_profile(config_path, profile_path)
    harness = build_harness(config, hitl_store_path=store_path)
    return approve_and_execute(harness, request_id)


def approve_and_continue_hitl_request(
    request_id: str,
    config_path: str = DEFAULT_CONFIG_PATH,
    profile_path: str | None = None,
    store_path: str = DEFAULT_HITL_STORE_PATH,
) -> RunResult:
    config = load_config_with_profile(config_path, profile_path)
    harness = build_harness(config, hitl_store_path=store_path)
    return approve_execute_and_continue(harness, request_id)


def deny_hitl_request(request_id: str, store_path: str = DEFAULT_HITL_STORE_PATH) -> HITLRequest:
    manager = HITLManager(store=HITLStore(store_path))
    request = manager.find(request_id)
    if request is None:
        raise ValueError(f"HITL request not found: {request_id}")
    if request.status != "pending":
        raise ValueError(f"HITL request is not pending: {request_id}")
    denied = manager.deny(request_id)
    if denied is None:
        raise ValueError(f"HITL request not found: {request_id}")
    return denied


def _hitl_request_row(request: HITLRequest) -> dict:
    return {
        "id": request.id,
        "status": request.status,
        "tool": request.action.tool or "",
        "reason": request.reason,
        "created_at": request.created_at,
        "resolved_at": request.resolved_at or "",
        "decided_by": request.decided_by or "",
    }
