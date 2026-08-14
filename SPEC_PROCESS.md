# Specification Process

## Initial Problem

The inherited harness already had useful pieces, but it was not ready to deliver. The main gaps were:

- The agent loop did not consistently enforce scope, permission, or human-in-the-loop checks.
- Tool results were not converted into structured feedback for later repair attempts.
- There was no durable trace format for replay or inspection.
- CLI, config, credential, plugin, theater, and documentation surfaces were incomplete.
- Some security test examples used high-risk literals that could interfere with model-side filtering.

## Recovery Decision

The recovery kept the existing repository structure instead of rebuilding from scratch. The design target was a deterministic harness kernel:

1. Receive a goal and construct context.
2. Ask an injected LLM for an action.
3. Validate and govern the action.
4. Execute only approved tools.
5. Convert tool results into feedback.
6. Record a trace entry.
7. Halt with an explicit reason.

This made each mechanism independently testable under `MockLLM`.

## Cold-Start Status

The project can be cold-started from a clean checkout with:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src/ tests/ demo/
```

The Dockerfile also provides a containerized verification path.

## Revision Rationale

- Neutral fixtures preserve security behavior without relying on sensitive command text.
- `python -m pytest` and `python -m ruff` reduce dependency on PATH layout.
- Scope checks use resolved path relationships rather than string prefixes.
- Missing workspace roots are treated as outside scope.
- Sensitive path detection checks path parts so the sensitive directory itself is blocked.
- Unknown tools now produce context feedback and trace records.
- Governed shell calls are denied by default unless a permission policy is present.
- Test success is based on process return code, not textual output.
- Feedback demos now require an actual failed attempt followed by a successful retry.
- HITL approval now persists requests across processes, and both CLI and Web helpers route approvals through the same governed runtime.
- Web UI logic is kept thin; task execution, trace summary, and HITL operations live in `agent_harness.web.services` so they can be unit tested without a browser.
- Tool menus include argument schemas before reaching the OpenAI-compatible provider, reducing malformed real-API actions without expanding permissions.
- Structured `done` actions can include an `answer` field, so API-backed runs have a clean user-facing final response instead of returning raw JSON.
- Fake OpenAI client end-to-end coverage now verifies multi-step API-backed runtime execution through read/write/test tools, trace, feedback, and final answer.
- HITL requests persist resume context and step, enabling approved actions to inject tool results and continue the agent loop.
- Safe read-only browsing tools `list_files` and `search_text` are registered by default without enabling shell execution.
- `read_many` and `git_diff` extend project inspection while still avoiding default shell access.
- `replace_once` provides safer single-match edits than broad replace operations.
- Web HITL approval can now continue saved-context tasks through the shared service layer.
- Web trace history is service-backed and can summarize JSONL runs without depending on Streamlit.
- Delivery verification is now scripted, and personal API setup is documented in `docs/personal_setup.md`.
- High-confidence secret and marker scanning is automated through `scripts.secret_scan`.

## Evidence

The implementation was developed with failing tests first for the behavioral fixes and then verified with the full suite.

Latest observed results:

- `161 passed`
- `All checks passed!`
- CLI smoke for `run` and `hitl list` passed.
- Secret and marker scan produced only expected API-key documentation and fake test-token references.
## Submission-readiness integrity note — 2026-08-14

A normal local verification pass was re-established after discovering that the repository virtual environment had an editable installation pointing at an older checkout. The environment was rebound to this repository before collecting the current `169 passed` evidence. This is local implementation evidence only.

The required cold-start exercise remains incomplete until a different agent type/session is given only `SPEC.md` and `PLAN.md`, implements one or two tasks without the original design conversation, and its questions and resulting document revisions are recorded here. No such exercise is claimed as completed by this note.
