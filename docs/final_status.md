# Final Project Status

## Verified repository evidence — 2026-08-14

From this checkout, `python scripts/verify_delivery.py` completed successfully with `185 passed`, Ruff reporting `All checks passed!`, a mock CLI run, a HITL-list smoke check, and the submission-scope secret/placeholder scan. GitHub Actions for merged main commit 99cfa9e passed both unit-test and container-build; the container job builds the image, starts the Streamlit WebUI, and performs an HTTP probe on port 8501.

The three deterministic mechanism demonstrations remain under `demo/`: governance denial, feedback healing, and scope denial. They use `MockLLM` and do not require network access or a real credential.

## Submission artifacts controlled by the repository

- `Dockerfile` starts the Streamlit WebUI on port 8501.
- Root `requirements.txt` installs this project for Streamlit Community Cloud, allowing the entrypoint `src/agent_harness/web/theater.py` to import the `src` package layout.
- GitHub Actions has `unit-test` and `container-build`; `.gitlab-ci.yml` retains the course-required `unit-test` job.
- `submission.jsonc` contains the supplied student identity, public GitHub repository URL, and the verified public Release URL v1.0.0-course-submission. It truthfully remains `is_deployed: false` until an actual public WebUI URL exists.
- Credentials use hidden input and safe precedence. User-visible provider, credential-backend, and runtime-assembly failures are redacted. The scanner produces Windows-console-safe output.

## Remaining evidence gates not representable by repository edits

1. A real public HTTPS WebUI URL, verified from a non-admin browser, then recorded in `submission.jsonc` with `is_deployed: true`.
2. A genuine cold-start exercise performed by a different agent type or independent session, with original questions, minimal change, diff, and verification recorded in `SPEC_PROCESS.md`.
3. The student's own 1500–2500 word/character reflection in `REFLECTION.md`.

The exact deployment and cold-start handoff is in `docs/final_submission_external_gates.md`. None of these gates should be replaced with a repository URL, a mocked screenshot, or an invented transcript.

## Safety boundary

This project supplies harness-level controls, not an operating-system sandbox. Run real-provider tasks only in a deliberately selected workspace with conservative permission rules. The default runtime omits `run_shell`.
