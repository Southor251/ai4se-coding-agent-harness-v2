# Final Project Status

## Local release evidence — 2026-08-14

The repository has a locally verified, deterministic Coding Agent Harness kernel. The latest normal verification ran from this checkout after re-binding the editable installation to `C:\Users\hp\Desktop\ai4se-coding-agent-harness\src`:

```powershell
.\.venv\Scripts\python.exe scripts\verify_delivery.py
```

Observed result:

- `175 passed`
- Ruff: `All checks passed!`
- Mock CLI run: passed
- HITL list: passed
- Secret and placeholder scan: passed

The three deterministic mechanism demonstrations also remain available under `demo/`: guardrail denial, feedback healing, and scope denial. They use `MockLLM` and do not need a network connection or a real credential.

## Delivery artifacts now aligned

- `Dockerfile` exposes port 8501 and starts the Streamlit WebUI.
- GitHub Actions has `unit-test` and `container-build` jobs; `.gitlab-ci.yml` retains the required `unit-test` job.
- `credentials update` uses hidden input; `credentials clear` requires confirmation by default. Non-empty runtime `OPENAI_API_KEY` is supported for deployment secret injection, while an explicitly empty adapter key does not fall back to the environment.\n- Provider, credential-backend, and runtime-assembly errors shown to users are redacted rather than emitted verbatim.
- The secret scanner prints non-ASCII findings safely on Windows consoles.

## External submission gates still requiring owner action

These are course requirements, not implementation claims. They are intentionally not fabricated in this repository:

1. A real public HTTPS URL for the deployed WebUI, plus a verified latest remote CI pass.
2. The student's own 1500–2500 word/character reflection in `REFLECTION.md`.
3. Real identity fields and the actual deployment/release URL in `submission.jsonc`.
4. The course-required cold-start exercise with a different agent/session, documented honestly in `SPEC_PROCESS.md`.

## Safety boundary

This project supplies harness-level controls, not an operating-system sandbox. Run real-provider tasks only in a deliberately selected workspace with conservative permission rules. The default runtime omits `run_shell`.
