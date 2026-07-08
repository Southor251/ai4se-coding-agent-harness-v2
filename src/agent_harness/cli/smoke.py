from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agent_harness.cli.run import run_goal
from agent_harness.config.loader import load_config_with_profile
from agent_harness.credentials.manager import CredentialManager
from agent_harness.runtime.result import RunResult


DEFAULT_CONFIG_PATH = "config/agent-harness.yaml"
DEFAULT_PROVIDER_SMOKE_TRACE = ".harness/runs/provider-smoke.jsonl"
DEFAULT_PROVIDER_SMOKE_GOAL = (
    "Use only read-only project inspection tools. List the workspace files or read README.md, "
    "then finish with a short answer. Do not write files."
)

Runner = Callable[[str, str | None, str | None, str | None], RunResult]


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class SmokeReport:
    checks: list[SmokeCheck]

    @property
    def ok(self) -> bool:
        return all(check.status != "fail" for check in self.checks)

    def render(self) -> str:
        lines = ["agent-harness provider smoke"]
        for check in self.checks:
            lines.append(f"[{check.status.upper()}] {check.name}: {check.detail}")
        lines.append(f"result={'ok' if self.ok else 'failed'}")
        return "\n".join(lines)


def run_provider_smoke(
    config_path: str | None = None,
    profile_path: str | None = None,
    trace_path: str = DEFAULT_PROVIDER_SMOKE_TRACE,
    goal: str = DEFAULT_PROVIDER_SMOKE_GOAL,
    credential_manager=None,
    runner: Runner = run_goal,
) -> SmokeReport:
    config_file = config_path or DEFAULT_CONFIG_PATH
    config = load_config_with_profile(config_file, profile_path)
    manager = credential_manager or CredentialManager()
    checks: list[SmokeCheck] = []

    provider = str(config.llm.get("provider", "mock"))
    if provider != "openai":
        checks.append(
            SmokeCheck(
                "provider",
                "fail",
                f"provider smoke requires llm.provider=openai, got {provider}",
            )
        )
        return SmokeReport(checks)
    checks.append(SmokeCheck("provider", "ok", provider))

    model = config.llm.get("model")
    if model:
        checks.append(SmokeCheck("model", "ok", str(model)))
    else:
        checks.append(SmokeCheck("model", "fail", "llm.model is required"))
        return SmokeReport(checks)

    base_url = config.llm.get("base_url")
    if base_url:
        checks.append(SmokeCheck("base_url", "ok", str(base_url)))
    else:
        checks.append(SmokeCheck("base_url", "warn", "empty; OpenAI SDK default endpoint is used"))

    try:
        configured = bool(manager.get())
    except Exception as exc:
        checks.append(SmokeCheck("credential", "fail", f"credential lookup failed: {exc}"))
        return SmokeReport(checks)
    if not configured:
        checks.append(SmokeCheck("credential", "fail", "not configured"))
        return SmokeReport(checks)
    checks.append(SmokeCheck("credential", "ok", "configured; secret not displayed"))

    trace = Path(trace_path)
    trace.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = runner(goal, config_file, trace_path, profile_path)
    except Exception as exc:
        checks.append(SmokeCheck("run", "fail", f"provider run failed: {exc}"))
        return SmokeReport(checks)

    if result.halt_reason == "done":
        checks.append(SmokeCheck("halt", "ok", f"done after {result.steps} step(s)"))
    else:
        checks.append(
            SmokeCheck(
                "halt",
                "fail",
                f"unexpected halt_reason={result.halt_reason} steps={result.steps}",
            )
        )

    if trace.exists() and trace.stat().st_size > 0:
        checks.append(SmokeCheck("trace", "ok", str(trace)))
    else:
        checks.append(SmokeCheck("trace", "fail", f"trace was not written: {trace}"))

    if result.answer:
        checks.append(SmokeCheck("answer", "ok", "model returned a user-facing answer"))
    else:
        checks.append(SmokeCheck("answer", "warn", "empty answer; inspect trace for raw actions"))

    return SmokeReport(checks)


def add_smoke_parser(subparsers):
    parser = subparsers.add_parser("smoke", help="run guarded smoke checks")
    smoke_subparsers = parser.add_subparsers(dest="smoke_command")

    provider = smoke_subparsers.add_parser(
        "provider",
        help="run a real OpenAI-compatible provider smoke check",
    )
    provider.add_argument("--config", default=None)
    provider.add_argument("--profile", default=None)
    provider.add_argument("--trace", default=DEFAULT_PROVIDER_SMOKE_TRACE)
    provider.add_argument("--goal", default=DEFAULT_PROVIDER_SMOKE_GOAL)
    provider.set_defaults(handler=_provider_smoke)


def _provider_smoke(args) -> int:
    report = run_provider_smoke(args.config, args.profile, args.trace, args.goal)
    print(report.render())
    return 0 if report.ok else 1