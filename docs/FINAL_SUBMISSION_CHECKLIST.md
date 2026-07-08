# Final Submission Checklist

## Repository

- [ ] Public GitHub repository URL is correct.
- [ ] All final patches are committed and pushed.
- [ ] No local-only changes remain: `git status --short` is empty.
- [ ] No secrets are committed.
- [ ] `.env` remains ignored.
- [ ] `config/local-openai.yaml` is not committed.

## Required files

- [ ] `SPEC.md`
- [ ] `PLAN.md`
- [ ] `SPEC_PROCESS.md`
- [ ] `README.md`
- [ ] `AGENT_LOG.md`
- [ ] `REFLECTION.md`, 1500-2500 words, written personally
- [ ] `.gitlab-ci.yml`
- [ ] `.github/workflows/test.yml`
- [ ] `Dockerfile`
- [ ] `docs/final_status.md`
- [ ] `docs/final_delivery_checklist.md`
- [ ] `docs/release_verification.md`
- [ ] `docs/hitl_walkthrough.md`
- [ ] `docs/web_theater_checklist.md`

## Verification

- [ ] `python scripts/verify_delivery.py` passes.
- [ ] `docker build -t ai4se-agent-harness .` passes.
- [ ] `agent-harness doctor --profile config/personal-harness.yaml` passes.
- [ ] `python -m demo.demo_hitl_write` passes.
- [ ] Web Theater launches locally.
- [ ] Optional real-provider smoke was run with local-only credential storage.

## Course evidence

- [ ] Commit history shows incremental development.
- [ ] Tests cover mock LLM / deterministic harness behavior.
- [ ] HITL, scope, permission, feedback, trace, and memory are implemented as code mechanisms.
- [ ] README explains install, run, Web, Docker, safety boundaries.
- [ ] Final status records latest local and CI verification result.
- [ ] Online WebUI URL is provided if required by instructor.
