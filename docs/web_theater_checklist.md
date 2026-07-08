# Web Theater Hardening Checklist

This checklist describes the intended manual verification path for the Streamlit Agent Loop Theater.

## Start

```bash
streamlit run src/agent_harness/web/theater.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

## Sidebar status

The sidebar should show:

- the active config path and profile path inputs;
- the selected trace path and trace-history selector;
- the HITL store path;
- runtime status with provider, pending HITL count, workspace root, trace existence, and whether `run_shell` is registered.

The runtime status must not display credential values.

## Trace inspection

After a run, the Trace panel should show:

- total steps;
- tool-call count;
- denial count;
- pending HITL count;
- feedback-event count;
- per-step LLM decision, action, tool, permission, HITL status, tool success, and feedback category when available.

## HITL path

For a write task under an ask-before-write profile:

1. Run the task from the Web console.
2. Confirm a pending HITL request appears.
3. Use `Approve + Continue`.
4. Confirm the run result updates and the trace can still be selected from `.harness/runs`.

## Safety expectation

The Web console uses the same service layer as the CLI. It should not bypass `ScopeGuard`, permission policy, or the persistent HITL store.
