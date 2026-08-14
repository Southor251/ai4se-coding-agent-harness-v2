# 最终提交外部收口操作单

本文件记录需要真实外部操作才能完成的课程证据。公网部署已完成并保留验证证据；异构冷启动仍不得由仓库链接、CI 绿灯或模拟记录替代。

## 1. 公网 WebUI 部署


### 已完成的部署证据（2026-08-14）

- 公开地址：https://southor251-ai4se-harness.streamlit.app/
- 浏览器在无登录状态下加载了 Agent Loop Theater、mock Provider、Trace 与 HITL 区域。
- 使用 WebUI 输入 `say_done` 并点击 Run，显示 `answer: done`、`halt_reason: done` 与单步 trace。
- 首次验证暴露单条 trace 的 slider 边界错误；PR #3 增加回归测试后合并，重新验证页面显示 Step 1 且无 StreamlitAPIException。
### 已准备好的仓库条件

- 仓库：`https://github.com/Southor251/ai4se-coding-agent-harness-v2`
- 分支：`main`
- Streamlit 入口：`src/agent_harness/web/theater.py`
- 依赖：根目录 `requirements.txt` 中的 `-e .` 安装本项目及 `pyproject.toml` 声明的依赖。
- Python：在 Streamlit Community Cloud 的 Advanced settings 选择 Python `3.12`。
- 应用默认使用 `mock` provider，不需要、也不应上传真实 API key 即可展示三项确定性机制与 WebUI。

### 推荐平台与实际步骤

使用 Streamlit Community Cloud：

1. 访问 `https://share.streamlit.io`，以拥有该 GitHub 仓库管理员权限的 GitHub 账户登录并授权 Streamlit。
2. 选择 **Create app**，仓库为 `Southor251/ai4se-coding-agent-harness-v2`，分支为 `main`，入口填写 `src/agent_harness/web/theater.py`。
3. 在 **Advanced settings** 选择 Python `3.12`。不要填入真实 `OPENAI_API_KEY`；课程演示使用默认 mock 配置。
4. 选择易辨认的公开子域名，例如 `southor251-ai4se-harness`，然后点击 Deploy。
5. 等待构建完成，从无登录浏览器窗口打开分配的 `https://*.streamlit.app` 地址，确认首页显示 Agent Harness Console，并运行一次 mock task 或 demo trace。
6. 将该 HTTPS URL 写入 `submission.jsonc` 的 `deploy_release_url`，并把 `is_deployed` 改为 `true`。在 README 的部署记录和 `docs/final_status.md` 中记录实际 URL、验证日期和验证动作。

### 验收标准

- URL 通过 HTTPS 公开访问；不依赖部署平台管理员登录。
- 首页能加载；一次 mock run 或已有 trace 回放可见。
- 浏览器、Git 历史、平台 Secret 输入和日志中没有真实凭据。
- 仓库最新提交对应的 GitHub Actions `unit-test` 与 `container-build` 都为 pass。

## 2. 异构冷启动证据

课程要求的是一次真实的不同 Agent 类型或独立新会话，只获得 `SPEC.md` 和 `PLAN.md` 后的工作记录。当前仓库不能以同一会话的复述或内部代码审阅替代这项证据。

### 执行边界

- 新会话只可获得 `SPEC.md`、`PLAN.md` 与以下任务指令；不要提供本次对话、`SPEC_PROCESS.md`、`AGENT_LOG.md` 或完整实现历史。
- 可选工具为与本次 Codex 会话不同的 Agent 类型，例如 Claude Code、Gemini CLI 或 Cursor Agent；必须记录实际工具与会话日期。
- 任务限定为发现并修订一处文档歧义，或实现一个 1–2 task 范围的最小改动。不得为了制造记录而捏造问题。

### 给独立 Agent 的原样任务

```text
你只能阅读 SPEC.md 和 PLAN.md。请识别一个会阻碍你开始实现的具体歧义或缺失信息；提出最少澄清问题。收到答复后，只修改解决该问题所必需的文件，并运行相关验证。请输出：问题、你的假设、改动文件与 diff 摘要、运行命令和原始结果。
```

### 必须记录的事实

完成后，由项目所有者把以下真实信息追加到 `SPEC_PROCESS.md`：

- Agent 类型、日期和它实际得到的输入范围；
- 它提出的原始问题；
- 人工给出的答案或采用的假设；
- 最小改动的 commit/PR、文件 diff 摘要和验证命令结果；
- 哪一处 SPEC/PLAN 因此更明确。

## 3. 最终提交前的人工核对

除 `REFLECTION.md` 外，在课程平台提交同一个仓库链接前，确认：

1. `main` 是最新提交状态，且公开可访问；
2. GitHub Release `v1.0.0-course-submission` 存在并指向其已验证的源码快照；
3. `submission.jsonc` 的姓名、学号、仓库 URL、部署状态和部署 URL 都真实；
4. 最新 GitHub Actions 为 pass；
5. 公网 WebUI URL 从无登录浏览器可打开；
6. 异构冷启动记录已真实追加到 `SPEC_PROCESS.md`；
7. 最后由学生本人替换并完成 `REFLECTION.md`。
