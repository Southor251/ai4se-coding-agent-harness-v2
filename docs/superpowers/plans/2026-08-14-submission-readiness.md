# Submission Readiness Implementation Plan

> **For agentic workers:** Execute this plan inline. Track every completed check with fresh command output; do not replace user identity fields with guessed values.

**Goal:** Make the Coding Agent Harness repository reproducible, distributable, evidence-backed, and ready for final submission once the student supplies identity and deployment details.

**Architecture:** Preserve the existing deterministic Python harness. Repair the local development entry points so they run the checked-out source, make the Docker artifact start the Streamlit WebUI, and align README, CI, and delivery evidence around one set of commands.

**Tech Stack:** Python 3.12, pytest, Ruff, Streamlit, Docker/OCI, GitHub Actions, GitLab CI, GitHub.

## Global Constraints

- The harness core remains independently testable with `MockLLM` and no network access.
- No API key may be added to source, Git, logs, container layers, or submission metadata.
- `REFLECTION.md` must remain student-authored; only an honest scaffold, checklist, and polishing guidance are permitted here.
- Final submission metadata requires the student's real ID, real name, repository URL, and a verified deployment/release URL.
- The final test claim must come from a fresh normal command against this checkout, not from an old log or a `PYTHONPATH` override.

---

### Task 1: Reproducible local verification entry point

**Files:**
- Modify: `README.md`
- Modify: `Makefile`
- Test: `tests/test_delivery_verify.py`

- [ ] **Step 1: Inspect the editable-install and verification assumptions.**

Run: `python -c "import agent_harness; print(agent_harness.__file__)"`

Expected: an import path under this checkout's `src/agent_harness` after repair.

- [ ] **Step 2: Add a documented, explicit bootstrap command.**

Document `python -m pip install -e \".[dev]\"` and verification with `python scripts/verify_delivery.py` so a new checkout cannot silently test a different editable source tree.

- [ ] **Step 3: Add a narrow regression assertion for delivery verification where needed.**

Run: `python -m pytest tests/test_delivery_verify.py -q`

Expected: PASS.

- [x] **Step 4: Verify the normal path.**

Run: `python -m pip install -e \".[dev]\"; python scripts/verify_delivery.py`

Expected: all five delivery checks exit zero without `PYTHONPATH`.

### Task 2: Make the container a real WebUI distribution artifact

**Files:**
- Modify: `Dockerfile`
- Create: `.dockerignore`
- Modify: `README.md`
- Test: `tests/test_delivery_verify.py`

- [ ] **Step 1: Write or extend a test that checks the declared distribution contract.**

The container contract must expose port `8501` and run `streamlit run src/agent_harness/web/theater.py --server.address=0.0.0.0 --server.port=8501`.

- [ ] **Step 2: Replace the test-only Docker default command with the WebUI command.**

Copy required runtime code/configuration, expose `8501`, and retain a deterministic install.

- [ ] **Step 3: Exclude virtual environments, test caches, trace/HITL state, `.env`, Git metadata, and editor files from the build context.**

- [ ] **Step 4: Build and run the image locally, then check its HTTP response.**

Run: `docker build -t ai4se-agent-harness:submission .` and a bounded localhost smoke check.

Expected: image builds; Streamlit answers on port `8501`; no key is passed or printed.

### Task 3: Align CI and delivery documentation

**Files:**
- Modify: `.github/workflows/test.yml`
- Modify: `.gitlab-ci.yml`
- Modify: `README.md`
- Modify: `SPEC.md`
- Modify: `PLAN.md`
- Modify: `SPEC_PROCESS.md`
- Modify: `AGENT_LOG.md`
- Modify: `docs/final_status.md`

- [ ] **Step 1: Update CI to run tests, Ruff, and the Docker build in the GitHub workflow.**

- [ ] **Step 2: Preserve the required GitLab `unit-test` job and document that GitHub is the active remote CI if that is the repository host.**

- [x] **Step 3: Replace stale verification counts and provisional status language only after fresh results exist.**

- [ ] **Step 4: Add a concise requirement-to-evidence matrix.**

Map six harness dimensions and the three deterministic demonstrations to exact source files/tests/commands.

- [x] **Step 5: Verify no placeholders or contradictory transport claims remain in shipped documents.**

Run: `python -m scripts.secret_scan` and targeted text search.

### Task 4: Deployment and identity gates

**Files:**
- Modify: `README.md`
- Create or modify: `submission.jsonc` only after user supplies values
- Modify: `REFLECTION.md` only with student-provided reflection material

- [ ] **Step 1: Add deploy-ready instructions and a clear deployment evidence section.**

- [ ] **Step 2: Publish a public WebUI using an account/platform expressly authorized by the user.**

Expected: an externally accessible HTTPS URL and deployment timestamp.

- [ ] **Step 3: Obtain the student's real name and ID and populate `submission.jsonc`.**

- [ ] **Step 4: Receive a student-authored 1500–2500 Chinese-character reflection draft, then perform only structural and language polishing.**

### Task 5: Final release and submission handoff

**Files:**
- Modify: relevant files from Tasks 1–4 only

- [ ] **Step 1: Run fresh normal verification, Docker smoke, secret scan, and Git diff review.**
- [ ] **Step 2: Confirm README commands, CI YAML, Docker behavior, deployment URL, and submission metadata agree.**
- [ ] **Step 3: Commit scoped changes, push to `Southor251`'s configured `origin`, and report the resulting commit and remote state.**

## Coverage Review

- Harness kernel/mock determinism: retained and reverified by Task 1.
- Distribution/WebUI: Task 2.
- CI and evidence consistency: Task 3.
- Public deployment, identity metadata, and student-authored reflection: Task 4.
- GitHub delivery and full validation: Task 5.
