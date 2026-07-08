# Final Commands

Use this sequence before submission.

## 1. Confirm clean branch state

```bash
git status --short
git log --oneline -10
```

## 2. Run final verification

```bash
python scripts/verify_delivery.py
```

Expected checks:

```text
pytest
ruff
doctor
cli_run
hitl_list
hitl_write_demo
secret_scan
```

## 3. Run Docker smoke

```bash
docker build -t ai4se-agent-harness .
```

## 4. Run Web Theater locally

```bash
streamlit run src/agent_harness/web/theater.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Check:

- Runtime status is visible.
- Provider/profile/workspace are visible.
- Pending HITL count is visible.
- Trace summary is visible.
- `run_shell registered` remains `False`.

## 5. Optional real API smoke

Do not commit `config/local-openai.yaml`, `.env`, screenshots containing keys, or trace records that contain secrets.

```bash
agent-harness credentials update
agent-harness doctor --profile config/local-openai.yaml
agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl
```

## 6. Commit

```bash
git add .
git commit -m "final: harden delivery verification and submission docs"
git push
```

## 7. After push

Check GitHub Actions. Record the latest passing run in `docs/final_status.md` or your submission notes.
