# AI4SE Coding Agent Harness

一个面向软件开发任务的、可确定性验证的 Coding Agent Harness。项目以 `MockLLM` 驱动完整控制循环，因此主循环、工具分发、治理护栏、反馈回灌、记忆和停机逻辑都能在离线单元测试中验证，而不依赖真实 API 或网络。

## 课程要求对应证据

| 课程要求 | 代码与证据 |
| --- | --- |
| 自主实现 harness 主循环与 LLM 抽象 | `src/agent_harness/agent/loop.py`、`src/agent_harness/llm/interface.py`、`src/agent_harness/llm/mock.py`、`tests/test_loop.py` |
| 动作/工具 | `src/agent_harness/tools/`、`tests/test_tools.py` |
| 治理与 HITL | `src/agent_harness/governance/`、`src/agent_harness/hitl/`、`tests/test_governance_loop.py`、`tests/test_hitl*.py` |
| 客观反馈与自我修正 | `src/agent_harness/feedback/`、`tests/test_feedback*.py` |
| 记忆与配置 | `src/agent_harness/memory/`、`src/agent_harness/config/`、对应单元测试 |
| 三项确定性机制演示 | `demo/demo_guardrail.py`、`demo/demo_feedback.py`、`demo/demo_scope.py` |
| 凭据安全 | `src/agent_harness/credentials/`、`.gitignore`、`scripts/secret_scan.py` |
| 分发与 WebUI | `Dockerfile`、`.github/workflows/test.yml`、`src/agent_harness/web/theater.py` |

详细设计见 `SPEC.md`，实施过程见 `PLAN.md`、`SPEC_PROCESS.md` 与 `AGENT_LOG.md`。

## 已实现的能力

- 自主实现的循环：上下文装配 → LLM 决策 → 动作解析 → 治理检查 → 工具分发 → 反馈回灌 → 停机判断。
- `MockLLM`、严格 JSON action protocol，以及 OpenAI-compatible 单次调用适配层。
- 受工作区范围约束的读写工具；默认运行时不注册 `run_shell`。
- `PermissionPolicy`、`ScopeGuard`、持久化 HITL 请求与批准/拒绝/继续执行。
- 对工具结果的确定性反馈分类和 JSONL trace。
- Streamlit Agent Harness Console：运行任务、查看 trace、检查 HITL 队列和安全状态。
- Windows Credential Manager 优先、受 Git 忽略的 `.env` 回退；凭据状态不会输出明文。

## 已知边界

- 这是 harness 层的治理，不是操作系统级沙箱；真实项目仍应在受限工作区和最小权限环境运行。
- 默认配置使用 `mock`。真实 OpenAI-compatible 模型需要用户在目标机器上自行安全配置 endpoint、model 与 key。
- Dockerfile 与 CI 已配置为启动并 smoke-test WebUI；本机 Docker Desktop 当前未运行，因此本地容器启动不在本批次中声称已验证。公开部署 URL 仍需由项目所有者使用获授权的部署账号创建并验证。
- `REFLECTION.md` 必须由学生本人完成。仓库中的说明仅提供题纲与自检标准，不是可提交的代写内容。

## 安装

需要 Python 3.12 或更高版本。为避免 editable 安装仍指向旧副本，在本仓库根目录创建或重新绑定虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -c "import agent_harness; print(agent_harness.__file__)"
```

最后一条命令必须显示本仓库下的 `src\agent_harness\__init__.py`。Linux/macOS 使用 `source .venv/bin/activate`，其余命令相同。

## 验证

```powershell
python scripts/verify_delivery.py
python -m demo.demo_guardrail
python -m demo.demo_feedback
python -m demo.demo_scope
```

`verify_delivery.py` 依次运行 pytest、Ruff、mock CLI run、HITL list 和 secret/占位标记扫描。它不调用真实 LLM，也不要求 API key。

## 使用 WebUI

```powershell
streamlit run src/agent_harness/web/theater.py
```

浏览器打开 Streamlit 输出的本地地址。默认 trace 位于 `.harness/runs/latest.jsonl`，HITL 请求位于 `.harness/hitl/requests.json`。首次运行前可先执行任一 demo 生成可回放的确定性行为。

## 凭据与真实供应商

默认 `config/agent-harness.yaml` 使用 `mock`。接入真实 OpenAI-compatible 服务前，先复制/维护个人 profile，再使用：

```powershell
agent-harness credentials update
agent-harness doctor --profile config/personal-harness.yaml
agent-harness run "read README.md" --profile config/personal-harness.yaml
```

key 不得写入源码、Git、日志、命令行历史或容器镜像。运行时环境中的非空 `OPENAI_API_KEY` 优先于已保存凭据，便于部署平台注入 secret；`.env` 是明文回退方案，必须保持在 `.gitignore` 中，且进程环境对同一机器上的适当权限主体可见。优先使用系统 keyring。详见 `docs/personal_setup.md`。

## Docker 分发

Docker 镜像默认启动 WebUI，而不是仅运行测试：

```powershell
docker build -t ai4se-agent-harness:submission .
docker run --rm -p 8501:8501 ai4se-agent-harness:submission
```

然后访问 `http://localhost:8501`。不要通过 Dockerfile、镜像层或提交的 Compose 文件传入真实 key。若目标机使用 `.env`，可在本机受限权限下创建后以 `docker run --env-file .env --rm -p 8501:8501 ai4se-agent-harness:submission` 注入；`.env` 为明文且进程环境可见，不能提交到 Git。

## CI 与提交前检查

GitHub Actions 在每次 push 时运行 `unit-test`（pytest + Ruff）和 `container-build`（Docker build + 8501 HTTP smoke）。`.gitlab-ci.yml` 也保留课程要求的 `unit-test` job。最终提交前应确认：

1. 最新远端 CI 为 pass；
2. Docker WebUI 可从新镜像启动；
3. 有真实、可访问的 HTTPS WebUI 部署 URL；
4. `REFLECTION.md` 是本人完成的 1500–2500 字反思；
5. `submission.jsonc` 填写真实学号、姓名、仓库 URL 和部署 URL；
6. `git status` 干净，且 `scripts/secret_scan.py` 无发现。

## 目录结构

```text
src/agent_harness/agent/       主循环与依赖容器
src/agent_harness/governance/  Scope、权限和 HITL
src/agent_harness/feedback/    反馈分类、传感与修正状态
src/agent_harness/trace/       JSONL trace
src/agent_harness/tools/       工具注册表与内置工具
src/agent_harness/credentials/ 凭据管理
src/agent_harness/web/         Streamlit WebUI 与服务层
demo/                          三项确定性机制演示
tests/                         离线单元与集成测试
docs/superpowers/              设计、计划与提交收口记录
```
