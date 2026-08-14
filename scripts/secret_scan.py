import argparse
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PATHS = [
    "src",
    "tests",
    "demo",
    "scripts",
    "config",
    ".github",
    "README.md",
    "SPEC.md",
    "PLAN.md",
    "SPEC_PROCESS.md",
    "AGENT_LOG.md",
    "REFLECTION.md",
    "Dockerfile",
    ".dockerignore",
    ".gitignore",
    ".gitlab-ci.yml",
    "Makefile",
    "pyproject.toml",
    "submission.jsonc",
    "docs/personal_setup.md",
    "docs/final_status.md",
]

IGNORED_FILES = {
    "scripts/secret_scan.py",
    "tests/test_secret_scan.py",
}

SECRET_PATTERNS = [
    ("private_key", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
    ("openai_secret", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("todo_marker", re.compile(r"\b(TODO|TBD|FIXME)\b")),
]


@dataclass(frozen=True)
class Finding:
    path: str
    kind: str
    line_number: int
    line: str


def format_finding(finding: Finding) -> str:
    rendered = f"{finding.path}:{finding.line_number}:{finding.kind}:{finding.line}"
    return rendered.encode("ascii", "backslashreplace").decode("ascii")


def scan_text(path: str, text: str) -> list[Finding]:
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path=path, kind=kind, line_number=line_number, line=line.strip()))
    return findings


def scan_paths(paths: list[str]) -> list[Finding]:
    findings = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        files = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
        for file_path in files:
            if file_path.as_posix() in IGNORED_FILES:
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            findings.extend(scan_text(str(file_path), text))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS)
    args = parser.parse_args(argv)
    findings = scan_paths(args.paths)
    for finding in findings:
        print(format_finding(finding))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
