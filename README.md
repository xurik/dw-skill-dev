# DataWorks 数据开发 Skill

通过 AI 编码工具（Claude Code、OpenClaw、Copaw、Codex、Qwen Code）完成阿里云 DataWorks 上的数据开发工作。

用户说"帮我建一个每天跑的 ETL 节点"，AI 直接执行 DataWorks API 并返回结果 —— 不是生成脚本。

## 能做什么

| 场景 | 典型用户说法 |
|------|-------------|
| 创建 ETL 节点 | "帮我建一个每天3点跑的 SQL 清洗节点" |
| 构建数据管道 | "建一个 ODS→DWD→DWS 的管道" |
| 修改调度/SQL | "把这个节点改成每小时跑" |
| 发布上线 | "把开发的节点发到生产" |
| 查看节点 | "项目里有哪些 dwd 节点？" |
| 管理 UDF/资源 | "注册一个解析 JSON 的 UDF" |

## 项目结构

```
dataworks-dev/
├── SKILL.md                    # 入口：场景映射 + 工作流 + API 示例
├── DESIGN.md                   # 设计文档
├── catalog/
│   └── node_types.yaml         # 节点类型受控枚举（27 种）
├── templates/                  # FlowSpec 黄金模板
│   ├── ODPS_SQL.json
│   ├── DIDE_SHELL.json
│   ├── VIRTUAL.json
│   └── CycleWorkflow.json
├── scripts/
│   ├── patcher.py              # SpecPatcher — 模板填充 / 增量 Patch / 工作流组装
│   └── validator.py            # SpecValidator — 三层校验
├── references/
│   ├── api-reference.md        # API 参数与响应
│   ├── node-types.md           # Code Model 分类与示例
│   ├── flowspec-schema.md      # 完整 FlowSpec Schema
│   └── node-types-catalog.md   # 100+ 节点类型目录
└── evals/
    └── evals.json              # 测试用例
```

## 核心设计

1. **模板优先** — 从 `templates/` 的黄金模板出发，用 `SpecPatcher` 填充业务变量，不从自然语言直接拼 FlowSpec
2. **受控枚举** — 节点类型必须从 `catalog/node_types.yaml` 选取，防止 AI 猜测错误的 `runtime.command`
3. **三层校验** — `SpecValidator` 在调 API 前做结构校验→模板校验→回归校验
4. **直接执行** — AI 在终端调用 DataWorks API 并返回业务结果，不输出脚本文件

## 使用前提

```bash
pip install alibabacloud_dataworks_public20240518
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-ak>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-sk>
```

## 技术细节

- **SDK**: `alibabacloud_dataworks_public20240518`（API 2024-05-18）
- **FlowSpec Schema**: 从 [dataworks-spec](https://github.com/aliyun/dataworks-spec) Java 源码提取
- **支持 100+ 节点类型**: MaxCompute、EMR、Hologres、Flink、数据库 SQL、控制流、数据集成、PAI 等

详见 [DESIGN.md](dataworks-dev/DESIGN.md)。
