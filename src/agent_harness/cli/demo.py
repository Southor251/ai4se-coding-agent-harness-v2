from agent_harness.demos import (
    run_feedback_demo,
    run_guardrail_demo,
    run_hitl_write_demo,
    run_scope_demo,
)


def run_all_demos() -> dict[str, dict]:
    return {
        "guardrail": run_guardrail_demo(),
        "feedback": run_feedback_demo(),
        "hitl_write": run_hitl_write_demo(),
        "scope": run_scope_demo(),
    }


def add_demo_parser(subparsers):
    parser = subparsers.add_parser("demo", help="run deterministic mechanism demos")
    parser.set_defaults(handler=_demo)


def _demo(args) -> int:
    for name, result in run_all_demos().items():
        print(f"{name}: {result}")
    return 0
