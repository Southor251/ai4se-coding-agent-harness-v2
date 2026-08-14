import sys
from dataclasses import dataclass
from pathlib import Path

from agent_harness.config.loader import load_config_with_profile
from agent_harness.credentials.manager import CredentialManager
from agent_harness.runtime.factory import build_harness


DEFAULT_CONFIG_PATH = "config/agent-harness.yaml"
DEFAULT_PROFILE_PATH = "config/personal-harness.yaml"
DEFAULT_TRACE_PATH = ".harness/runs/latest.jsonl"
DEFAULT_HITL_STORE_PATH = ".harness/hitl/requests.json"
MIN_PYTHON_MAJOR = 3
MIN_PYTHON_MINOR = 12


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def ok(self) -> bool:
        return all(check.status != "fail" for check in self.checks)

    def render(self) -> str:
        lines = ["agent-harness doctor"]
        for check in self.checks:
            lines.append(f"[{check.status.upper()}] {check.name}: {check.detail}")
        lines.append(f"result={'ok' if self.ok else 'failed'}")
        return "\n".join(lines)


def run_doctor(
    config_path: str | None = None,
    profile_path: str | None = None,
    trace_path: str = DEFAULT_TRACE_PATH,
    hitl_store_path: str = DEFAULT_HITL_STORE_PATH,
    credential_manager=None,
) -> DoctorReport:
    config_file = config_path or DEFAULT_CONFIG_PATH
    config = load_config_with_profile(config_file, profile_path)
    manager = credential_manager or CredentialManager()
    checks: list[DoctorCheck] = []

    checks.append(_check_python_version())
    checks.append(_check_workspace_root(config.workspace_root))
    checks.extend(_check_llm_config(config))
    checks.append(_check_credential(manager))
    checks.append(_check_env_gitignore())
    checks.append(_check_permission_rules(config))
    checks.append(_check_trace_path(trace_path))
    checks.append(_check_hitl_store_path(hitl_store_path))
    checks.append(_check_tool_safety(config))

    return DoctorReport(checks)


def _check_python_version() -> DoctorCheck:
    major, minor = sys.version_info[:2]
    if major > MIN_PYTHON_MAJOR or (major == MIN_PYTHON_MAJOR and minor >= MIN_PYTHON_MINOR):
        return DoctorCheck("python", "ok", f"{major}.{minor}")
    return DoctorCheck("python", "fail", f"{major}.{minor} < {MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR}")


def _check_workspace_root(workspace_root: str) -> DoctorCheck:
    root = Path(workspace_root)
    if root.exists():
        return DoctorCheck("workspace_root", "ok", str(root.resolve()))
    return DoctorCheck("workspace_root", "warn", f"{workspace_root} does not exist")


def _check_llm_config(config) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    provider = str(config.llm.get("provider", "mock"))
    checks.append(DoctorCheck("provider", "ok", provider))
    model = config.llm.get("model")
    if model:
        checks.append(DoctorCheck("model", "ok", str(model)))
    else:
        checks.append(DoctorCheck("model", "warn", "not set"))
    base_url = config.llm.get("base_url")
    if base_url:
        checks.append(DoctorCheck("base_url", "ok", str(base_url)))
    else:
        checks.append(DoctorCheck("base_url", "warn", "empty; SDK default endpoint is used"))
    return checks


def _check_credential(manager) -> DoctorCheck:
    try:
        configured = bool(manager.get())
    except Exception:
        return DoctorCheck("credential", "fail", "lookup failed; inspect secure local logs")
    if configured:
        return DoctorCheck("credential", "ok", "configured; secret not displayed")
    return DoctorCheck("credential", "warn", "not configured")


def _check_env_gitignore() -> DoctorCheck:
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        return DoctorCheck("env_gitignore", "warn", ".gitignore not found")
    content = gitignore.read_text(encoding="utf-8")
    if ".env" in content:
        return DoctorCheck("env_gitignore", "ok", ".env is ignored")
    return DoctorCheck("env_gitignore", "fail", ".env is not ignored")


def _check_permission_rules(config) -> DoctorCheck:
    rules = config.permission.get("rules", [])
    return DoctorCheck("permission_rules", "ok", f"{len(rules)} rule(s)")


def _check_trace_path(trace_path: str) -> DoctorCheck:
    trace = Path(trace_path)
    if trace.exists():
        return DoctorCheck("trace_path", "ok", str(trace))
    return DoctorCheck("trace_path", "warn", f"{trace_path} not yet created")


def _check_hitl_store_path(hitl_store_path: str) -> DoctorCheck:
    store = Path(hitl_store_path)
    if store.exists():
        return DoctorCheck("hitl_store", "ok", str(store))
    return DoctorCheck("hitl_store", "warn", f"{hitl_store_path} not yet created")


def _check_tool_safety(config) -> DoctorCheck:
    harness = build_harness(config, trace_path=None, hitl_store_path=None)
    tool_names = [tool.name for tool in harness.tools.list()] if harness.tools else []
    if "run_shell" in tool_names:
        return DoctorCheck("tool_safety", "warn", "run_shell is registered")
    return DoctorCheck("tool_safety", "ok", "run_shell is not registered")


def add_doctor_parser(subparsers):
    parser = subparsers.add_parser("doctor", help="run local diagnostic checks")
    parser.add_argument("--config", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--trace", default=DEFAULT_TRACE_PATH)
    parser.add_argument("--hitl-store", default=DEFAULT_HITL_STORE_PATH)
    parser.set_defaults(handler=_doctor)


def _doctor(args) -> int:
    report = run_doctor(
        config_path=args.config,
        profile_path=args.profile,
        trace_path=args.trace,
        hitl_store_path=args.hitl_store,
    )
    print(report.render())
    return 0 if report.ok else 1

