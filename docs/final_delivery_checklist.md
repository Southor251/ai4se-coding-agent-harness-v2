# Final Delivery Checklist

Use this file as the last pre-submission gate.

## 1. Repository Hygiene

- [ ] `git status --short` shows only intended files before commit.
- [ ] No real API key appears in source, docs, logs, traces, terminal screenshots, or Git history.
- [ ] `.env` remains ignored.
- [ ] Local-only files such as `config/local-openai.yaml` are not committed unless they contain no secrets and are clearly marked as examples.

## 2. Required Course Artifacts

- [ ] `SPEC.md` explains problem statement, users, architecture, safety, credential threat model, distribution, and acceptance criteria.
- [ ] `PLAN.md` reflects the implemented slices and final status.
- [ ] `AGENT_LOG.md` records the actual development process, including deviations from the plan.
- [ ] `README.md` explains install, verify, credentials, CLI, Web, Docker, and safety boundaries.
- [ ] `REFLECTION.md` is personally written by the student.
- [ ] `docs/final_status.md` matches the actual repository state.
- [ ] `docs/personal_setup.md` gives a safe real-provider setup path.
- [ ] `docs/hitl_walkthrough.md` explains the HITL write flow.
- [ ] `docs/web_theater_checklist.md` explains Web Theater validation.

## 3. Deterministic Verification

Run:

```bash
python scripts/verify_delivery.py
```

Record the actual output in `AGENT_LOG.md`.

The command should cover:

- pytest
- ruff
- doctor
- safe CLI run
- HITL list
- deterministic HITL write demo
- secret scan

## 4. Distribution Verification

Run:

```bash
docker build -t ai4se-agent-harness .
```

The build must finish without relying on a real API key.

## 5. Real Provider Smoke

This is a local-only manual test. Do not commit the profile if it contains real endpoint details you do not want public.

```bash
agent-harness credentials update
agent-harness doctor --profile config/local-openai.yaml
agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl
```

The smoke command should produce a trace and must not print the secret.

## 6. Demo Script

Run:

```bash
agent-harness demo
python -m demo.demo_hitl_write
streamlit run src/agent_harness/web/theater.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Check that:

- guardrail demo denies the blocked action.
- feedback demo shows a failed attempt followed by recovery.
- scope demo blocks out-of-workspace access.
- HITL write demo writes only after approval.
- Web Theater displays runtime status, trace summary, and HITL controls.

## 7. Submission Bundle

- [ ] Public GitHub/GitLab repository URL is accessible.
- [ ] CI is green.
- [ ] Docker build path is documented.
- [ ] WebUI access path is documented. If no hosted WebUI is deployed, state the local Streamlit command and limitation explicitly.
- [ ] Final commit hash is recorded in `AGENT_LOG.md`.
