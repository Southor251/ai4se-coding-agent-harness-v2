# Personal Harness Setup

This guide describes how to run the harness as a local, governed coding-agent application.

## 1. Install

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## 2. Verify The Local Build

```bash
python scripts/verify_delivery.py
```

For a command preview only:

```bash
python scripts/verify_delivery.py --dry-run
```

## 3. Configure Your API

The safe default uses `mock`. To use an OpenAI-compatible API, create or edit a profile based on `config/personal-harness.yaml`:

```yaml
workspace_root: "."
llm:
  provider: openai
  model: your-model
  temperature: 0.2
  base_url: https://your-api.example/v1
permission:
  rules:
    - name: ask before writes
      pattern: .*
      verdict: ask
      rule_type: path
memory:
  enabled: true
```

Store the API key through the credential manager or an environment variable. Do not put secrets in YAML files.

```bash
agent-harness credentials update <secret>
agent-harness credentials show
```


## 4. Check The Local Runtime

```bash
agent-harness doctor --profile config/personal-harness.yaml
```
## 5. Run A Real Provider Smoke Check

After setting `llm.provider: openai` in a local profile and storing the key through
`agent-harness credentials update`, run:

```bash
agent-harness smoke provider --profile config/local-openai.yaml --trace .harness/runs/provider-smoke.jsonl
```

The smoke command fails before calling the model if the profile still uses `mock` or if no credential is configured. It never prints the secret value.

## 6. Run A Task

```bash
agent-harness run "say done" --profile config/personal-harness.yaml --trace .harness/runs/latest.jsonl
```

The model must return one JSON action at a time:

```json
{"type":"call_tool","tool":"read_file","args":{"path":"README.md"}}
```

```json
{"type":"done","answer":"finished"}
```

## 7. Handle HITL Requests

List pending requests:

```bash
agent-harness hitl list --store .harness/hitl/requests.json
```

Approve and execute one pending action:

```bash
agent-harness hitl approve <request_id> --profile config/personal-harness.yaml --store .harness/hitl/requests.json
```

Approve and continue a saved-context task:

```bash
agent-harness hitl approve <request_id> --continue --profile config/personal-harness.yaml --store .harness/hitl/requests.json
```

Deny without executing:

```bash
agent-harness hitl deny <request_id> --store .harness/hitl/requests.json
```

## 8. Use The Web Console

```bash
streamlit run src/agent_harness/web/theater.py
```

The Web console can run goals, select trace history from `.harness/runs`, inspect trace steps, and approve or deny HITL requests.

## Safety Defaults

- `run_shell` is not registered in the default governed runtime.
- File actions are checked by `ScopeGuard`.
- The starter personal profile asks before writes.
- API secrets should stay in the credential manager, environment variables, or an ignored local `.env` file.
