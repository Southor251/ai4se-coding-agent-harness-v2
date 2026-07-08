# Final Project Submission: AI4SE Coding Agent Harness

## Summary

This submission implements a self-contained coding-agent harness where the LLM is only responsible for the next-step decision, while the harness owns deterministic orchestration, tool dispatch, permission governance, scope checking, HITL approval, feedback, memory, trace logging, configuration, credentials, CLI, demos, and Streamlit Theater.

## What changed in the final hardening phase

- Added `agent-harness doctor` for local runtime diagnostics.
- Added provider smoke command for OpenAI-compatible API configuration without exposing secrets.
- Added deterministic HITL write-flow demo and tests.
- Hardened Streamlit Theater runtime status, trace summary, and HITL visibility.
- Expanded final delivery verification, release verification docs, and Docker build smoke coverage.

## Verification

Run from a clean checkout:

```bash
python -m pip install -e ".[dev]"
python scripts/verify_delivery.py
docker build -t ai4se-agent-harness .
```

Optional real-provider smoke, using a local profile and credential manager only:

```bash
agent-harness credentials update
agent-harness doctor --profile config/local-openai.yaml
agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl
```

## Safety boundaries

- No high-level agent frameworks are used.
- Default runtime does not register `run_shell`.
- Write actions are governed by permission rules and HITL.
- Scope guard still applies after approval.
- Credentials are not stored in committed YAML files and are never printed by doctor/smoke commands.
- This is a harness-level safety system, not an OS sandbox.

## Notes for review

The project is intentionally mechanism-heavy: the permission policy, scope guard, HITL state machine, feedback sensor, trace store, and mock-LLM tests remain verifiable even when the real LLM provider is removed.
