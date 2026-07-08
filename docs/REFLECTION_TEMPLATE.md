# REFLECTION.md Template

> Important: write this in your own words. Use this file as a structure only. The course requirement expects your personal reflection, not a generated essay.

## 1. Project motivation and scope

Explain why the project chose a coding-agent harness rather than a full autonomous agent. State the core idea: LLM predicts the next action, but the harness implements the reliable engineering mechanisms.

## 2. Superpowers and workflow

Describe how you used the seven-step workflow. Cover:

- how the initial SPEC shaped the project boundary;
- how PLAN decomposed the project into small TDD tasks;
- how subagent/Codex-style development was used;
- what you manually reviewed or changed;
- where the workflow prevented scope creep.

## 3. TDD and deterministic verification

Discuss:

- red-green-refactor discipline;
- MockLLM tests;
- why real-provider behavior was separated from deterministic harness tests;
- why permission/HITL/scope/feedback were tested as mechanisms rather than prompts.

## 4. Harness mechanisms

Explain the main mechanisms:

- LLM interface and strict JSON action protocol;
- tool registry and built-in tools;
- PermissionPolicy;
- ScopeGuard;
- HITL request persistence and approve-and-continue;
- FeedbackSensor;
- TraceStore;
- project memory;
- CLI and Streamlit Theater.

Give concrete examples, especially the HITL write-flow demo.

## 5. Prompt/context strategy

Explain what context is passed to the LLM and why the project minimizes reliance on prompt-only safety. Emphasize that prompt instructions guide behavior, while code enforces boundaries.

## 6. Credentials, distribution, and safety

Discuss:

- keyring / ignored `.env` fallback;
- no secrets in YAML or commits;
- Docker distribution;
- local Web Theater;
- why `run_shell` is not registered by default;
- why this is not an OS sandbox.

## 7. Subagent/process critique

Reflect on what went well and what did not. Good topics:

- task granularity;
- benefit of tests before implementation;
- problems caused by changing scope;
- how documentation helped resume work;
- where more time would improve the project.

## 8. Limitations and future work

Mention:

- stronger OS-level sandboxing;
- richer provider hardening;
- better Web UI or hosted deployment;
- deeper replay/audit features;
- LSP or code intelligence;
- more realistic repository-editing benchmark tasks.

## 9. Final assessment

Conclude with what the project demonstrates about intelligent software engineering: AI prediction is useful, but trustworthy software work requires harnessing, verification, guardrails, traceability, and human control.
