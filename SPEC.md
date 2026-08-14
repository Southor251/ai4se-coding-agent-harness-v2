# SPEC · Coding Agent Harness

> 项目：AI4SE 期末项目 · A 类
> 版本：v2.0（范围收缩 + 三新机制 + 可测自愈 + Agent Loop Theater）
> 日期：2026-07-07
> 状态：本地提交打磨已完成；公开部署、真实 submission 身份字段、本人反思与异构冷启动记录仍为外部收口项。
> 变更摘要：v1.0 范围过大，v2.0 收缩为垂直切片；新增 PermissionPolicy / ScopeGuard / TraceStore 三机制；自愈闭环改为确定性可测；WebUI 改为 Agent Loop Theater 回放；插件系统保留；文件快照 / 跨会话记忆 / PyPI / LSP 移到未来工作

---

## 1. 问题陈述

### 1.1 要解决的问题

当前 LLM 编码能力已高度成熟，但"LLM 能思考"与"Agent 能可靠工作"之间存在一道工程鸿沟。裸 LLM 只是一个会生成文本的循环，缺乏工具执行、安全治理、客观反馈、可观测性等工程支撑。这些工程的总和就是 **Harness**。

核心等式：

$$Agent = LLM \times Harness$$

本项目构建一个教学演示型的 Coding Agent Harness，以最直观的方式展示上述等式，同时为开发者个人长期使用预留插件扩展接口。

### 1.2 目标用户

- **主要（教学演示）**：AI4SE 课程学生与评审老师，通过源码 + 演示理解 harness 如何运转
- **次要（个人长期）**：开发者希望在自有项目中嵌入一个轻量、可扩展的编码智能体

### 1.3 核心命题与 main contribution

课程命题的代码级回答：LLM 在整个 agent 循环中只做**一行**任务决策（"下一步做什么"），其余全部是工程：工具分发、治理护栏、反馈回灌、可观测性。本 harness 的每行代码都在为这句话提供证明。

**main contribution**：一个可回放、可单测的 Coding Agent Harness 内核。它用确定性权限引擎和反馈传感器证明：移除真实 LLM 后，治理、反馈、工具分发、trace 仍可独立验证。

### 1.4 v1 范围边界

| 纳入 v1 | 移到未来工作（v1.1+） |
|---------|----------------------|
| 主循环 + MockLLM + OpenAILLM | 文件快照（危险动作前拍照 + 回滚） |
| 5 个核心工具 | 跨会话记忆（consolidate + JSON 持久化） |
| PermissionPolicy（allow/ask/deny） | 熵管理（compact 压缩） |
| ScopeGuard（路径围栏） | LSP 实时反馈 |
| FeedbackSensor（失败分类 + 回灌） | 双通道 HITL（WebUI 实时审批） |
| TraceStore（JSONL 轨迹） | PyPI 分发 |
| Agent Loop Theater（trace 回放） | 并发子 agent（fan-out） |
| 插件系统（5 基类 + 注册表 + 4 钩子） | TodoList 持久化 |
| 凭据管理（keyring + .env） | 预算三维追踪（仅保留 steps） |
| Docker 分发 | |
| 机制演示（3 个确定性脚本） | |

---

## 2. 用户故事（INVEST 原则）

| # | 标题 | 角色 | 故事 | 验收标准 |
|---|------|------|------|----------|
| US-01 | **教学演示** | 学生 | 我想看到一个具备治理护栏和反馈闭环的 harness 演示，直观理解 $Agent = LLM \times Harness$ | Agent Loop Theater 中每一轮循环以金色高亮 LLM 决策行，以蓝色显示 harness 工程动作 |
| US-02 | **CLI 启动** | 用户 | 我想通过一条 CLI 命令启动 harness，提供 API key 后让它帮我读写代码文件、运行测试 | `agent-harness run "添加单元测试"` → agent 创建测试文件 → 运行 → 报告结果 |
| US-03 | **轨迹回放** | 用户 | 我想在 WebUI 中回溯完整的决策轨迹 | 运行后生成 trace.jsonl，Agent Loop Theater 按 step 回放每轮的 LLM 决策、动作、权限结果、工具结果、反馈 |
| US-04 | **危险操作拦截** | 用户 | 当 agent 试图执行危险操作时，我希望它被拦截并等待我确认 | `rm -rf /`、越界路径、敏感文件写入被 PermissionPolicy 拦截，CLI 弹窗审批，可批准/拒绝/超时默认拒绝 |
| US-05 | **插件扩展** | 开发者 | 我想通过注册插件来扩展 harness 的工具体系，不修改核心代码 | 实现 ToolPlugin 子类 → 注册 → 新工具出现在功能菜单中；entry_points 发现作为可选增强 |
| US-06 | **自愈闭环** | 用户 | 测试失败后 agent 收到结构化反馈并据此改变下一步动作 | 注入一次测试失败 → FeedbackSensor 分类为 assertion → 回灌结构化 feedback → MockLLM 选择下一条预设动作 → 记录修正次数 |
| US-07 | **生命周期钩子** | 开发者 | 我想注册 before_action / after_action / on_feedback / on_halt 钩子 | 钩子在对应事件触发时执行，before_action 钩子可返回 deny 拦截 |
| US-08 | **YAML 配置** | 用户 | 我想通过 YAML 文件声明 agent 行为约束 | `max_steps: 50`、`workspace_root: "./workspace"` → 加载后 agent 遵守约束 |

---

## 3. 功能规约

### 3.1 LLM 抽象层 (`src/agent_harness/llm/`)

| 项目 | 内容 |
|------|------|
| 输入 | `context: list[Message]`, `menu: list[ToolDef]` |
| 行为 | 调用 LLM API，解析响应为 `(text: str, action: AgentAction)` |
| 输出 | `LLMResponse(text, action)` |
| 边界 | context 为空 → 返回默认提示；API 超时 → 抛出重试异常 |
| 错误 | API key 无效 → 明确错误信息；网络错误 → 最多重试 3 次 |
| 实现 | `LLMInterface` 抽象基类 → `MockLLM`（固定/预设响应队列）+ `OpenAILLM`（真实 API） |

**MockLLM 设计要点**：MockLLM 接受一个预设的响应队列 `list[LLMResponse]`，每次调用弹出下一个。这使得"收到结构化 feedback 后选择下一条预设动作"可确定性测试，符合 A.4-(C) 硬标准。

### 3.2 Agent 主循环 (`src/agent_harness/agent/loop.py`)

| 项目 | 内容 |
|------|------|
| 输入 | `goal: str`, `H: Harness` |
| 行为 | context 装配 → while 循环 → 每轮：菜单构建 → LLM 调用 → 解析 → 权限检查 → 分发 → 反馈 → 停机判断 |
| 输出 | `answer: str` |
| 停机条件 | `action.type == "done"` 或 `steps >= MAX_STEPS` |
| 边界 | MAX_STEPS=0 → 立即返回空；context 为空 → 仅 system prompt |
| 错误 | LLM 连续失败 N 次 → 停机并报告 |

### 3.3 工具系统 (`src/agent_harness/tools/`)

v1 实现 5 个核心工具：

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `read_file` | 读取文件内容 | `path: str` | `ToolResult(content)` |
| `write_file` | 写入文件 | `path, content` | `ToolResult(success)` |
| `edit_file` | 替换文件中的文本 | `path, old, new` | `ToolResult(success, diff)` |
| `run_shell` | 执行 shell 命令 | `command: str` | `ToolResult(stdout, stderr, exit_code)` |
| `run_test` | 运行测试 | `pattern: str` | `ToolResult(passed, failed, output)` |

工具错误处理：`ToolError` 异常 + try/except，失败信息作为客观事实回灌上下文。

### 3.4 PermissionPolicy 权限引擎 (`src/agent_harness/governance/permission.py`)

**参考来源**：[OpenCode permissions](https://opencode.ai/docs/permissions) 与 [Codex permissions](https://developers.openai.com/codex/permissions)。

| 项目 | 内容 |
|------|------|
| 输入 | `action: AgentAction`, `rules: list[PermissionRule]` |
| 行为 | 遍历规则 → 模式匹配 → 返回 verdict |
| 输出 | `Verdict: "allow" \| "ask" \| "deny"` |
| 优先级 | `deny` 优先级最高；多条规则命中时取最严格 |
| 规则类型 | 路径规则（allow/deny/ask）、命令规则（allow/deny/ask）、正则规则 |
| 边界 | 空规则 → 全部 allow；全量 deny → 所有动作被拦截 |
| HITL | verdict == "ask" 时触发审批：pending → approved/denied/timed_out |
| 超时 | N 秒无响应 → 默认 deny |

**与 v1.0 的区别**：v1.0 只有 allow/deny 两态，v2.0 增加 "ask" 态对应"需人工审批"，直接映射 OpenCode 的权限模型与 Codex 的 read/write/deny 三态。

### 3.5 ScopeGuard 路径围栏 (`src/agent_harness/governance/scope.py`)

| 项目 | 内容 |
|------|------|
| 输入 | `path: str`, `workspace_root: Path` |
| 行为 | 路径规范化（`os.path.realpath` 解析 `..`、符号链接）→ 检查是否在 workspace_root 内 → 检查敏感路径 |
| 输出 | `ScopeVerdict: "inside" \| "outside" \| "sensitive"` |
| 敏感路径 | `/etc/`、`/var/lib/`、`C:\Windows\`、`.git/`、`.env` |
| 边界 | workspace_root 不存在 → 全部 outside；路径为空 → inside |
| 与权限引擎联动 | outside/sensitive → PermissionPolicy 返回 deny |

**设计理由**：课程 A 文件强调治理边界。不做真沙箱（容器隔离）时，路径围栏是最低可信的治理。Codex 的 sandbox 也以 workspace root 为基础。

### 3.6 FeedbackSensor 反馈传感器 (`src/agent_harness/feedback/`)

| 项目 | 内容 |
|------|------|
| 输入 | `ToolResult`（来自 run_test / run_shell） |
| 行为 | 解析输出 → 分类失败 → 生成结构化 feedback → 回灌上下文 |
| 输出 | `Feedback(category: str, message: str, raw: str)` |
| 失败分类 | `syntax`（语法错误）、`assertion`（断言失败）、`timeout`（超时）、`tool_error`（工具调用失败） |
| 自愈机制 | FeedbackSensor 注入结构化 feedback → MockLLM 收到后选择下一条预设动作 → 记录修正次数 → 超限（默认 3 次）升级给人 |

**确定性可测设计**：自愈闭环不依赖 LLM 的"理解力"。测试时 MockLLM 的响应队列预设为：[动作A（改代码）, 动作B（改完跑测试）, 动作C（done）]。注入一次测试失败后，FeedbackSensor 回灌结构化 feedback，MockLLM 弹出动作B。整条链路无需真实 LLM，每次运行结果相同。

### 3.7 TraceStore 轨迹存储 (`src/agent_harness/trace/`)

| 项目 | 内容 |
|------|------|
| 格式 | JSONL，每行一个 step |
| 每行内容 | `step`, `llm_text`, `llm_action`, `permission_verdict`, `tool_result`, `feedback`, `context_size`, `timestamp` |
| 写入时机 | 循环内每轮 `record()`（增量落盘）+ 会话末 `flush()` |
| 文件路径 | `.harness/trace/{session_id}.jsonl` |
| 边界 | 无 trace 文件 → 空回放；trace 文件损坏 → 跳过坏行 |
| 消费者 | Agent Loop Theater 读取并回放 |

**设计理由**：参考 OpenCode 的 trace 与 agent-loop.html 中"可观测性"概念卡的双节奏（record 每轮 / flush 会话末）。增量落盘保证中途崩溃不丢决策链。

### 3.8 记忆系统 (`src/agent_harness/memory/`)

v1 仅实现会话级：

| 项目 | 内容 |
|------|------|
| 会话级 | 循环内 `take_note` → `write_note` → `read_notes` |
| 边界 | 无笔记 → 空列表 |
| 跨会话 | 移到未来工作（v1.1+） |

### 3.9 配置系统 (`src/agent_harness/config/`)

```yaml
# agent-harness.yaml
max_steps: 50
workspace_root: "./workspace"
llm:
  provider: mock  # mock | openai
  model: gpt-4
permission:
  denied_commands: ["rm -rf", "format", "shutdown", "del /f"]
  denied_paths: ["/etc/", "/var/lib/", "C:\\Windows\\", ".git/", ".env"]
  ask_paths: ["./src/**/*.py"]  # 写 src 下 py 文件需确认
feedback:
  max_retries: 3
```

### 3.10 凭据管理 (`src/agent_harness/credentials/`)

| 项目 | 内容 |
|------|------|
| 存储 | Windows Credential Manager（优先）→ `.env` 文件（回退） |
| 首次运行 | 隐藏输入（getpass）→ 验证 → 保存 |
| 查看 | `credentials show` → "状态: 已配置 (最后更新: 日期)"，不得回显明文 |
| 更新 | `credentials update` → 隐藏输入新 key |
| 清除 | `credentials clear` → 确认后删除 |

### 3.11 插件系统 (`src/agent_harness/plugins/`)

| 扩展点 | 基类 | 说明 |
|--------|------|------|
| 工具插件 | `ToolPlugin` | 注册自定义工具 |
| 护栏插件 | `GuardrailPlugin` | 注册自定义权限规则 |
| 传感器插件 | `SensorPlugin` | 注册自定义反馈传感器 |
| 记忆后端 | `MemoryBackend` | 替换记忆存储方式 |
| UI 面板 | `UIPanel` | 注册自定义回放页面 |

| 钩子 | 触发时机 |
|------|----------|
| `before_action` | 工具执行前（可返回 deny 拦截） |
| `after_action` | 工具执行后 |
| `on_feedback` | 反馈传感器产出结果后 |
| `on_halt` | 循环停机时 |

**发现机制（dsv4flash 友好设计）**：
1. **显式注册**（主路径）：在 YAML 配置中声明插件入口，启动时加载。dsv4flash 对此最可靠。
2. **entry_points 发现**（可选增强）：`importlib.metadata.entry_points` 扫描，作为 pip 安装插件的自动发现。带配置开关 `plugins.auto_discover: true`。

### 3.12 Agent Loop Theater (`src/agent_harness/web/theater.py`)

| 项目 | 内容 |
|------|------|
| 框架 | Streamlit 单页面应用 |
| 数据源 | 读取 `.harness/trace/{session_id}.jsonl` |
| 回放方式 | 按 step 逐步回放，可前进/后退/跳转 |
| 可视化 | 金色高亮 LLM 决策行（`llm_text` + `llm_action`），蓝色显示 harness 工程动作（`permission_verdict` + `tool_result` + `feedback`） |
| 侧栏 | 显示 context_size 变化曲线、step 计数、停机原因 |
| 边界 | trace 文件不存在 → 显示"请先运行 agent" |

**与 v1.0 的区别**：v1.0 做 5 个 Streamlit 页面 + 实时观察，依赖 session_state 管理，dsv4flash 不可靠。v2.0 改为单页面 trace 回放，确定性读取 JSONL 文件，dsv4flash 可靠。

---

## 4. 非功能性需求

### 4.1 性能

- LLM 调用超时：30s
- 工具执行超时：60s（可配置）
- Agent Loop Theater 加载：< 2s
- trace 回放：100 轮以内即时加载

### 4.2 安全（凭据威胁模型）

| 威胁 | 对策 | 严重程度 |
|------|------|----------|
| `.env` 文件泄露 | 加入 `.gitignore`；README 明确警告；Docker 运行时建议 volume mount | 中 |
| 进程环境变量可读 | 尽早读入后 `os.environ.pop("OPENAI_API_KEY", None)` | 低 |
| 日志泄露 key | 所有日志输出前过滤 `sk-...` 模式 | 高 |
| Git 历史泄露 | 提交前自查脚本；CI 中设密钥扫描 | 高 |
| 内存 dump | Python 无法完全防御；优先 keyring 加密存储 | 已说明 |
| 越界文件访问 | ScopeGuard 路径规范化 + workspace root 限制 | 高 |

### 4.3 可用性

- CLI 首次运行引导：用户输入 key 后 30s 内可开始使用
- Docker 单命令启动：`docker run -p 8501:8501 agent-harness`
- 错误信息中文化（或中英双语）
- 所有配置项有默认值

### 4.4 可观测性

- 每轮 trace 记录完整（决策 + 动作 + 结果 + 权限 + 反馈 + 上下文大小）
- Agent Loop Theater: 金色 = LLM 决策，蓝色 = harness 工程
- 会话末 trace flush 落盘
- 循环内增量落盘，中途崩溃可回放已记录部分

---

## 5. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│              Agent Loop Theater (Streamlit)                   │
│  读取 trace.jsonl → 逐步回放 → 金色/蓝色手术灯可视化        │
└────────────────────────┬────────────────────────────────────┘
                         │ 读取 JSONL
┌────────────────────────▼────────────────────────────────────┐
│                      CLI (argparse)                           │
│  run · web · credentials {show,update,clear}                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Agent 主循环                                │
│  [一次] build_agent() → [循环] agent_loop() → [收尾] cleanup │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐│
│  │LLM 抽象层│→│PermissionPolicy│→│工具分发  │→│FeedbackSensor││
│  │MockLLM   │  │+ ScopeGuard   │  │ToolRegistry│  │失败分类+回灌  ││
│  │OpenAILLM │  │allow/ask/deny │  │5 内建工具│  │自愈计数      ││
│  └──────────┘  └──────────────┘  └──────────┘  └──────────┘│
└───────┬───────────────┬──────────────┬───────────────────────┘
        │               │              │
┌───────▼───────┐ ┌─────▼──────┐ ┌────▼──────────┐
│ TraceStore     │ │ 记忆系统    │ │ 配置系统       │
│ JSONL 增量落盘 │ │ scratchpad │ │ YAML → Pydantic│
│ record+flush   │ │ (会话级)   │ │ schema 校验    │
└───────────────┘ └────────────┘ └───────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 插件系统 (Plugin System)                                     │
│ ToolPlugin · GuardrailPlugin · SensorPlugin                 │
│ MemoryBackend · UIPanel                                     │
│ Hooks: before_action / after_action / on_feedback / on_halt │
│ 发现: 显式注册(主) + entry_points(可选)                      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 凭据管理 (Credentials)                                       │
│ Windows Credential Manager / .env · 隐藏输入 · 更新/清除    │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户输入 goal
  → build_agent() 装配 context（system prompt + rules + memory + goal）
  → while 循环:
    1. 构建功能菜单（tools + 插件工具）
    2. LLM(context, menu) → (text, action)     ← 唯一一行"任务决策"
    3. PermissionPolicy.check(action) + ScopeGuard.check(path)
       → allow? → 继续
       → ask? → HITL 审批
       → deny? → 拦截，回灌"被策略拦截"
    4. dispatch: call_tool / take_note
    5. run_hooks(before_action) → 执行 → run_hooks(after_action)
    6. FeedbackSensor.parse(tool_result) → 分类 → 结构化 feedback 回灌
    7. TraceStore.record(step)  ← 每轮增量落盘
  → 退出后: TraceStore.flush() + run_hooks(on_halt)
  → 返回 answer
```

### 外部依赖

| 依赖 | 用途 | 版本要求 |
|------|------|----------|
| openai | LLM API 调用 | ≥1.0 |
| keyring | Windows Credential Manager | 最新 |
| streamlit | Agent Loop Theater | ≥1.28 |
| pyyaml | 配置解析 | 最新 |
| pydantic | 数据模型校验 | ≥2.0 |
| pytest | 测试框架 | ≥7.0 |

---

## 6. 数据模型

### 6.1 核心实体

```python
@dataclass
class AgentAction:
    type: Literal["call_tool", "done", "take_note"]
    tool: str | None = None
    args: dict | None = None
    note: str | None = None
    changed_code: bool = False

@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str | None = None
    files_changed: list[str] = field(default_factory=list)

@dataclass
class TraceRecord:
    step: int
    llm_text: str
    llm_action: AgentAction
    permission_verdict: Literal["allow", "ask", "deny"]
    hitl_status: Literal["pending", "approved", "denied", "timed_out"] | None = None
    tool_result: ToolResult | None = None
    feedback: "Feedback | None" = None
    context_size: int = 0
    timestamp: float = 0.0

@dataclass
class Feedback:
    category: Literal["syntax", "assertion", "timeout", "tool_error", "success"]
    message: str
    raw: str

@dataclass
class HITLRequest:
    id: str
    action: AgentAction
    reason: str
    status: Literal["pending", "approved", "denied", "timed_out"]
    created_at: float
    decided_by: Literal["human", "auto_deny", "timeout"] | None = None
    resolved_at: float | None = None

@dataclass
class PermissionRule:
    name: str
    pattern: str
    verdict: Literal["allow", "ask", "deny"]
    rule_type: Literal["path", "command", "regex"]

@dataclass
class ScopeVerdict:
    decision: Literal["inside", "outside", "sensitive"]
    normalized_path: str
    workspace_root: str
```

### 6.2 关系约束

- 每轮循环生产 1 个 `TraceRecord`，追加到 `TraceStore`
- 每轮最多 1 个 `HITLRequest`（如果权限引擎返回 ask）
- `ToolResult` 经 `FeedbackSensor` 解析为 0 或 1 个 `Feedback`
- `PermissionRule` 与 `ScopeGuard` 联动：ScopeGuard 返回 outside/sensitive 时，PermissionPolicy 直接 deny

---

## 7. 领域与机制设计（A 类额外要求）

### 7.1 领域：Coding

Coding 领域的四个核心机制映射：

| 机制 | Coding 领域形态 | 实现方式 |
|------|----------------|----------|
| **动作/工具** | 读写文件、执行 shell、运行测试 | `ToolRegistry` + 5 个内建工具 + 插件扩展 |
| **客观反馈信号** | 测试运行结果（pass/fail/error）+ shell 退出码 | `FeedbackSensor` 解析 + 分类 + 结构化回灌 |
| **危险动作** | 越界写、危险 shell 命令、敏感文件访问 | `PermissionPolicy`（allow/ask/deny）+ `ScopeGuard`（路径围栏） |
| **记忆** | 会话内笔记 | 会话级 scratchpad（跨会话移到未来工作） |

### 7.2 重点维度：治理护栏 + 反馈闭环

**为什么选这两个维度做深：**

1. **天然由代码构成**：权限规则匹配、路径规范化、失败分类器都是确定性逻辑，与 A.4-(B) "机制必须是代码，不能是提示词"的要求最契合
2. **最易用 mock LLM 验证**：移除 LLM 后，`PermissionPolicy.check()` 和 `FeedbackSensor.classify()` 仍可独立测试，符合 A.4-(C) 的硬标准
3. **课程概念映射最强**：治理对应 agent-loop.html 中"权限门控/Guardrail"概念卡，反馈对应"反馈循环"概念卡

**治理护栏深度实现：**
- PermissionPolicy 三态引擎（allow/ask/deny），deny 优先级最高
- ScopeGuard 路径围栏（workspace root + 路径规范化 + 敏感文件 deny）
- HITL 状态机（pending → approved/denied/timed_out + 超时默认 deny）
- CLI 审批通道（WebUI 审批记录在 Agent Loop Theater 中回放展示）

**反馈闭环深度实现：**
- FeedbackSensor 多源解析（测试输出 / shell stderr）
- 失败分类（syntax / assertion / timeout / tool_error）
- 结构化 feedback 回灌（注入上下文，MockLLM 可据此选择预设动作）
- 自愈计数（记录修正次数，超限升级给人）

### 7.3 非重点维度（最低可运行实现）

- **决策/主循环**：基础的 while 循环 + 停机判断（核心但非深入方向）
- **记忆**：会话级 scratchpad（跨会话移到未来工作）
- **配置**：YAML → Pydantic 校验（最小实现）
- **插件**：5 基类 + 显式注册表 + 4 钩子 + entry_points 可选

---

## 8. 凭据与分发设计

### 8.1 凭据安全存储

```
存储层级（优先级递减）：
  1. 受部署平台保护的非空 OPENAI_API_KEY 运行时环境变量
  2. Windows Credential Manager (keyring)  ← 本机交互式使用首选
  3. .env 文件（明文回退，加入 .gitignore）

生命周期：
  录入：`agent-harness credentials update` 使用 CLI 隐藏输入（getpass）→ keyring.set_password
  使用：运行时环境变量 → keyring.get_password → .env → 未配置
  更新：同录入流程；不得把 key 作为命令行参数传入
  清除：`credentials clear` 默认需确认，或用 `--yes` 非交互确认；删除 keyring 与 .env 对应行
  查看：仅显示"状态：已配置 / 未配置"，不得回显明文
```

### 8.2 分发（v1 仅 Docker）

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY config ./config
RUN python -m pip install --no-cache-dir .
EXPOSE 8501
CMD ["streamlit", "run", "src/agent_harness/web/theater.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

```bash
docker build -t agent-harness .
docker run -p 8501:8501 -v agent-harness-data:/root/.agent-harness agent-harness
```

### 8.3 目标机 key 安全配置

```bash
# WebUI 不提供浏览器内 key 录入功能；先在目标机安全配置 secret。
# 本机 .env 为明文且必须被 Git 忽略；用 Docker 的 env-file 在运行时注入：
docker run --env-file .env -p 8501:8501 agent-harness
# 环境变量会对具有足够权限的本机进程可见，不能写入镜像层、Git 或命令历史。
```

---

## 9. 技术选型与理由

| 层面 | 选型 | 理由 |
|------|------|------|
| **核心语言** | Python 3.12 | 教学最友好；keyring 原生支持 Windows Credential Manager；mock 测试原生支持；dsv4flash 对 Python 标准库可靠性最高 |
| **WebUI** | Streamlit 单页面 | 纯 Python，API 极简单，dsv4flash 训练数据覆盖充分；trace 回放只读 JSONL，不依赖 session_state |
| **LLM 供应商** | OpenAI API | 兼容性最广，通过 LLMInterface 支持插件式切换 |
| **凭据管理** | keyring | 跨平台，原生支持 Windows Credential Manager |
| **配置** | PyYAML + Pydantic | schema 校验 + 自动补全 + 类型安全 |
| **测试** | pytest + mock | 确定性单元测试，mock LLM 不依赖网络 |
| **分发** | Docker | 覆盖"新机器零配置运行"检验；PyPI 移到未来工作 |
| **CI** | GitHub Actions | push 自动运行测试（含 unit-test job） |
| **权限模型** | allow/ask/deny 三态 | 参考 OpenCode permissions 与 Codex permissions，有真实工程出处 |

---

## 10. 验收标准

| 功能 | 验收标准 |
|------|----------|
| LLM 抽象层 | MockLLM 返回固定/预设响应，OpenAILLM 调用真实 API；单元测试覆盖两种实现 |
| Agent 主循环 | goal → agent_loop → done/MAX_STEPS → answer；mock LLM 可驱动完整循环 |
| 5 个工具 | 每个工具有至少一个单元测试覆盖正常路径和错误路径 |
| PermissionPolicy | 危险命令 deny、安全命令 allow、敏感操作 ask；deny 优先级最高；单元测试覆盖 |
| ScopeGuard | `..` 越界 deny、workspace 内 allow、敏感路径 deny；路径规范化正确 |
| FeedbackSensor | 测试成功/失败可正确解析；失败分类准确；结构化 feedback 正确回灌 |
| 自愈闭环 | 注入失败 → 分类 → 回灌 → MockLLM 选择预设动作 → 记录修正次数；确定性可重复 |
| TraceStore | 每轮 record 增量落盘；会话末 flush；JSONL 格式正确；中途崩溃可回放已记录部分 |
| 记忆系统 | 会话内 write_note → read_notes；单元测试覆盖 |
| 插件系统 | 实现 ToolPlugin 子类 → 注册 → 新工具出现；4 钩子触发正确；entry_points 可选 |
| 凭据管理 | 首次引导录入 → 查看状态 → 更新 → 清除；key 不泄露 |
| 机制演示 | ①权限拦截危险动作；②注入失败+反馈修正；③重点维度确定性行为 |
| Agent Loop Theater | 读取 trace.jsonl → 逐步回放 → 金色/蓝色可视化正确 |
| 分发 | `docker build && docker run` 可启动 |
| CI | `.gitlab-ci.yml` 含 `unit-test` job；最后一次 CI/CD pass |

---

## 11. 与主流实现的差距分析及亮点设计

### 11.1 差距分析 vs Codex CLI / OpenCode / Claude Code

| 维度 | 主流实现 | 本项目 | 处理策略 |
|------|---------|--------|----------|
| 沙箱隔离 | 容器/Docker 隔离执行 | ScopeGuard 路径围栏 | 做轻量版（路径规范化 + workspace root） |
| LSP 实时反馈 | 编辑后即时获取类型/语法错误 | 仅测试后反馈 | 不做（platform-specific，移到未来工作） |
| Git 集成 | 自动 commit、checkpoint、diff 回滚 | 无 | 移到未来工作（文件快照） |
| 多模型分工 | 强模型决策 + 弱模型压缩/分类 | 单一模型 | 不做（非评分核心） |
| 并发子 agent | 并行 fan-out | 仅串行 | 不做（dsv4flash 调试不可靠） |
| Token 预算 | 精细 cost/budget 控制 | 基础 MAX_STEPS | 做基础版 |
| Prompt caching | 缓存重复上下文 | 无 | 不做 |
| 权限模型 | allow/ask/deny 三态 | ✓ 实现 | **作为亮点，参考 OpenCode/Codex** |
| 路径围栏 | workspace root + sandbox | ✓ 实现 | **作为亮点** |
| trace 回放 | 决策轨迹 + 状态快照 | ✓ 实现 | **TraceStore + Agent Loop Theater 作为亮点** |

### 11.2 三个"让评审老师眼前一亮"的设计

**① PermissionPolicy + ScopeGuard 联动（治理维度）**

```
动作识别 → 路径规范化 → workspace 边界检查 → 敏感文件检查 → allow/ask/deny
```

这回答了"治理边界如何用代码实现"。参考 OpenCode 与 Codex 的真实权限模型，有工程出处，可确定性单测。

**② 确定性自愈闭环（反馈维度）**

```
测试失败 → FeedbackSensor 分类 → 结构化 feedback 回灌 → MockLLM 选择预设动作 → 记录修正次数
```

这直接对应 agent-loop.html 中"反馈循环"概念卡。关键在于：移除真实 LLM 后，这条链路仍可用确定性单测验证，每次运行结果相同。

**③ Agent Loop Theater（可观测性）**

运行 demo 生成 trace.jsonl，Streamlit 读取并逐步回放。每步用金色高亮 LLM 的"那一行"决策，用蓝色显示 harness 执行的"其余所有行"。评审老师打开 WebUI 的第一眼就能看到 $Agent = LLM \times Harness$ 这个命题在运转。这直接呼应课件 agent-loop.html 的"逐步展开 agent 一生"。

---

## 12. 风险与未决问题

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| dsv4flash 生成复杂异步代码不可靠 | 高级特性可能无法实现 | 全程同步实现；所有代码避免 async；重点逻辑用 mock 测试 |
| Windows Credential Manager 跨平台兼容 | Linux/macOS 用户需适配 | keyring 库已抽象；.env 回退覆盖所有平台 |
| Streamlit 回放性能 | 大 trace 文件加载慢 | JSONL 增量读取；100 轮以内即时加载 |
| mock-LLM 测试覆盖不全 | 核心机制未验证 | 每个核心模块至少 3 个测试用例（正常/边界/错误） |
| 插件 entry_points 发现不可靠 | dsv4flash 对 importlib.metadata 覆盖不足 | 显式注册为主路径；entry_points 为可选增强，带配置开关 |
| WebUI 部署成本 | 免费额度可能不足 | 优先 Docker 本地运行；部署选 Render 免费计划 |
