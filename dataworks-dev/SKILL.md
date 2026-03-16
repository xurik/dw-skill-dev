---
name: dataworks-dev
description: >
  DataWorks 数据开发能力。帮助数据开发人员通过 AI 编码工具完成 DataWorks 上的数据开发工作。
  使用场景包括但不限于：创建 ETL 数据管道、构建数仓分层（ODS→DWD→DWS→ADS）、配置定时调度、
  管理节点依赖关系、发布上线、管理 UDF 函数和文件资源。当用户提到以下任何内容时触发此 skill：
  DataWorks、数据开发、数据管道、ETL、调度节点、工作流、发布部署、MaxCompute/ODPS SQL、
  数仓建设、离线开发、数据集成、FlowSpec、或任何涉及在 DataWorks 平台上进行数据开发的需求。
  即使用户没有明确提到 DataWorks，只要描述的是阿里云上的数据开发/数仓工作，也应触发此 skill。
---

# DataWorks 数据开发 Skill

帮助数据开发人员通过 AI 编码工具（Claude Code、OpenClaw、Copaw、Codex、Qwen Code 等）完成 DataWorks 上的数据开发工作。通过 `alibabacloud_dataworks_public20240518` SDK（API 2024-05-18）实现。

## 你能帮用户做什么

| 场景 | 对应操作 | 典型用户说法 |
|------|---------|-------------|
| 创建 ETL 节点 | CreateNode + FlowSpec | "帮我建一个每天跑的 SQL 节点" |
| 构建数据管道 | ImportWorkflowDefinition | "我要建一个 ODS→DWD→DWS 的管道" |
| 修改调度/SQL | UpdateNode (增量 Patch) | "把这个节点改成每小时跑" |
| 发布上线 | CreatePipelineRun | "帮我把开发的节点发到生产" |
| 查看节点列表 | ListNodes | "看看项目里有哪些 dwd 节点" |
| 注册 UDF 函数 | CreateFunction | "帮我注册一个解析 JSON 的 UDF" |
| 上传文件资源 | CreateResource | "把这个 JAR 包上传到 DataWorks" |
| 管理组件 | CreateComponent | "做一个可复用的 ETL 模板" |
| 下线节点 | CreatePipelineRun(Offline) | "把这个节点下线" |
| 查看依赖 | ListNodeDependencies | "这个节点依赖了哪些上游？" |

### 工作流程

**你是执行者，不是代码生成器。** 用户说"帮我创建一个节点"，你应该直接创建并告诉他结果，而不是给他一个脚本让他自己跑。

当用户描述数据开发需求时，按以下步骤处理：

1. **理解需求** — 用户要创建/修改/发布什么？涉及哪些节点类型？
2. **确认关键信息** — 如果用户没提供，主动询问：
   - `project_id`（工作空间 ID）
   - `region`（地域，默认 cn-shanghai）
   - 数据源名称（如 `odps_first`）
   - 资源组（如 `S_res_group_xxx`）
   - 调度时间（cron 表达式）
3. **确保环境就绪** — 检查 SDK 和凭证（见下方"环境准备"）
4. **从模板生成 FlowSpec** — 使用 `SpecPatcher` + 模板，不要从头编写
5. **校验** — 使用 `SpecValidator` 校验
6. **直接执行 API 调用** — 在终端运行 Python 代码调用 DataWorks API
7. **返回业务结果** — 告诉用户"已创建节点 xxx，ID: yyy，调度时间每天3点"

### 环境准备

每次执行前，先确保环境就绪：

**第一步：检查 SDK**
```bash
pip show alibabacloud_dataworks_public20240518 2>/dev/null || pip install alibabacloud_dataworks_public20240518
```

**第二步：检查凭证**
```bash
echo $ALIBABA_CLOUD_ACCESS_KEY_ID | head -c 4
```
如果为空，提示用户配置：
```
请先配置阿里云凭证：
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-ak>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-sk>
```
也支持 `~/.aliyun/config.json` 或 ECS 实例角色自动获取。

**第三步：初始化客户端**
```python
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi.models import Config
from alibabacloud_dataworks_public20240518.client import Client

credential_client = CredentialClient()
config = Config(
    credential=credential_client,
    endpoint='dataworks.<region>.aliyuncs.com'
)
client = Client(config)
```

**Endpoint format**: `dataworks.<region>.aliyuncs.com`
Common regions: `cn-shanghai`, `cn-beijing`, `cn-hangzhou`, `cn-shenzhen`, `cn-chengdu`, `ap-southeast-1`

**Security**: Never hardcode credentials. Use the Alibaba Cloud credential chain:
```python
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi.models import Config

# Auto-detect: env vars → OIDC → ~/.aliyun/config.json → ECS metadata
credential_client = CredentialClient()
config = Config(
    credential=credential_client,
    endpoint=f"dataworks.{os.environ.get('DATAWORKS_REGION', 'cn-shanghai')}.aliyuncs.com"
)
```

Environment variables: `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET`

## Core Concept: FlowSpec

Most create/update APIs accept a `Spec` parameter in **FlowSpec** format — a JSON structure that describes nodes, scripts, triggers, and dependencies.

### FlowSpec 生成原则

**不要从自然语言直接生成完整的 FlowSpec JSON。** 正确的做法是 "检索 + 模板 + 约束填充 + 验证"：

1. **受控枚举**：节点类型必须从 `catalog/node_types.yaml` 中选取，不允许自由猜测 `runtime.command` 值
2. **黄金模板**：每种节点类型在 `templates/` 目录有最小可用的 Spec 模板（最好来自 DataWorks 控制台"显示 Spec"导出）
3. **只填业务变量**：创建时从模板出发，只填写用户关心的字段（名称、SQL内容、cron、资源组、依赖），不重造结构
4. **增量 Patch 更新**：更新时先用 GetNode 读取现有 Spec，只修改目标字段，保留其他所有原始字段
5. **ID 策略受控**：ImportWorkflowDefinition 中，ID 存在则更新、不存在则创建，必须明确选择 `omit_for_create` / `reuse_existing`
6. **三层校验**：结构校验（version/kind/spec）→ 模板校验（必填字段/枚举值）→ 回归校验（diff 对比）

### Skill 提供的工具

| 文件 | 用途 |
|------|------|
| `catalog/node_types.yaml` | 节点类型受控枚举，含 command、语言、content 格式、必填字段、用户可填字段 |
| `templates/*.json` | 每种节点的最小可用 FlowSpec 模板（用户应从控制台导出替换） |
| `scripts/patcher.py` | SpecPatcher — 模板填充、增量 Patch、工作流组装 |
| `scripts/validator.py` | SpecValidator — 三层校验 |
| `references/node-types.md` | 节点类型完整分类、Code Model 说明、特殊字段参考 |
| `references/api-reference.md` | 所有 API 的参数和响应结构 |

### 使用 SpecPatcher 生成 FlowSpec

```python
import sys, json
sys.path.insert(0, '<skill_path>/scripts')
from patcher import SpecPatcher

patcher = SpecPatcher(templates_dir='<skill_path>/templates')

# 创建：从模板填充业务变量
spec = patcher.create_node('ODPS_SQL', {
    'node_name': 'daily_report',
    'script_path': '业务流程/report/daily_report',
    'sql_content': "INSERT OVERWRITE TABLE rpt SELECT * FROM ods WHERE dt='${bizdate}';",
    'cron_expression': '00 00 06 * * ?',
    'datasource_name': 'odps_first',
    'resource_group': 'S_res_group_xxx',
    'input_dependency': 'project_root',
    'output_name': 'project.daily_report',
})

# 增量更新：只改变的字段
patch = patcher.create_update_patch(existing_spec, {
    'script.content': 'SELECT count(*) FROM t;',
    'trigger.cron': '00 30 07 * * ?',
})

# 工作流组装
wf = patcher.assemble_workflow(
    node_specs=[node_a_spec, node_b_spec],
    flow_deps=[{'nodeId': 'transform', 'depends': [{'nodeId': 'extract', 'type': 'Normal'}]}],
    id_policy='use_name_as_id',
)
```

### 使用 SpecValidator 校验

```python
from validator import SpecValidator

validator = SpecValidator()
errors = validator.validate(spec)
for e in errors:
    print(f"[{e['level']}] {e['message']}")
# 空列表 = 校验通过
```

### 如何补充新节点模板

用户环境的模板应该从 DataWorks 控制台导出：
1. 在控制台创建目标类型的最小节点
2. 点击"显示 Spec"按钮导出完整 JSON
3. 保存到 `templates/<COMMAND>.json`（如 `templates/EMR_HIVE.json`）
4. 在 `catalog/node_types.yaml` 中添加对应条目

Read `references/node-types.md` for the complete node type classification and Code Model details.

### FlowSpec Structure for a Node

```json
{
  "version": "1.1.0",
  "kind": "Node",
  "spec": {
    "nodes": [
      {
        "name": "my_sql_task",
        "recurrence": "Normal",
        "timeout": 0,
        "instanceMode": "T+1",
        "rerunMode": "Allowed",
        "rerunTimes": 3,
        "rerunInterval": 180000,
        "datasource": {
          "name": "odps_first"
        },
        "script": {
          "path": "业务流程/数据开发/my_sql_task",
          "runtime": {
            "command": "ODPS_SQL"
          },
          "content": "SELECT * FROM my_table WHERE dt = '${bizdate}';"
        },
        "trigger": {
          "type": "Scheduler",
          "cron": "00 00 02 * * ?",
          "startTime": "1970-01-01 00:00:00",
          "endTime": "9999-01-01 00:00:00",
          "timezone": "Asia/Shanghai",
          "delaySeconds": 0
        },
        "runtimeResource": {
          "resourceGroup": "S_res_group_xxx_xxx"
        },
        "inputs": {
          "nodeOutputs": [
            {
              "data": "project_root",
              "artifactType": "NodeOutput"
            }
          ]
        },
        "outputs": {
          "nodeOutputs": [
            {
              "data": "project.my_sql_task",
              "artifactType": "NodeOutput",
              "refTableName": "my_sql_task"
            }
          ]
        }
      }
    ]
  }
}
```

### Key FlowSpec Fields

| Field | Description |
|-------|-------------|
| `version` | Always `"1.1.0"` |
| `kind` | `"Node"` for single nodes, `"CycleWorkflow"` for scheduled workflows, `"ManualWorkflow"` for manual workflows |
| `recurrence` | `"Normal"` (standard schedule), `"Pause"` (paused), `"Skip"` (skip execution) |
| `instanceMode` | `"T+1"` (next-day instance), `"Immediately"` (immediate) |
| `rerunMode` | `"Allowed"`, `"FailureAllowed"` (only on failure), `"Denied"` |
| `script.runtime.command` | Engine type: `"ODPS_SQL"`, `"SHELL"`, `"PYTHON"`, `"EMR_HIVE"`, `"EMR_SPARK"`, `"DIDE_SHELL"`, `"CDH_HIVE"`, etc. |
| `trigger.cron` | Cron expression, e.g. `"00 00 02 * * ?"` = daily at 02:00 |
| `trigger.type` | `"Scheduler"` (scheduled) or `"Manual"` |

### FlowSpec for Workflows

```json
{
  "version": "1.1.0",
  "kind": "CycleWorkflow",
  "metadata": {
    "owner": "user_id",
    "description": "Daily ETL pipeline"
  },
  "spec": {
    "nodes": [ ... ],
    "scripts": [ ... ],
    "triggers": [ ... ],
    "runtimeResources": [ ... ],
    "flow": [
      {
        "nodeId": "node_b",
        "depends": [
          { "nodeId": "node_a", "type": "Normal" }
        ]
      }
    ]
  }
}
```

## API Quick Reference

Read `references/api-reference.md` for complete parameter details of every API.

Below is a concise guide to the most common operations.

### Nodes (节点)

Nodes are the core unit of data development — each node represents a schedulable task (SQL, Shell, Python, etc.).

**Create a node:**
```python
from alibabacloud_dataworks_public20240518.models import CreateNodeRequest
import json

spec = {
    "version": "1.1.0",
    "kind": "Node",
    "spec": {
        "nodes": [{
            "name": "daily_report",
            "recurrence": "Normal",
            "timeout": 0,
            "instanceMode": "T+1",
            "rerunMode": "Allowed",
            "rerunTimes": 3,
            "rerunInterval": 180000,
            "datasource": {"name": "odps_first"},
            "script": {
                "path": "业务流程/report/daily_report",
                "runtime": {"command": "ODPS_SQL"},
                "content": "INSERT OVERWRITE TABLE rpt_daily SELECT * FROM ods_raw WHERE dt='${bizdate}';"
            },
            "trigger": {
                "type": "Scheduler",
                "cron": "00 00 06 * * ?",
                "startTime": "1970-01-01 00:00:00",
                "endTime": "9999-01-01 00:00:00",
                "timezone": "Asia/Shanghai"
            },
            "runtimeResource": {"resourceGroup": "S_res_group_xxx"},
            "inputs": {
                "nodeOutputs": [{"data": "project_root", "artifactType": "NodeOutput"}]
            },
            "outputs": {
                "nodeOutputs": [{"data": "project.daily_report", "artifactType": "NodeOutput"}]
            }
        }]
    }
}

request = CreateNodeRequest(
    project_id=12345,
    scene='DATAWORKS_PROJECT',
    spec=json.dumps(spec)
)
response = client.create_node(request)
node_id = response.body.id
```

**Scene values:**
- `DATAWORKS_PROJECT` — create in project directory (standard scheduled nodes)
- `DATAWORKS_MANUAL_WORKFLOW` — create inside a manual workflow (requires `container_id`)
- `DATAWORKS_MANUAL_TASK` — create as manual task

**Get node details:**
```python
from alibabacloud_dataworks_public20240518.models import GetNodeRequest

request = GetNodeRequest(id='860438872620113xxxx')
response = client.get_node(request)
node = response.body.node
print(f"Name: {node.name}, Owner: {node.owner}")
# node.spec contains the FlowSpec JSON string
```

**List nodes (with pagination):**
```python
from alibabacloud_dataworks_public20240518.models import ListNodesRequest

request = ListNodesRequest(
    project_id=12345,
    page_number=1,
    page_size=50,
    name='daily'  # fuzzy match
)
response = client.list_nodes(request)
for node in response.body.paging_info.nodes:
    print(f"{node.id}: {node.name}")
```

**Update a node (incremental update via FlowSpec):**
```python
from alibabacloud_dataworks_public20240518.models import UpdateNodeRequest

# Only include fields you want to change
update_spec = {
    "version": "1.1.0",
    "kind": "Node",
    "spec": {
        "nodes": [{
            "script": {
                "content": "SELECT count(*) FROM my_table WHERE dt='${bizdate}';"
            },
            "trigger": {
                "cron": "00 30 07 * * ?"
            }
        }]
    }
}

request = UpdateNodeRequest(
    id='860438872620113xxxx',
    project_id=12345,
    spec=json.dumps(update_spec)
)
client.update_node(request)
```

**Delete / Move / Rename:**
```python
from alibabacloud_dataworks_public20240518.models import (
    DeleteNodeRequest, MoveNodeRequest, RenameNodeRequest
)

# Delete
client.delete_node(DeleteNodeRequest(id='xxx', project_id=12345))

# Move to new path
client.move_node(MoveNodeRequest(id='xxx', project_id=12345, path='业务流程/新目录/node_name'))

# Rename
client.rename_node(RenameNodeRequest(id='xxx', project_id=12345, name='new_name'))
```

**List node dependencies:**
```python
from alibabacloud_dataworks_public20240518.models import ListNodeDependenciesRequest

request = ListNodeDependenciesRequest(
    id='860438872620113xxxx',
    project_id=12345,
    page_number=1,
    page_size=50
)
response = client.list_node_dependencies(request)
for dep in response.body.paging_info.nodes:
    print(f"Depends on: {dep.id} ({dep.name})")
```

### Workflows (工作流)

Workflows group multiple nodes with dependency relationships.

**Create a workflow:**
```python
from alibabacloud_dataworks_public20240518.models import CreateWorkflowDefinitionRequest

spec = {
    "version": "1.1.0",
    "kind": "CycleWorkflow",
    "metadata": {
        "owner": "owner_id",
        "description": "Daily ETL pipeline"
    },
    "spec": {
        "nodes": [],
        "flow": []
    }
}

request = CreateWorkflowDefinitionRequest(
    project_id=12345,
    spec=json.dumps(spec)
)
response = client.create_workflow_definition(request)
workflow_id = response.body.id
```

**Import a workflow (with nodes and dependencies):**

This is an **async API** — it returns an `AsyncJob` object. Poll `GetJobStatus` to check completion.

```python
from alibabacloud_dataworks_public20240518.models import (
    ImportWorkflowDefinitionRequest, GetJobStatusRequest
)
import time

# Full workflow definition with embedded nodes
spec = {
    "version": "1.1.0",
    "kind": "CycleWorkflow",
    "spec": {
        "nodes": [
            {"id": "node_a", "name": "extract", "script": {"runtime": {"command": "ODPS_SQL"}, "content": "..."}},
            {"id": "node_b", "name": "transform", "script": {"runtime": {"command": "ODPS_SQL"}, "content": "..."}}
        ],
        "flow": [
            {"nodeId": "node_b", "depends": [{"nodeId": "node_a", "type": "Normal"}]}
        ]
    }
}

request = ImportWorkflowDefinitionRequest(
    project_id=12345,
    spec=json.dumps(spec)
)
response = client.import_workflow_definition(request)
job_id = response.body.async_job.id

# Poll for completion (recommended interval: 1s, max 10 attempts)
for _ in range(10):
    time.sleep(1)
    job_resp = client.get_job_status(GetJobStatusRequest(job_id=job_id))
    job = job_resp.body.job_status
    if job.completed:
        if job.status == 'Success':
            workflow_id = job.response  # the created workflow ID
            print(f"Workflow imported: {workflow_id}")
        else:
            print(f"Import failed: {job.error}")
        break
```

**Get / List / Update / Delete / Move / Rename:**
```python
from alibabacloud_dataworks_public20240518.models import (
    GetWorkflowDefinitionRequest,
    ListWorkflowDefinitionsRequest,
    UpdateWorkflowDefinitionRequest,
    DeleteWorkflowDefinitionRequest,
    MoveWorkflowDefinitionRequest,
    RenameWorkflowDefinitionRequest,
)

# Get workflow details
resp = client.get_workflow_definition(GetWorkflowDefinitionRequest(id='xxx', project_id=12345))

# List workflows
resp = client.list_workflow_definitions(ListWorkflowDefinitionsRequest(
    project_id=12345, page_number=1, page_size=20
))

# Update (incremental FlowSpec)
client.update_workflow_definition(UpdateWorkflowDefinitionRequest(
    id='xxx', project_id=12345, spec=json.dumps(update_spec)
))

# Delete
client.delete_workflow_definition(DeleteWorkflowDefinitionRequest(id='xxx', project_id=12345))

# Move
client.move_workflow_definition(MoveWorkflowDefinitionRequest(
    id='xxx', project_id=12345, path='new/path'
))

# Rename
client.rename_workflow_definition(RenameWorkflowDefinitionRequest(
    id='xxx', project_id=12345, name='new_name'
))
```

### Pipeline Runs (发布流程)

Pipeline runs handle the deployment lifecycle — publishing development entities to production.

**Create a pipeline run:**
```python
from alibabacloud_dataworks_public20240518.models import CreatePipelineRunRequest

request = CreatePipelineRunRequest(
    project_id=12345,
    type='Online',  # 'Online' for deploy, 'Offline' for undeploy
    # Entity IDs to publish (max 10, only first entity + its children actually published)
    object_ids=['860438872620113xxxx'],
    description='Deploy daily report nodes'
)
response = client.create_pipeline_run(request)
pipeline_id = response.body.id
```

**Get pipeline run details:**
```python
from alibabacloud_dataworks_public20240518.models import GetPipelineRunRequest

request = GetPipelineRunRequest(id='xxx', project_id=12345)
response = client.get_pipeline_run(request)
run = response.body.pipeline_run
print(f"Status: {run.status}")
# Status values: Init, Running, Success, Fail, Termination, Cancel
# Check run.stages for detailed per-stage progress
```

**Execute a pipeline stage:**
```python
from alibabacloud_dataworks_public20240518.models import ExecPipelineRunStageRequest

# Stages must be executed in order — check GetPipelineRun for stage codes
request = ExecPipelineRunStageRequest(
    project_id=12345,
    id='pipeline_run_id',
    code='DEV_CHECK'  # stage code from GetPipelineRun
)
client.exec_pipeline_run_stage(request)
```

**List pipeline runs:**
```python
from alibabacloud_dataworks_public20240518.models import ListPipelineRunsRequest

request = ListPipelineRunsRequest(
    project_id=12345,
    page_number=1,
    page_size=20
)
response = client.list_pipeline_runs(request)
for run in response.body.paging_info.pipeline_runs:
    print(f"{run.id}: {run.status}")
```

**Abolish (terminate) a pipeline run:**
```python
from alibabacloud_dataworks_public20240518.models import AbolishPipelineRunRequest

client.abolish_pipeline_run(AbolishPipelineRunRequest(id='xxx', project_id=12345))
```

### Resources (文件资源)

File resources (JARs, Python files, text files) that nodes can reference.

```python
from alibabacloud_dataworks_public20240518.models import (
    CreateResourceRequest, GetResourceRequest,
    ListResourcesRequest, DeleteResourceRequest,
    UpdateResourceRequest, MoveResourceRequest, RenameResourceRequest
)

# Create a Python resource
spec = {
    "version": "1.1.0",
    "kind": "Resource",
    "spec": {
        "fileResources": [{
            "name": "my_script.py",
            "script": {
                "content": "",
                "path": "业务流程/资源/my_script.py",
                "runtime": {"command": "ODPS_PYTHON"}
            },
            "type": "python",
            "datasource": {"name": "odps_first", "type": "odps"}
        }]
    }
}
# resource_file can be an OSS URL or left empty for inline content
client.create_resource(CreateResourceRequest(
    project_id=12345, spec=json.dumps(spec)
))

# List resources
resp = client.list_resources(ListResourcesRequest(
    project_id=12345, page_number=1, page_size=50
))
```

### Functions (UDF函数)

User-defined functions registered in DataWorks.

```python
from alibabacloud_dataworks_public20240518.models import (
    CreateFunctionRequest, GetFunctionRequest,
    ListFunctionsRequest, DeleteFunctionRequest,
    UpdateFunctionRequest, MoveFunctionRequest, RenameFunctionRequest
)

# Create a UDF
spec = {
    "version": "1.1.0",
    "kind": "Function",
    "spec": {
        "functions": [{
            "name": "my_udf",
            "script": {
                "content": "{\"name\": \"my_udf\", \"datasource\": {\"type\": \"ODPS\", \"name\": \"odps_first\"}, \"runtimeResource\": {\"resourceGroup\": \"S_res_group_xxx\"}}",
                "path": "业务流程/函数/my_udf",
                "runtime": {"command": "ODPS_FUNCTION"}
            },
            "datasource": {"name": "odps_first", "type": "ODPS"},
            "runtimeResource": {"resourceGroup": "S_res_group_xxx"},
            "fileResources": [{"name": "my_udf.jar"}]
        }]
    }
}
client.create_function(CreateFunctionRequest(
    project_id=12345, spec=json.dumps(spec)
))

# List functions
resp = client.list_functions(ListFunctionsRequest(
    project_id=12345, page_number=1, page_size=50
))
```

### Components (组件)

Reusable task templates.

```python
from alibabacloud_dataworks_public20240518.models import (
    CreateComponentRequest, GetComponentRequest,
    ListComponentsRequest, DeleteComponentRequest, UpdateComponentRequest
)

# List components
resp = client.list_components(ListComponentsRequest(
    project_id=12345, page_number=1, page_size=50
))

# Get component details
resp = client.get_component(GetComponentRequest(id='xxx', project_id=12345))
```

## Common Patterns

### Fetch-and-Patch Pattern (for complex or DI nodes)

When templates/ doesn't have a matching template (e.g., DI, Flink, PAI), fetch an existing node from DataWorks and use `SpecPatcher` to modify it:

```python
import json
from patcher import SpecPatcher

patcher = SpecPatcher()

# Step 1: 从 DataWorks 获取已有节点的 Spec 作为模板
resp = client.get_node(GetNodeRequest(id='existing_di_node_id', project_id=12345))
existing_spec = json.loads(resp.body.node.spec)

# Step 2: 增量 Patch — 只改业务字段，保留所有结构
patched = patcher.patch_existing_node(existing_spec, {
    'name': 'new_sync_orders',
    'script.path': '业务流程/数据集成/sync_orders',
})

# Step 3: 对 DI 节点还需要修改 content 内部的 JSON
node = patched['spec']['nodes'][0]
if node['script']['runtime']['command'] == 'DI':
    di_config = json.loads(node['script']['content'])
    di_config['steps'][0]['parameter']['table'] = ['orders']
    di_config['steps'][1]['parameter']['table'] = 'ods_orders'
    node['script']['content'] = json.dumps(di_config)

# Step 4: 删除 id（创建新节点）
node.pop('id', None)

# Step 5: 校验后提交
from validator import SpecValidator
errors = SpecValidator().validate(patched)
if not errors:
    client.create_node(CreateNodeRequest(
        project_id=12345, scene='DATAWORKS_PROJECT', spec=json.dumps(patched)
    ))
```

### Pagination Helper

All List APIs use `page_number` + `page_size` pattern:

```python
def paginate(list_fn, request_cls, **kwargs):
    """Generic pagination helper for DataWorks list APIs."""
    page = 1
    while True:
        request = request_cls(page_number=page, page_size=100, **kwargs)
        response = list_fn(request)
        paging = response.body.paging_info
        items = getattr(paging, 'nodes', None) or getattr(paging, 'pipeline_runs', None) \
                or getattr(paging, 'workflow_definitions', None) or []
        yield from items
        if page * 100 >= int(paging.total_count):
            break
        page += 1
```

### Error Handling

```python
from alibabacloud_tea_openapi.models import Config
from Tea.exceptions import TeaException

try:
    response = client.create_node(request)
except TeaException as e:
    print(f"Error code: {e.code}")
    print(f"Message: {e.message}")
    print(f"Request ID: {e.data.get('RequestId', 'N/A')}")
```

### 典型工作流：创建节点并发布上线

以下是你（AI 编码工具）应该直接在终端执行的完整流程：

```python
# 在终端直接执行，不是生成脚本文件
import sys, json, time
sys.path.insert(0, '<skill_path>/scripts')

from patcher import SpecPatcher
from validator import SpecValidator
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi.models import Config
from alibabacloud_dataworks_public20240518.client import Client
from alibabacloud_dataworks_public20240518.models import (
    CreateNodeRequest, CreatePipelineRunRequest, GetPipelineRunRequest
)

# 1. 初始化
credential_client = CredentialClient()
config = Config(credential=credential_client, endpoint='dataworks.cn-shanghai.aliyuncs.com')
client = Client(config)

# 2. 从模板生成 FlowSpec
patcher = SpecPatcher(templates_dir='<skill_path>/templates')
spec = patcher.create_node('ODPS_SQL', {
    'node_name': 'daily_report',
    'script_path': '业务流程/report/daily_report',
    'sql_content': "INSERT OVERWRITE TABLE rpt SELECT * FROM ods WHERE dt='${bizdate}';",
    'cron_expression': '00 00 06 * * ?',
    'datasource_name': 'odps_first',
    'resource_group': 'S_res_group_xxx',
    'input_dependency': 'project_root',
    'output_name': 'project.daily_report',
})

# 3. 校验
errors = SpecValidator().validate(spec)
assert not errors, f"校验失败: {errors}"

# 4. 创建节点
resp = client.create_node(CreateNodeRequest(
    project_id=12345, scene='DATAWORKS_PROJECT', spec=json.dumps(spec)
))
node_id = resp.body.id
print(f"✓ 节点已创建: daily_report (ID: {node_id})")

# 5. 发布上线
deploy = client.create_pipeline_run(CreatePipelineRunRequest(
    project_id=12345, type='Online', object_ids=[node_id], description='Deploy daily_report'
))
pipeline_id = deploy.body.id

# 6. 等待发布完成
while True:
    status = client.get_pipeline_run(GetPipelineRunRequest(id=pipeline_id, project_id=12345))
    s = status.body.pipeline_run.status
    if s in ('Success', 'Fail', 'Termination', 'Cancel'):
        print(f"✓ 发布完成: {s}")
        break
    time.sleep(5)
```

**执行后你应该回复用户：**
> 已完成：
> - 创建节点 `daily_report`（ID: 860438872620113xxxx）
> - 调度时间：每天 06:00
> - 已发布到生产环境，状态：Success

## Important Notes

- **Incremental updates**: UpdateNode/UpdateWorkflowDefinition etc. use incremental FlowSpec — only include fields you want to change.
- **Single entity per request**: CreateNode/CreateResource/CreateFunction each process only the first item in the FlowSpec. For batch node creation, use ImportWorkflowDefinition.
- **ImportWorkflowDefinition is async**: Returns an AsyncJob — you must poll `GetJobStatus` to check actual completion status.
- **Cannot delete published nodes**: DeleteNode fails on published nodes. You must take them offline first (via a pipeline run with `type='Offline'`).
- **ID type change**: SDK v8.0.0+ changed `Id` and `ContainerId` from Long to String. Use string types.
- **Pipeline stages are sequential**: You cannot skip or reorder stages in ExecPipelineRunStage.
- **Pipeline `type` parameter**: CreatePipelineRun requires `type='Online'` (deploy) or `type='Offline'` (undeploy).
- **ProjectId**: Required for almost all APIs. Get it from the DataWorks console workspace management page.

## Reference Files

Read reference files before generating code — they contain authoritative field definitions,
enum values, and examples that prevent common mistakes.

**FlowSpec 生成（按需读取）:**
- `references/node-types.md` — Code Model 分类、content 格式说明、各节点类型详细示例
- `references/flowspec-schema.md` — **完整 FlowSpec Schema**（从 dataworks-spec 源码提取），所有字段定义、
  所有枚举值、控制流节点结构、引擎特定配置
- `references/node-types-catalog.md` — **100+ 节点类型完整目录**，含 CodeProgramType code、language、extension

**API 参考:**
- `references/api-reference.md` — 所有 API 的参数、响应结构、约束条件

**工具和枚举:**
- `catalog/node_types.yaml` — 节点类型受控枚举（生成时必须查阅）
- `templates/*.json` — 黄金模板（建议从控制台导出替换）
- `scripts/patcher.py` — SpecPatcher（模板填充/增量 Patch/工作流组装）
- `scripts/validator.py` — SpecValidator（三层校验）
