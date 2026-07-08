# Release Verification Procedure

This procedure is the canonical release gate for the final project.

## Clean Checkout

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Automated Verification

```bash
python scripts/verify_delivery.py
```

A successful run means the deterministic harness mechanisms pass without any real API key.

## Docker Verification

```bash
docker build -t ai4se-agent-harness .
```

The Docker build is intentionally keyless. It validates package installation and test execution in a clean image.

## CLI Smoke

```bash
agent-harness doctor --profile config/personal-harness.yaml
agent-harness run "say done" --profile config/personal-harness.yaml --trace .harness/runs/latest.jsonl
agent-harness hitl list --store .harness/hitl/requests.json
```

## HITL Write Demo

```bash
python -m demo.demo_hitl_write
```

The expected status is `approved_and_written`.

## Web Theater

```bash
streamlit run src/agent_harness/web/theater.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Validate:

- runtime status is visible in the sidebar.
- trace summary displays step counts and HITL counts.
- HITL list/approve/deny/approve+continue controls are visible.
- no credential value is displayed.

## Real Provider Smoke

This section is local-only.

```bash
agent-harness credentials update
agent-harness doctor --profile config/local-openai.yaml
agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl
```

Do not commit `config/local-openai.yaml` if it contains private endpoint details.
