# DataWorks 数据开发 Skill — 设计文档

## 1. 定位

这是一个面向**数据开发人员**的 skill，让他们在 AI 编码工具（Claude Code、OpenClaw、Copaw、Codex、Qwen Code）中通过自然语言完成 DataWorks 上的数据开发工作。

用户说"帮我建一个每天凌晨跑的 ETL 节点"，AI 直接执行 DataWorks API 创建节点，返回"已创建节点 xxx，ID: yyy"。**不是生成脚本让用户自己跑。**

## 2. 核心设计原则

### 2.1 AI 是执行者，不是代码生成器

传统的 API 文档 skill 输出的是代码片段，用户还得复制粘贴去运行。本 skill 要求 AI 直接在终端执行操作并返回业务结果：

```
用户: "帮我创建一个清洗订单数据的节点，每天3点跑"
AI:   [在终端执行 Python 调用 CreateNode API]
AI:   "已创建节点 dwd_orders_clean (ID: 860438xxxx)，调度时间每天 03:00"
```

### 2.2 模板优先，不从自然语言直接生成 FlowSpec

FlowSpec 是 DataWorks 用来描述节点/工作流的 JSON 格式，字段繁多、枚举值严格、不同节点类型结构差异大。让 AI 从自然语言直接拼 JSON 极易出错。

正确做法：**检索 → 模板 → 约束填充 → 校验 → 执行**

```
用户需求
  ↓
受控枚举 (catalog/node_types.yaml) → 确定节点类型
  ↓
黄金模板 (templates/*.json) → 获取已知正确的 JSON 骨架
  ↓
SpecPatcher (scripts/patcher.py) → 只填充业务变量（名称、SQL、cron 等）
  ↓
SpecValidator (scripts/validator.py) → 三层校验
  ↓
调用 DataWorks API → 返回结果
```

### 2.3 主动确认关键信息

数据开发人员说的是业务语言，不是 API 参数。AI 需要把业务需求映射到 API 参数，缺少的信息主动询问：

| 业务语言 | 对应参数 | 需要确认 |
|---------|---------|---------|
| "我的项目" | `project_id` | 必须 |
| "上海 region" | `endpoint` | 默认 cn-shanghai |
| "每天3点跑" | `trigger.cron` = `00 00 03 * * ?` | AI 可推断 |
| "ODPS 数据源" | `datasource.name` | 需要确认具体名称 |
| "默认资源组" | `runtimeResource.resourceGroup` | 需要确认 |

## 3. 架构设计

### 3.1 文件结构

```
dataworks-dev/
├── SKILL.md                        # 入口：场景映射 + 工作流程 + API 示例
├── catalog/
│   └── node_types.yaml             # 受控枚举：27 种常用节点类型
├── templates/                      # 黄金模板（建议从 DataWorks 控制台导出替换）
│   ├── ODPS_SQL.json               # MaxCompute SQL 节点
│   ├── DIDE_SHELL.json             # Shell 脚本节点
│   ├── VIRTUAL.json                # 虚拟节点
│   └── CycleWorkflow.json          # 周期工作流
├── scripts/
│   ├── patcher.py                  # SpecPatcher — 模板填充 + 增量 Patch + 工作流组装
│   └── validator.py                # SpecValidator — 结构校验 + 模板校验 + 回归校验
├── references/
│   ├── api-reference.md            # 所有 API 参数 / 响应结构
│   ├── node-types.md               # Code Model 分类 / 特殊字段 / 详细示例
│   ├── flowspec-schema.md          # 完整 FlowSpec Schema（从 dataworks-spec 源码提取）
│   └── node-types-catalog.md       # 100+ 节点类型完整目录
└── evals/
    └── evals.json                  # 测试用例
```

### 3.2 各层职责

| 层 | 文件 | 职责 | AI 何时读取 |
|----|------|------|-----------|
| 入口层 | `SKILL.md` | 场景映射、工作流程、常用 API 示例 | 每次触发 skill 时 |
| 枚举层 | `catalog/node_types.yaml` | 节点类型受控列表，防止 AI 猜测 | 需要确定节点类型时 |
| 模板层 | `templates/*.json` | 已知正确的 FlowSpec JSON 骨架 | 创建新节点/工作流时 |
| 工具层 | `scripts/patcher.py` `scripts/validator.py` | 模板填充、增量更新、校验 | 每次生成/修改 FlowSpec 时 |
| 参考层 | `references/*.md` | 深度参考（完整 schema、100+ 节点类型） | 遇到不常见节点类型时 |

### 3.3 信息分层（渐进加载）

```
SKILL.md (~800行)          ← 每次都加载，覆盖 80% 场景
  ↓ 按需
catalog/node_types.yaml     ← 确定节点类型时
templates/*.json            ← 生成 FlowSpec 时
  ↓ 深度参考
references/node-types.md    ← 遇到 EMR/DI/Flink 等复杂节点时
references/flowspec-schema.md ← 需要完整字段定义时
references/node-types-catalog.md ← 需要不常见节点的 command 值时
references/api-reference.md ← 需要 API 参数细节时
```

## 4. FlowSpec 生成策略

### 4.1 为什么不能直接生成

FlowSpec 有以下容易出错的点：

1. **`runtime.command` 值严格** — `ODPS_SQL` 不是 `odps_sql`，`CONTROLLER_CYCLE` 不是 `CONTROLLER_DO_WHILE`
2. **不同节点的 content 格式不同** — ODPS SQL 是纯 SQL 文本，EMR 是 EmrCode JSON（SQL 在 `properties.arguments[0]` 里），DI 是复杂 JSON 配置
3. **必填字段因节点类型而异** — ODPS SQL 需要 `datasource`，Shell 不需要；Branch 需要 `branch.branches`，普通节点不需要
4. **枚举值大小写敏感** — `recurrence: "Normal"` 不是 `"normal"`，`instanceMode: "T+1"` 不是 `"t+1"`

### 4.2 content_format 分类

这是最关键的设计决策之一。不同节点的 `script.content` 结构完全不同：

| content_format | 含义 | 代表节点 |
|---------------|------|---------|
| `plain_text` | content 是纯代码文本 | ODPS_SQL, DIDE_SHELL, PYTHON, MySQL, Hologres |
| `emr_json` | content 是 EmrCode JSON | EMR_HIVE, EMR_SPARK, EMR_SHELL |
| `di_json` | content 是数据集成配置 JSON | DI, RI |
| `controller` | 无 content，用节点顶层特殊字段 | VIRTUAL, BRANCH, JOIN, CYCLE, TRAVERSE |
| `spark_json` | content 是 Spark 配置 JSON | ODPS_SPARK |
| `complex_json` | 其他复杂 JSON | FLINK_SQL_STREAM, PAI_FLOW |
| `none` | 无 content | VIRTUAL |

**原则：`plain_text` 类型可以从模板生成，其他类型必须从 DataWorks 控制台导出模板或从已有节点 Fetch-and-Patch。**

### 4.3 三种生成模式

**模式 A：模板创建（适用于 plain_text 节点）**
```
SpecPatcher.create_node('ODPS_SQL', {业务变量}) → FlowSpec
```

**模式 B：Fetch-and-Patch（适用于复杂节点如 DI/Flink/PAI）**
```
GetNode(已有节点) → 现有 Spec → SpecPatcher.patch_existing_node(changes) → 新 Spec
```

**模式 C：工作流组装**
```
多个节点 Spec + 依赖关系 → SpecPatcher.assemble_workflow() → 工作流 Spec
```

## 5. 关键工具设计

### 5.1 SpecPatcher

| 方法 | 用途 |
|------|------|
| `create_node(type, vars)` | 从模板 + `{{placeholder}}` 替换生成新节点 |
| `create_update_patch(existing, changes)` | 生成最小增量更新 Patch（只含变更字段） |
| `patch_existing_node(existing, changes)` | 在完整 Spec 上做 AST 级修改 |
| `assemble_workflow(nodes, deps, id_policy)` | 组装工作流 + 管理 ID 策略 |

**ID 策略**（用于 ImportWorkflowDefinition）：
- `omit_for_create` — 删除所有 id，让服务端生成（新建场景）
- `reuse_existing` — 保留已有 id（更新场景）
- `use_name_as_id` — 用 name 作为临时 id（用于 flow 依赖引用）

### 5.2 SpecValidator

三层校验：

| 层 | 检查内容 | 错误示例 |
|----|---------|---------|
| 结构校验 | version/kind/spec/nodes 是否存在且类型正确 | 缺少 `spec` 字段 |
| 模板校验 | 必填字段、枚举值是否合法 | `runtime.command` 值不在合法列表中 |
| 回归校验 | 更新 Patch 是否只改了允许的字段 | Patch 里意外包含了 `id` 字段 |

### 5.3 模板系统

模板是带 `{{placeholder}}` 占位符的 FlowSpec JSON，来源有两种：

1. **skill 自带** — `templates/` 目录下的 ODPS_SQL.json、DIDE_SHELL.json 等，覆盖最常用场景
2. **用户从控制台导出** — 在 DataWorks 控制台创建最小节点 → "显示 Spec" → 保存为 JSON → 替换到 `templates/`

用户导出的模板更准确，因为包含了用户环境的真实配置（数据源名、资源组 ID 等）。

## 6. 数据来源与准确性

### 6.1 FlowSpec Schema

从 https://github.com/aliyun/dataworks-spec 的 Java 源码中提取：

- **类层次** — `Specification<DataWorksWorkflowSpec>` → `SpecNode` → `SpecScript` → `SpecScriptRuntime`
- **所有枚举** — `SpecKind`（18 种）、`TriggerType`（5 种）、`DependencyType`（4 种）、`VariableType`（6 种）等
- **100+ 节点类型** — `CodeProgramType` 枚举的完整列表，含 code、language、extension
- **引擎特定配置** — `emrJobConfig`、`flinkConf`、`sparkConf`、`maxComputeConf` 等

### 6.2 API 参数

从 https://api.aliyun.com/meta/v1/products/dataworks-public/versions/2024-05-18/apis/ 提取：

- **CreateNode**: `ProjectId`(int64), `ContainerId`(string), `Scene`(string), `Spec`(string)
- **CreatePipelineRun**: `ProjectId`(int64), `Type`(`Online`/`Offline`), `ObjectIds`(string[])
- **ImportWorkflowDefinition**: 异步 API，返回 `AsyncJob`，需轮询 `GetJobStatus`

### 6.3 关键修正记录

在研究过程中发现并修正了多个常见错误认知：

| 错误 | 正确 |
|------|------|
| Scene 值是 `DATAWORKS_STANDARD_MODE` | `DATAWORKS_PROJECT` / `DATAWORKS_MANUAL_WORKFLOW` / `DATAWORKS_MANUAL_TASK` |
| CreatePipelineRun 用 `PipelineId` + `EntityIds` | 用 `Type`(`Online`/`Offline`) + `ObjectIds` |
| CreateWorkflowDefinition 创建工作流和节点 | 只创建工作流壳，节点需单独创建或用 ImportWorkflowDefinition |
| EMR 节点的 content 是纯 SQL | content 是 EmrCode JSON，SQL 在 `properties.arguments[0]` |
| 控制流节点用 `CONTROLLER_DO_WHILE` | 用 `CONTROLLER_CYCLE`（code: 1103） |
| 控制流节点用 `CONTROLLER_FOREACH` | 用 `CONTROLLER_TRAVERSE`（code: 1106） |

## 7. 跨平台兼容

当前以 Claude Code 的 SKILL.md 格式交付。核心内容（SDK 调用、模板、Patcher、Validator）是标准 Python，不依赖任何特定 AI 工具的功能，因此：

- **Claude Code** — 直接作为 skill 加载
- **OpenClaw / Copaw / Qwen Code** — 将 SKILL.md 内容作为 system prompt 或自定义指令加载
- **Codex** — 作为 AGENTS.md 或任务指令加载
- **任何有终端访问的 AI 工具** — 只要能执行 `pip install` 和 `python3 -c ...`，就能用

## 8. Eval 测试设计

### 8.1 测试原则

- **用数据开发人员的业务语言**，不是 API 术语
- **验证 AI 是否直接执行**，而不是生成脚本
- **静态检查**生成代码的结构正确性（无真实账号时）
- **端到端测试**（有真实账号时）实际调用 API 验证

### 8.2 Iteration 1 → 2 结果

| 指标 | Iter-1 with_skill | Iter-2 with_skill | 变化 |
|------|-------------------|-------------------|------|
| 通过率 | 97% | 100% | +3% |
| Token 开销倍数 | 3.2x | 1.7x | 降低 47% |
| 主要改进 | — | description 面向场景、业务语言 prompt | — |

with_skill vs without_skill 核心差异：
- **Eval 1**（创建节点）：without_skill 缺少 `scene=DATAWORKS_PROJECT`，不用模板/校验
- **Eval 2**（列出+发布）：Iteration-1 without_skill 用了错误的 `CreateDeployment` API
- **Eval 3**（构建管道）：两者都能完成，但 with_skill 使用了 SpecPatcher + SpecValidator
