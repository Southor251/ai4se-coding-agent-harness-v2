# HITL Write Walkthrough

This walkthrough validates the write-safety path: the agent proposes a file write, the harness
turns the action into a pending human approval request, the file is not written before approval,
and approval executes the tool under `ScopeGuard` before the loop continues.

## Deterministic local demo

Run the mock-LLM demo first. It does not require an API key and does not use shell execution.

```bash
python -m demo.demo_hitl_write
```

Expected result fields:

```text
'status': 'approved_and_written'
'request_status': 'approved'
'file_existed_before_approval': False
'file_written': True
'halt_reason': 'done'
```

The demo writes `.harness/demo_workspace/hello.txt` only after the pending request is approved.
It uses the same HITL resume helper as the CLI approval path.

## Test command

```bash
python -m pytest tests/test_hitl_write_flow.py -q
```

Then run the delivery suite:

```bash
python scripts/verify_delivery.py
```

## Real provider walkthrough

For a real OpenAI-compatible provider, keep credentials out of YAML and out of Git.

```bash
agent-harness doctor --profile config/local-openai.yaml
agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl
```

Use a profile whose permission rules ask before writes:

```yaml
permission:
  rules:
    - name: ask before writes
      pattern: .*
      verdict: ask
      rule_type: path
```

Then run a write task against a controlled workspace, inspect the pending request, and approve it:

```bash
agent-harness run "Create demo.txt in the workspace with one short sentence." \
  --profile config/local-openai.yaml \
  --trace .harness/runs/hitl-write.jsonl

agent-harness hitl list --store .harness/hitl/requests.json
agent-harness hitl approve <request_id> --continue \
  --profile config/local-openai.yaml \
  --store .harness/hitl/requests.json
```

The file should not be written before approval. Approval still rechecks scope before executing the
stored tool action.
