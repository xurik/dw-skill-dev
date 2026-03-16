# DataWorks Node Types Reference

DataWorks 支持 90+ 种节点类型，每种节点的 FlowSpec `script.content` 格式不同。本文档按内容格式分类，帮助你理解如何为不同节点生成正确的 FlowSpec。

**核心原则**：对于 SQL/Shell/Python 类节点，`script.content` 就是代码文本，可以直接编写。对于 JSON 配置类节点（尤其是数据集成），建议先在 DataWorks 控制台创建一个模板节点，然后通过 `GetNode` API 获取其 FlowSpec 作为基础进行修改。

---

## 目录

1. [Code Model 分类](#code-model)
2. [内容格式速查](#content-format-quickref)
3. [SQL 类节点](#sql-nodes)
4. [Shell/脚本类节点](#shell-nodes)
5. [Python 类节点](#python-nodes)
6. [EMR 类节点](#emr-nodes)
7. [数据集成类节点 (DI)](#di-nodes)
8. [控制类节点](#controller-nodes)
9. [Flink/流计算类节点](#flink-nodes)
10. [算法/AI 类节点](#ai-nodes)
11. [资源和函数类节点](#resource-function-nodes)
12. [Flow 依赖类型](#flow-dependency-types)
13. [模板获取模式](#template-pattern)

---

## Code Model 分类 {#code-model}

DataWorks 内部对每种节点类型有一个 Code Model 类，决定了 `script.content` 的解析方式。理解这个分类是生成正确 FlowSpec 的关键：

| Code Model | 适用节点 | content 格式 | 如何生成 |
|-----------|---------|-------------|---------|
| **PlainTextCode** | ODPS_SQL, DIDE_SHELL, PYTHON, PYODPS, MySQL, PostgreSQL, HOLOGRES_SQL, 所有数据库SQL... | 纯文本代码 | 直接写代码 |
| **EmrCode** | EMR_HIVE, EMR_SPARK_SQL, EMR_SHELL, CDH_HIVE, CDH_SPARK_SQL... | JSON: `{type, launcher, properties}` | 代码放在 `properties.arguments[0]` |
| **DataIntegrationCode** | DI, RI, DATAX, DATAX2 | 数据源/目标/映射 JSON | **必须用模板获取** |
| **ControllerBranchCode** | CONTROLLER_BRANCH | JSON 数组: `[{condition, nodeoutput}]` | 对应节点 `branch` 字段 |
| **ControllerJoinCode** | CONTROLLER_JOIN | JSON: `{branchList, resultStatus}` | 对应节点 `join` 字段 |
| **MultiLanguageScriptingCode** | CONTROLLER_ASSIGNMENT, CONTROLLER_CYCLE_END | JSON: `{language, content}` | language 可选 odps/python/shell |
| **OdpsSparkCode** | ODPS_SPARK | 资源引用行 + JSON | `##@resource_reference{...}` 前缀 |
| **PaiFlowCode** | PAI_STUDIO, PAI_FLOW | 复杂管道 JSON | **必须用模板获取** |
| **SparkSubmitCode** | ADB_SPARK | Spark 提交配置 JSON | 参考模板 |

**生成策略**：PlainTextCode 可直接编写；EmrCode 结构固定可编程生成；其他 JSON 类型建议用模板获取模式。

### script.language 值参考

| 节点类型 | language 值 | runtime.engine |
|---------|------------|----------------|
| ODPS_SQL | `sql` 或 `odps` | `MaxCompute` |
| DIDE_SHELL | `shell` 或 `odps` | `MaxCompute` 或 `General` |
| PYTHON/PYODPS | `python` | `MaxCompute` 或 `General` |
| EMR_HIVE | `hive-sql` | `Hive` |
| EMR_SPARK_SQL | `sql` | `Spark` |
| HOLOGRES_SQL | `sql` | `Hologres` |
| DI | `json` | `DataIntegration` |
| 数据库SQL节点 | `sql` | 对应数据库名 |

---

## 内容格式速查 {#content-format-quickref}

### script.content = 纯代码文本

这些节点的 `script.content` 就是可执行的代码，可以直接用字符串写入：

| runtime.command | 引擎 | 内容格式 | 文件扩展名 |
|----------------|------|---------|-----------|
| `ODPS_SQL` | MaxCompute | SQL | .sql |
| `ODPS_SPARK_SQL` | MaxCompute Spark | SQL | .sql |
| `ODPS_SQL_SCRIPT` | MaxCompute Script | 多条SQL | .ms |
| `HIVE` | MaxCompute (Hive兼容) | SQL | .sql |
| **EMR/CDH 系列** | **注意：虽然扩展名是 .sql/.sh，但 content 是 EmrCode JSON 格式，详见 EMR 章节** | | |
| `HOLOGRES_SQL` | Hologres | PostgreSQL兼容SQL | .sql |
| `HOLOGRES_DEVELOP` | Hologres开发 | SQL | .sql |
| `CLICK_SQL` | ClickHouse | SQL | .sql |
| `POSTGRESQL` | PostgreSQL | SQL | .sql |
| `MySQL` | MySQL | SQL | .sql |
| `Sql Server` | SQL Server | SQL | .sql |
| `Oracle` | Oracle | SQL | .sql |
| `StarRocks` | StarRocks | SQL | .sql |
| `DRDS` | DRDS | SQL | .sql |
| `Doris` | Doris | SQL | .sql |
| `Mariadb` | MariaDB | SQL | .sql |
| `Selectdb` | SelectDB | SQL | .sql |
| `Redshift` | Redshift | SQL | .sql |
| `Vertica` | Vertica | SQL | .sql |
| `OceanBase` | OceanBase | SQL | .sql |
| `DB2` | DB2 | SQL | .sql |
| `ADB for PostgreSQL` | ADB PG | SQL | .sql |
| `ADB for MySQL` | ADB MySQL | SQL | .sql |
| `ADB Spark SQL` | ADB Spark | SQL | .sql |
| `CDH_HIVE` | CDH Hive | HiveQL | .sql |
| `CDH_SPARK_SQL` | CDH Spark SQL | SQL | .sql |
| `CDH_PRESTO` | CDH Presto | SQL | .sql |
| `CDH_IMPALA` | CDH Impala | SQL | .sql |
| `DIDE_SHELL` | 通用Shell | Shell脚本 | .sh |
| `SHELL` | Shell | Shell脚本 | .sh |
| **EMR_SHELL/CDH_SHELL 等** | **EmrCode JSON，详见 EMR 章节** | | |
| `SSH` | SSH远程执行 | Shell脚本 | .sh |
| `PERL` | Perl | Perl脚本 | .pl |
| `PYTHON` | Python 3 | Python代码 | .py |
| `PY_ODPS` | PyODPS 2 | Python代码 | .py |
| `PYODPS3` | PyODPS 3 | Python代码 | .py |
| `COMPONENT_SQL` | SQL组件 | SQL | .sql |
| `SQL_COMPONENT` | SQL组件(新) | SQL | .sql |

### script.content = JSON 配置

这些节点的 `script.content` 是复杂的 JSON 字符串，结构因节点类型和配置不同而差异很大：

| runtime.command | 引擎 | 说明 | 文件扩展名 |
|----------------|------|------|-----------|
| `DI` | 数据集成 | 离线同步任务配置 | .json |
| `RI` | 数据集成 | 实时同步任务配置 | .json |
| `DATAX` | DataX | 旧版离线同步 | .json |
| `DATAX2` | DataX2 | 旧版离线同步 | .json |
| `CDP` | CDP | 旧版同步 | .json |
| `CONTROLLER_BRANCH` | 控制 | 分支条件配置 | .json |
| `CONTROLLER_CYCLE` | 控制 | 循环条件配置 | .json |
| `CONTROLLER_TRAVERSE` | 控制 | 遍历配置 | .json |
| `CONTROLLER_ASSIGNMENT` | 控制 | 赋值配置 | .json |
| `CONTROLLER_JOIN` | 控制 | 汇聚配置 | .json |
| `CONTROLLER_WAIT` | 控制 | 等待条件配置 | .json |
| `BLINK_STREAM_SQL` | Flink流 | Flink SQL作业配置 | .json |
| `FLINK_SQL_BATCH` | Flink批 | Flink SQL批处理配置 | .json |
| `FLINK_SQL_STREAM` | Flink流 | Flink SQL流处理配置 | .json |
| `BLINK_BATCH_SQL` | Flink批 | Blink SQL批处理配置 | .json |
| `BLINK_DATASTREAM` | Flink | DataStream作业配置 | .json |
| `pai` | PAI | 机器学习实验配置 | .json |
| `pai_studio` | PAI Studio | PAI Studio实验 | .json |
| `pai_dlc` | PAI DLC | 深度学习容器 | .sh |
| `PAI_FLOW` | PAI Flow | 工作流YAML | .yaml |
| `COMBINED_NODE` | 组合节点 | 子节点组合配置 | .json |
| `CHECK` | 检查 | 数据质量检查规则 | .json |
| `CHECK_NODE` | 检查节点 | 对象可用性检查 | .json |
| `ODPS_SPARK` | MaxCompute Spark | Spark作业配置 | .json |
| `ODPS_SHARK` | MaxCompute Shark | Shark配置 | .json |
| `ADB Spark` | ADB Spark | ADB Spark配置 | .json |
| `HOLOGRES_SYNC_DDL` | Hologres | DDL同步配置 | .json |
| `HOLOGRES_SYNC_DATA` | Hologres | 数据同步配置 | .json |
| `DataService_studio` | 数据服务 | API配置 | .json |
| `SCHEDULER_TRIGGER` | 调度触发器 | 触发器配置 | .json |
| `PARAM_HUB` | 参数节点 | 参数配置 | .json |
| `DATA_PUSH` | 数据推送 | 推送配置 | .json |
| `DATA_QUALITY_MONITOR` | 数据质量 | 监控规则配置 | .json |

### script.content = 空或无关紧要

| runtime.command | 说明 |
|----------------|------|
| `VIRTUAL` | 虚拟节点，不产生数据，用于控制依赖 |
| `SUB_PROCESS` | 子流程，引用其他工作流 |
| `VIRTUAL_WORKFLOW` | 虚拟工作流 |

---

## SQL 类节点 {#sql-nodes}

最简单的节点类型。`script.content` 就是 SQL 语句。

```json
{
  "version": "1.1.0",
  "kind": "Node",
  "spec": {
    "nodes": [{
      "name": "my_odps_sql",
      "recurrence": "Normal",
      "timeout": 0,
      "instanceMode": "T+1",
      "rerunMode": "Allowed",
      "rerunTimes": 3,
      "rerunInterval": 180000,
      "datasource": { "name": "odps_first" },
      "script": {
        "path": "业务流程/数据开发/my_odps_sql",
        "runtime": { "command": "ODPS_SQL" },
        "content": "INSERT OVERWRITE TABLE target_table PARTITION(dt='${bizdate}')\nSELECT col1, col2\nFROM source_table\nWHERE dt = '${bizdate}';",
        "parameters": [
          {
            "name": "bizdate",
            "artifactType": "Variable",
            "scope": "NodeParameter",
            "type": "System",
            "value": "$[yyyymmdd-1]"
          }
        ]
      },
      "trigger": {
        "type": "Scheduler",
        "cron": "00 00 02 * * ?",
        "startTime": "1970-01-01 00:00:00",
        "endTime": "9999-01-01 00:00:00",
        "timezone": "Asia/Shanghai"
      },
      "runtimeResource": { "resourceGroup": "S_res_group_xxx" },
      "inputs": {
        "nodeOutputs": [
          { "data": "project_root", "artifactType": "NodeOutput" }
        ]
      },
      "outputs": {
        "nodeOutputs": [
          { "data": "project.my_odps_sql", "artifactType": "NodeOutput" }
        ]
      }
    }]
  }
}
```

**不同 SQL 引擎的区别**仅在于 `runtime.command` 和 `datasource` 不同：

- MaxCompute: `"command": "ODPS_SQL"`, datasource type = odps
- Hologres: `"command": "HOLOGRES_SQL"`, datasource type = hologres
- MySQL: `"command": "MySQL"`, datasource type = mysql
- ClickHouse: `"command": "CLICK_SQL"`, datasource type = clickhouse
- 注意：**EMR 节点不是纯 SQL**，见下面 EMR 专门章节

**注意 command 值大小写不一致**：`"MySQL"`, `"Sql Server"`, `"Oracle"`, `"ADB for PostgreSQL"` 等，必须与 CodeProgramType 定义完全一致。

---

## Shell/脚本类节点 {#shell-nodes}

`script.content` 是 Shell 脚本代码。

```json
{
  "script": {
    "path": "业务流程/数据开发/my_shell",
    "runtime": { "command": "DIDE_SHELL" },
    "content": "#!/bin/bash\necho \"Processing date: ${bizdate}\"\npython3 /home/admin/scripts/etl.py --date ${bizdate}\necho \"Done\""
  }
}
```

**注意**：DIDE_SHELL 不支持交互式命令（如 top, vim）。

---

## Python 类节点 {#python-nodes}

### PYTHON (通用 Python 3)

```json
{
  "script": {
    "runtime": { "command": "PYTHON" },
    "content": "import sys\nprint('Hello from Python')\nprint(f'bizdate={args[\"bizdate\"]}')"
  }
}
```

### PyODPS (PYODPS3)

PyODPS 节点自带 MaxCompute 连接上下文，可直接使用 `o` 对象：

```json
{
  "script": {
    "runtime": { "command": "PYODPS3" },
    "content": "import sys\nfrom odps import options\n\n# o 是预置的 ODPS 入口对象\nfor table in o.list_tables():\n    print(table.name)\n\nt = o.get_table('my_table')\nprint(t.schema)"
  },
  "datasource": { "name": "odps_first" }
}
```

---

## 数据集成类节点 (DI) {#di-nodes}

**这是最复杂的节点类型。** 数据集成节点的 `script.content` 是一个大型 JSON 字符串，描述源端、目标端、字段映射、通道配置等。不同数据源组合（MySQL→MaxCompute、Oracle→Hologres、FTP→OSS 等）的 JSON 结构差异很大。

**强烈建议使用"模板获取"模式**（见下文）：先在 DataWorks 控制台可视化创建一个 DI 节点，配置好后通过 GetNode API 获取其 FlowSpec，然后以此为模板进行编程修改。

### DI 节点的 script.content 大致结构

```json
{
  "type": "job",
  "version": "2.0",
  "steps": [
    {
      "stepType": "mysql",
      "parameter": {
        "datasource": "mysql_source",
        "table": ["source_table"],
        "column": ["id", "name", "created_at"],
        "where": "dt = '${bizdate}'",
        "splitPk": "id"
      },
      "name": "Reader",
      "category": "reader"
    },
    {
      "stepType": "odps",
      "parameter": {
        "datasource": "odps_first",
        "table": "target_table",
        "column": ["id", "name", "created_at"],
        "partition": "dt=${bizdate}",
        "truncate": true
      },
      "name": "Writer",
      "category": "writer"
    }
  ],
  "setting": {
    "speed": { "channel": 5 },
    "errorLimit": { "record": 0 }
  },
  "order": {
    "hops": [
      { "from": "Reader", "to": "Writer" }
    ]
  }
}
```

**注意**：上面的结构是简化示例。实际的 DI 配置远比这复杂，各 reader/writer plugin 的 parameter 字段完全不同。

### DI 节点 FlowSpec 包装

```json
{
  "version": "1.1.0",
  "kind": "Node",
  "spec": {
    "nodes": [{
      "name": "mysql_to_odps_sync",
      "recurrence": "Normal",
      "script": {
        "runtime": { "command": "DI" },
        "content": "{...上面的 JSON 字符串，需要转义...}"
      },
      "trigger": { ... },
      "runtimeResource": { "resourceGroup": "S_res_group_xxx" }
    }]
  }
}
```

---

## EMR 类节点 {#emr-nodes}

**EMR 节点的 `script.content` 不是纯 SQL/代码**，而是一个特殊的 JSON 结构 (EmrCode)，实际代码放在 `properties.arguments[0]` 中。

### EmrCode JSON 结构

```json
{
  "type": "HIVE_SQL",
  "launcher": {
    "allocationSpec": {
      "DATAWORKS_SESSION_DISABLE": false,
      "priority": "1",
      "queue": "default"
    }
  },
  "properties": {
    "envs": {},
    "arguments": ["SELECT * FROM my_hive_table WHERE dt='${bizdate}'"],
    "tags": ["resource_group_id"]
  }
}
```

### 完整的 EMR FlowSpec 示例

```json
{
  "script": {
    "path": "业务流程/EMR/my_hive_task",
    "language": "sql",
    "runtime": {
      "command": "EMR_HIVE",
      "template": {
        "type": "HIVE_SQL",
        "launcher": {
          "allocationSpec": {
            "DATAWORKS_SESSION_DISABLE": false,
            "priority": "1",
            "queue": "default"
          }
        },
        "properties": { "envs": {}, "arguments": [], "tags": [] }
      }
    },
    "content": "{\"type\":\"HIVE_SQL\",\"launcher\":{\"allocationSpec\":{\"DATAWORKS_SESSION_DISABLE\":false,\"priority\":\"1\",\"queue\":\"default\"}},\"properties\":{\"envs\":{},\"arguments\":[\"SELECT * FROM my_table\"],\"tags\":[]}}"
  }
}
```

### EmrJobType 值 (content 中的 type 字段)

| command | type 值 |
|---------|--------|
| EMR_HIVE | `HIVE_SQL` |
| EMR_SPARK_SQL | `SPARK_SQL` |
| EMR_SPARK | `SPARK` |
| EMR_SPARK_SHELL | `SPARK_SHELL` |
| EMR_SPARK_STREAMING | `SPARK_STREAMING` |
| EMR_MR | `MR` |
| EMR_SHELL | `SHELL` |
| EMR_PRESTO | `PRESTO_SQL` |
| EMR_TRINO | `TRINO_SQL` |
| EMR_IMPALA | `IMPALA_SQL` |
| EMR_KYUUBI | `KYUUBI` |
| EMR_STREAMING_SQL | `STREAMING_SQL` |

### EMR runtime 额外字段

EMR 节点的 `runtime` 还可以包含以下额外配置：

```json
{
  "runtime": {
    "command": "EMR_HIVE",
    "engine": "Hive",
    "sparkConf": {
      "spark.executor.memory": "1024m",
      "spark.executor.cores": 1,
      "spark.executor.instances": 1,
      "spark.yarn.queue": "default"
    },
    "emrJobConfig": {
      "submitMode": "Local",
      "submitter": "root",
      "priority": 1,
      "queue": "default",
      "cores": 1,
      "memory": 1024
    }
  }
}
```

CDH 节点结构与 EMR 相同，只是 command 前缀改为 `CDH_`，且使用 `cdhJobConfig` 代替 `emrJobConfig`。

---

## 控制类节点 {#controller-nodes}

控制类节点使用**节点对象上的特殊顶层字段**（不仅仅是 script.content），这是它们与普通节点的最大区别。

### 虚拟节点 (VIRTUAL)

最简单的控制节点，仅用于建立依赖关系：

```json
{
  "script": {
    "runtime": { "command": "VIRTUAL" },
    "content": ""
  }
}
```

### 分支节点 (CONTROLLER_BRANCH)

使用节点的 **`branch`** 顶层字段：

```json
{
  "id": "branch_node",
  "script": { "runtime": { "command": "CONTROLLER_BRANCH" } },
  "branch": {
    "branches": [
      { "when": "a == 1", "output": "{{artifacts.branch_success}}", "desc": "成功分支" },
      { "when": "a == 2", "output": "{{artifacts.branch_fail}}", "desc": "失败分支" }
    ]
  }
}
```

script.content 中的格式 (ControllerBranchCode)：
```json
[
  {"condition": "a == 1", "nodeoutput": "project.branch_success", "description": "成功分支"},
  {"condition": "a == 2", "nodeoutput": "project.branch_fail", "description": "失败分支"}
]
```

### 赋值节点 (CONTROLLER_ASSIGNMENT)

script.content 是 MultiLanguageScriptingCode 格式，支持 `odps`/`python`/`shell`：

```json
{
  "script": {
    "runtime": { "command": "CONTROLLER_ASSIGNMENT" },
    "content": "{\"language\": \"odps\", \"content\": \"select 1\"}"
  }
}
```

### 汇聚节点 (CONTROLLER_JOIN)

使用节点的 **`join`** 顶层字段：

```json
{
  "id": "join_node",
  "script": { "runtime": { "command": "CONTROLLER_JOIN" } },
  "join": {
    "branches": [
      {
        "nodeId": "upstream_1",
        "assertion": { "field": "status", "in": ["SUCCESS"] },
        "name": "b1"
      },
      {
        "nodeId": "upstream_2",
        "assertion": { "field": "status", "in": ["SUCCESS"] },
        "name": "b2"
      }
    ],
    "logic": { "expression": "b1 and b2" }
  }
}
```

### 循环节点 (CONTROLLER_CYCLE / do-while)

使用节点的 **`do-while`** 顶层字段，内含子节点和循环条件：

```json
{
  "id": "loop_node",
  "script": {
    "runtime": { "command": "CONTROLLER_CYCLE" },
    "parameters": [
      { "name": "loopDataArray", "scope": "NodeParameter", "type": "System", "value": "[]" }
    ]
  },
  "do-while": {
    "maxIterations": 10,
    "parallelism": 3,
    "nodes": [
      { "id": "start", "script": { "runtime": { "command": "CONTROLLER_CYCLE_START" } } },
      { "id": "inner_task", "script": { "runtime": { "command": "DIDE_SHELL" }, "content": "echo loop" } }
    ],
    "flow": [
      { "nodeId": "inner_task", "depends": [{ "nodeId": "start", "type": "Normal" }] }
    ],
    "while": {
      "id": "end",
      "script": {
        "content": "select True",
        "language": "odps-sql",
        "runtime": { "command": "CONTROLLER_CYCLE_END" }
      }
    }
  }
}
```

### 遍历节点 (CONTROLLER_TRAVERSE / for-each)

使用节点的 **`for-each`** 顶层字段：

```json
{
  "id": "foreach_node",
  "script": {
    "runtime": { "command": "CONTROLLER_TRAVERSE" },
    "parameters": [
      { "name": "loopDataArray", "scope": "NodeParameter", "type": "System", "value": "[]" }
    ]
  },
  "for-each": {
    "nodes": [
      { "id": "start", "script": { "runtime": { "command": "CONTROLLER_TRAVERSE_START" } } },
      { "id": "body", "script": { "runtime": { "command": "DIDE_SHELL" }, "content": "echo ${item}" } },
      { "id": "end", "script": { "runtime": { "command": "CONTROLLER_TRAVERSE_END" } } }
    ],
    "flow": [
      { "nodeId": "body", "depends": [{ "output": "start", "type": "Normal" }] },
      { "nodeId": "end", "depends": [{ "output": "body", "type": "Normal" }] }
    ]
  }
}
```

### 参数节点 (PARAM_HUB)

使用节点的 **`param-hub`** 顶层字段：

```json
{
  "id": "param_1",
  "script": { "runtime": { "command": "PARAM_HUB" } },
  "param-hub": {
    "variables": [
      { "name": "region", "type": "Constant", "scope": "NodeContext", "value": "cn-shanghai" },
      { "name": "bizdate", "type": "System", "scope": "NodeContext", "value": "${yyyymmdd}" }
    ]
  }
}
```

### 组合节点 (COMBINED_NODE)

使用节点的 **`combined`** 顶层字段嵌套子节点：

```json
{
  "id": "combined_1",
  "script": { "runtime": { "command": "ODPS_SQL" } },
  "combined": {
    "nodes": [
      { "id": "sql1", "script": { "path": "/file1.sql", "runtime": { "command": "ODPS_SQL" } } },
      { "id": "sql2", "script": { "path": "/file2.sql", "runtime": { "command": "ODPS_SQL" } } }
    ],
    "flow": [
      { "nodeId": "{{sql2}}", "depends": [{ "nodeId": "{{sql1}}" }] }
    ]
  }
}
```

---

## Flink/流计算类节点 {#flink-nodes}

Flink 节点的 `script.content` 是 JSON 配置。建议通过模板获取模式创建。

```json
{
  "script": {
    "language": "json",
    "runtime": { "command": "FLINK_SQL_STREAM" },
    "content": "{\"flinkSql\":\"CREATE TABLE source (...) WITH (...);\\nCREATE TABLE sink (...) WITH (...);\\nINSERT INTO sink SELECT * FROM source;\",\"configuration\":{\"parallelism\":\"4\"}}"
  }
}
```

---

## 算法/AI 类节点 {#ai-nodes}

PAI 节点的 `script.content` 是复杂的 JSON (PaiFlowCode)。**强烈建议使用模板获取模式**。

PAI Studio (pai_studio) 的 content 包含：`appId`, `tasks[]`, `taskRelations[]`, `inputs`, `outputs`, `computeResource` 等。

PAI DLC 节点类似 Shell：

```json
{
  "script": {
    "runtime": { "command": "pai_dlc" },
    "content": "python train.py --epochs 10 --batch-size 32"
  }
}
```

### ODPS Spark 节点

ODPS_SPARK 的 content 有特殊格式：**资源引用前缀行 + JSON 配置**：

```json
{
  "script": {
    "runtime": { "command": "ODPS_SPARK" },
    "content": "##@resource_reference{\"my_jar.jar\"}\n{\"version\":\"2.x\",\"language\":\"java\",\"mainClass\":\"com.example.MyJob\",\"mainJar\":\"my_jar.jar\",\"args\":\"arg1 arg2\",\"configs\":[\"spark.executor.memory=4g\"]}"
  }
}
```

---

## 资源和函数类节点 {#resource-function-nodes}

这些不是调度节点，而是数据开发中的辅助实体。

### 资源类型

| runtime.command | 说明 |
|----------------|------|
| `ODPS_PYTHON` | Python 资源文件 |
| `ODPS_JAR` | JAR 包资源 |
| `ODPS_FILE` | 普通文件资源 |
| `ODPS_ARCHIVE` | 压缩包资源 |
| `EMR_JAR` | EMR JAR 资源 |
| `EMR_FILE` | EMR 文件资源 |

### 函数类型

| runtime.command | 说明 |
|----------------|------|
| `ODPS_FUNCTION` | MaxCompute UDF |
| `EMR_FUNCTION` | EMR UDF |

---

## Flow 依赖类型 {#flow-dependency-types}

FlowSpec 中 `flow[].depends[].type` 支持以下依赖类型：

| type | 说明 |
|------|------|
| `Normal` | 标准同周期依赖（上游同一调度周期执行完才执行） |
| `CrossCycleDependsOnSelf` | 跨周期自依赖（依赖自己上一个周期的执行结果） |
| `CrossCycleDependsOnOtherNode` | 跨周期依赖其他节点（依赖其他节点上一个周期） |
| `CrossCycleDependsOnChildren` | 跨周期依赖子节点（依赖子节点上一个周期） |

### Flow 示例

```json
{
  "flow": [
    {
      "nodeId": "node_b",
      "depends": [
        { "nodeId": "node_a", "type": "Normal" },
        { "type": "CrossCycleDependsOnSelf" }
      ]
    }
  ]
}
```

---

## 模板获取模式 {#template-pattern}

**这是处理复杂节点类型（尤其是 DI、Flink、PAI）最可靠的方法。**

### 思路

1. 在 DataWorks 控制台中手动创建一个目标类型的节点
2. 通过可视化界面配置好各项参数
3. 调用 `GetNode` API 获取该节点的完整 FlowSpec
4. 解析 FlowSpec，以此为模板进行编程修改
5. 用修改后的 FlowSpec 调用 `CreateNode` 或 `UpdateNode`

### 代码示例

```python
import json
from alibabacloud_dataworks_public20240518.models import GetNodeRequest, CreateNodeRequest

# Step 1: 获取模板节点的 FlowSpec
template_resp = client.get_node(GetNodeRequest(
    id='existing_template_node_id',
    project_id=12345
))
template_spec = json.loads(template_resp.body.node.spec)

# Step 2: 修改模板
node_def = template_spec['spec']['nodes'][0]
node_def['name'] = 'new_node_name'
node_def['script']['path'] = '业务流程/数据开发/new_node_name'

# 对于 SQL 节点，直接修改 content
node_def['script']['content'] = 'SELECT * FROM new_table WHERE dt = "${bizdate}";'

# 对于 DI 节点，解析内部 JSON 再修改
if node_def['script']['runtime']['command'] == 'DI':
    di_config = json.loads(node_def['script']['content'])
    # 修改源表
    di_config['steps'][0]['parameter']['table'] = ['new_source_table']
    # 修改目标表
    di_config['steps'][1]['parameter']['table'] = 'new_target_table'
    node_def['script']['content'] = json.dumps(di_config)

# Step 3: 用修改后的 FlowSpec 创建新节点
# 删除原节点的 id，让系统自动分配
if 'id' in node_def:
    del node_def['id']

request = CreateNodeRequest(
    project_id=12345,
    scene='DATAWORKS_PROJECT',
    spec=json.dumps(template_spec)
)
response = client.create_node(request)
print(f"Created node: {response.body.id}")
```

### 批量复制模式

当你需要创建多个结构相似的节点时（比如为多张表创建同类型的 DI 同步节点），模板模式尤其有用：

```python
tables = ['orders', 'users', 'products', 'payments']

for table in tables:
    # 深拷贝模板
    spec = json.loads(json.dumps(template_spec))
    node = spec['spec']['nodes'][0]

    # 修改节点名和路径
    node['name'] = f'sync_{table}'
    node['script']['path'] = f'业务流程/数据集成/sync_{table}'

    # 修改 DI 配置中的表名
    di_config = json.loads(node['script']['content'])
    di_config['steps'][0]['parameter']['table'] = [table]
    di_config['steps'][1]['parameter']['table'] = f'ods_{table}'
    di_config['steps'][1]['parameter']['partition'] = f'dt=${{bizdate}}'
    node['script']['content'] = json.dumps(di_config)

    response = client.create_node(CreateNodeRequest(
        project_id=12345,
        scene='DATAWORKS_PROJECT',
        spec=json.dumps(spec)
    ))
    print(f"Created sync_{table}: {response.body.id}")
```

### 调度参数速查

FlowSpec 中常用的调度参数表达式：

| 表达式 | 含义 | 示例值 |
|--------|------|--------|
| `$[yyyymmdd]` | 业务日期 | 20260315 |
| `$[yyyymmdd-1]` | 业务日期前一天 | 20260314 |
| `$[yyyymmdd+1]` | 业务日期后一天 | 20260316 |
| `$[yyyy-mm-dd]` | 带横线格式 | 2026-03-15 |
| `$[hh24miss]` | 时分秒 | 020000 |
| `$[yyyy]` | 年 | 2026 |
| `$[mm]` | 月 | 03 |
| `$[dd]` | 日 | 15 |
| `${bizdate}` | 业务日期(节点参数) | 自动替换 |
