from pathlib import Path

from agent_harness.agent.harness import Harness
from agent_harness.agent.loop import agent_loop
from agent_harness.governance.hitl import HITLManager
from agent_harness.governance.permission import PermissionPolicy
from agent_harness.governance.scope import ScopeGuard
from agent_harness.hitl.resume import approve_execute_and_continue
from agent_harness.hitl.store import HITLStore
from agent_harness.llm.interface import LLMResponse
from agent_harness.llm.mock import MockLLM
from agent_harness.models import AgentAction, PermissionRule
from agent_harness.tools.builtin.write_file import WriteFileTool
from agent_harness.tools.registry import ToolRegistry

DEMO_CONTENT = "hello from hitl demo\n"


def _tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(WriteFileTool())
    return registry


def _permission_policy() -> PermissionPolicy:
    permission = PermissionPolicy()
    permission.add_rule(PermissionRule("ask before demo writes", ".*", "ask", "path"))
    return permission


def _hitl_manager(hitl_store_path: str | Path | None) -> HITLManager:
    if hitl_store_path:
        return HITLManager(store=HITLStore(hitl_store_path))
    return HITLManager()


def run_demo(
    workspace_root: str | Path = ".harness/demo_workspace",
    hitl_store_path: str | Path | None = None,
) -> dict:
    """Run a deterministic HITL write workflow.

    The first harness run requests a write action under an ``ask`` rule and exits before the
    file is written. A second harness instance approves the persisted request, executes the
    tool under ScopeGuard, and resumes the loop with a deterministic ``done`` action.
    """
    workspace = Path(workspace_root).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    target = workspace / "hello.txt"
    if target.exists():
        target.unlink()

    first_harness = Harness(
        llm=MockLLM(
            [
                LLMResponse(
                    "request write",
                    AgentAction(
                        type="call_tool",
                        tool="write_file",
                        args={"path": str(target), "content": DEMO_CONTENT},
                    ),
                )
            ]
        ),
        tools=_tool_registry(),
        permission=_permission_policy(),
        scope=ScopeGuard(str(workspace)),
        hitl=_hitl_manager(hitl_store_path),
        max_steps=1,
    )
    agent_loop("create a HITL-protected demo file", first_harness)

    pending_requests = [
        request
        for request in first_harness.hitl.requests
        if request.status == "pending" and (request.action.args or {}).get("path") == str(target)
    ]
    if not pending_requests:
        return {
            "status": "failed",
            "reason": "no pending HITL request was created",
            "file_written": target.exists(),
        }

    request_id = pending_requests[-1].id
    existed_before_approval = target.exists()
    approval_manager = _hitl_manager(hitl_store_path) if hitl_store_path else first_harness.hitl
    approval_harness = Harness(
        llm=MockLLM(
            [
                LLMResponse(
                    "done",
                    AgentAction(type="done", answer="hitl write complete"),
                )
            ]
        ),
        tools=_tool_registry(),
        permission=_permission_policy(),
        scope=ScopeGuard(str(workspace)),
        hitl=approval_manager,
        max_steps=5,
    )

    result = approve_execute_and_continue(approval_harness, request_id)
    approved_request = approval_manager.find(request_id)
    content = target.read_text(encoding="utf-8") if target.exists() else ""
    success = (
        approved_request is not None
        and approved_request.status == "approved"
        and not existed_before_approval
        and target.exists()
        and content == DEMO_CONTENT
        and result.halt_reason == "done"
    )

    return {
        "status": "approved_and_written" if success else "failed",
        "request_id": request_id,
        "request_status": approved_request.status if approved_request else "missing",
        "file_written": target.exists(),
        "file_existed_before_approval": existed_before_approval,
        "target_path": str(target),
        "halt_reason": result.halt_reason,
        "steps": result.steps,
    }
