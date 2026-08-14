# Final Project Status

## Verified repository evidence — 2026-08-14

From this checkout, `python scripts/verify_delivery.py` completed successfully with `186 passed`, Ruff reporting `All checks passed!`, a mock CLI run, a HITL-list smoke check, and the submission-scope secret/placeholder scan. GitHub Actions for merged main commit 99cfa9e passed both unit-test and container-build; the container job builds the image, starts the Streamlit WebUI, and performs an HTTP probe on port 8501.

The three deterministic mechanism demonstrations remain under `demo/`: governance denial, feedback healing, and scope denial. They use `MockLLM` and do not require network access or a real credential.

## Submission artifacts controlled by the repository

- `Dockerfile` starts the Streamlit WebUI on port 8501.
- Root `requirements.txt` installs this project for Streamlit Community Cloud, allowing the entrypoint `src/agent_harness/web/theater.py` to import the `src` package layout.
- GitHub Actions has `unit-test` and `container-build`; `.gitlab-ci.yml` retains the course-required `unit-test` job.
- `submission.jsonc` contains the supplied student identity, public GitHub repository URL, and the verified public deployment URL https://southor251-ai4se-harness.streamlit.app/. It truthfully records `is_deployed: true`.
- Credentials use hidden input and safe precedence. User-visible provider, credential-backend, and runtime-assembly failures are redacted. The scanner produces Windows-console-safe output.

## Verified public deployment

The public HTTPS WebUI is available at https://southor251-ai4se-harness.streamlit.app/. An independent anonymous browser loaded the Agent Loop Theater, observed the mock runtime, and executed `say_done` successfully with `answer: done`, `halt_reason: done`, and a visible trace. A one-row trace slider exception was found during this test, fixed in PR #3 with a regression test, and the public page was retested successfully.

## Remaining evidence gates not representable by repository edits

1. A genuine cold-start exercise performed by a different agent type or independent session, with original questions, minimal change, diff, and verification recorded in `SPEC_PROCESS.md`.
2. The student's own 1500–2500 word/character reflection in `REFLECTION.md`.

The exact deployment and cold-start handoff is in `docs/final_submission_external_gates.md`. None of these gates should be replaced with a repository URL, a mocked screenshot, or an invented transcript.

## Safety boundary

This project supplies harness-level controls, not an operating-system sandbox. Run real-provider tasks only in a deliberately selected workspace with conservative permission rules. The default runtime omits `run_shell`.
