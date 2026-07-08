import argparse
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]


def build_checks() -> list[Check]:
    return [
        Check("pytest", [sys.executable, "-m", "pytest", "-q"]),
        Check("ruff", [sys.executable, "-m", "ruff", "check", "src/", "tests/", "demo/"]),
        Check(
            "doctor",
            [
                sys.executable,
                "-m",
                "agent_harness.cli.main",
                "doctor",
                "--profile",
                "config/personal-harness.yaml",
            ],
        ),
        Check(
            "cli_run",
            [
                sys.executable,
                "-m",
                "agent_harness.cli.main",
                "run",
                "say done",
                "--profile",
                "config/personal-harness.yaml",
                "--trace",
                ".harness/runs/latest.jsonl",
            ],
        ),
        Check(
            "hitl_list",
            [
                sys.executable,
                "-m",
                "agent_harness.cli.main",
                "hitl",
                "list",
                "--store",
                ".harness/hitl/requests.json",
            ],
        ),
        Check(
            "hitl_write_demo",
            [
                sys.executable,
                "-m",
                "demo.demo_hitl_write",
            ],
        ),
        Check(
            "secret_scan",
            [
                sys.executable,
                "-m",
                "scripts.secret_scan",
            ],
        ),
    ]


def run_checks(checks: list[Check], dry_run: bool = False) -> int:
    for check in checks:
        print(f"== {check.name}: {' '.join(check.command)}")
        if dry_run:
            continue
        result = subprocess.run(check.command)
        if result.returncode != 0:
            return result.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return run_checks(build_checks(), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
