# Final Project Status

## Status

This repository is a local, testable Coding Agent Harness for the AI4SE final project. The current delivery target is no longer a broad IDE clone; it is a governed harness kernel with clear user-facing entry points, deterministic mechanism demos, and a documented path for real OpenAI-compatible provider setup.

The safe default runtime uses `mock`. Real API-backed execution is opt-in through a local profile plus the credential manager; API keys must not be committed or written into YAML.

## Final Verification Command

Run this before submission and record the observed output in `AGENT_LOG.md`:

```bash
python scripts/verify_delivery.py
```

Expected checks:

- full `pytest` suite
- `ruff` over `src/`, `tests/`, and `demo/`
- `agent-harness doctor --profile config/personal-harness.yaml`
- safe CLI run smoke
- HITL list smoke
- deterministic HITL write demo
- high-confidence secret/marker scan

Optional distribution check:

```bash
docker build -t ai4se-agent-harness .
```

## Implemented Capabilities

### Harness Kernel

- Self-owned agent loop: context assembly, LLM call, JSON action parsing, governance, tool dispatch, feedback injection, trace recording, and halt handling.
- Mockable LLM abstraction with deterministic `MockLLM`.
- Strict JSON action protocol with `call_tool`, `take_note`, `done.answer`, and observable invalid-action recovery.
- OpenAI-compatible provider configuration for `model`, `base_url`, and `temperature`.

### Tools

Default governed runtime tools:

- `read_file`
- `read_many`
- `list_files`
- `search_text`
- `git_diff`
- `write_file`
- `replace_once`
- `edit_file`
- `run_test`

`run_shell` is intentionally not registered in the default governed runtime.

### Governance and HITL

- `ScopeGuard` checks workspace boundaries and sensitive paths.
- Permission rules support `allow`, `ask`, and `deny`.
- Ask-mode actions create persistent HITL requests in `.harness/hitl/requests.json`.
- CLI and Web support list, approve, deny, and approve-plus-continue flows.
- Deterministic HITL write demo proves that a write action is not executed before approval and still passes scope enforcement after approval.

### Feedback and Trace

- Feedback sensor classifies tool results and injects structured feedback into the loop.
- JSONL trace store records step-level execution details.
- Web Theater can select trace history, summarize runs, inspect steps, and operate HITL requests.

### User-Facing Commands

Core commands:

```bash
agent-harness doctor --profile config/personal-harness.yaml
agent-harness run "say done" --profile config/personal-harness.yaml
agent-harness smoke provider --profile config/local-openai.yaml
agent-harness hitl list --store .harness/hitl/requests.json
agent-harness hitl approve <request_id> --continue --profile config/personal-harness.yaml
agent-harness demo
streamlit run src/agent_harness/web/theater.py
```

### Distribution

- Editable Python package install through `pyproject.toml`.
- Docker build path through `Dockerfile`.
- GitHub Actions runs unit/lint checks and Docker build smoke.

## User-Specific Setup Still Required

Before using a real provider:

1. Create a local profile such as `config/local-openai.yaml`.
2. Set `llm.provider: openai`.
3. Set the desired `model` and `base_url`.
4. Store the key with `agent-harness credentials update`; do not write it into YAML or Git.
5. Run `agent-harness doctor --profile config/local-openai.yaml`.
6. Run `agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl`.

## Safety Boundary

This project provides harness-level governance, not an operating-system sandbox. It should be run against a chosen workspace directory with conservative permission rules. The default runtime intentionally omits shell execution. Real projects that need shell access should add explicit, narrow permission rules and preferably run the harness inside an external sandbox such as a container or VM.
