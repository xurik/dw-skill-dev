# FlowSpec Complete Schema Reference

Source: Java classes from https://github.com/aliyun/dataworks-spec

This is the authoritative field-level reference. Use `references/node-types.md` for usage patterns
and examples. Use this file when you need to know **exactly what fields exist** and **what enum values are valid**.

## Table of Contents
- [Top-Level Wrapper](#top-level-wrapper)
- [All SpecKind Values](#all-speckind-values)
- [DataWorksWorkflowSpec](#dataworksworkflowspec)
- [SpecNode (Complete)](#specnode)
- [SpecScript](#specscript)
- [SpecScriptRuntime](#specscriptruntime)
- [SpecTrigger](#spectrigger)
- [SpecVariable](#specvariable)
- [SpecScheduleStrategy](#specschedulestrategy)
- [Flow Dependencies](#flow-dependencies)
- [Control Flow Nodes](#control-flow-nodes)
- [SpecFileResource](#specfileresource)
- [SpecFunction](#specfunction)
- [SpecComponent](#speccomponent)
- [All Enums](#all-enums)

---

## Top-Level Wrapper

```json
{ "version": "1.1.0", "kind": "<SpecKind>", "metadata": {}, "spec": {} }
```

SpecVersion: `1.0.0`, `1.1.0`, `1.2.0`, `2.0.0`

## All SpecKind Values

| Enum | JSON Label | Use Case |
|------|-----------|----------|
| CYCLE_WORKFLOW | `CycleWorkflow` | Scheduled workflow/node |
| MANUAL_WORKFLOW | `ManualWorkflow` | Manual workflow |
| TRIGGER_WORKFLOW | `TriggerWorkflow` | Event-triggered |
| MANUAL_NODE | `ManualNode` | Manual standalone node |
| TEMPORARY_WORKFLOW | `TemporaryWorkflow` | Temporary/ad-hoc |
| PAIFLOW | `PaiFlow` | PAI ML flow |
| BATCH_DEPLOYMENT | `BatchDeployment` | Batch deployment |
| DATASOURCE | `DataSource` | Data source def |
| DATA_QUALITY | `DataQuality` | DQ rules |
| DATA_SERVICE | `DataService` | Data service |
| DATA_CATALOG | `DataCatalog` | Catalog entity |
| TABLE | `Table` | Table definition |
| NODE | `Node` | Standalone node |
| COMPONENT | `Component` | Reusable component |
| RESOURCE | `Resource` | File resource |
| FUNCTION | `Function` | UDF function |
| WORKFLOW | `Workflow` | Generic workflow |
| DATA_INTEGRATION_JOB | `DataIntegrationJob` | DI job |

## DataWorksWorkflowSpec

The `spec` body. All fields optional.

| Field | Type |
|-------|------|
| `name` | String |
| `owner` | String |
| `description` | String |
| `type` | String |
| `strategy` | SpecScheduleStrategy |
| `nodes` | SpecNode[] |
| `workflows` | SpecWorkflow[] |
| `flow` / `dependencies` | SpecFlowDepend[] |
| `fileResources` | SpecFileResource[] |
| `functions` | SpecFunction[] |
| `components` | SpecComponent[] |
| `variables` | SpecVariable[] |
| `triggers` | SpecTrigger[] |
| `scripts` | SpecScript[] |
| `artifacts` | SpecArtifact[] |
| `datasources` | SpecDatasource[] |
| `runtimeResources` | SpecRuntimeResource[] |
| `dqcRules` | SpecDqcRule[] |
| `tables` | SpecTable[] |
| `dataIntegrationJobs` | SpecDataIntegrationJob[] |

## SpecNode

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique ID (for flow references) |
| `name` | String | Display name |
| `owner` | String | Owner |
| `description` | String | Description |
| `recurrence` | NodeRecurrenceType | `Normal`/`Pause`/`Skip`/`NoneAuto` |
| `priority` | Integer | 1-8 |
| `timeout` | Integer | Timeout value |
| `timeoutUnit` | TimeUnit | Unit |
| `instanceMode` | NodeInstanceModeType | `T+1`/`Immediately` |
| `rerunMode` | NodeRerunModeType | `Allowed`/`Denied`/`FailureAllowed` |
| `rerunTimes` | Integer | Retry count |
| `rerunInterval` | Integer | Retry interval (ms) |
| `ignoreBranchConditionSkip` | Boolean | |
| `autoParse` | Boolean | Auto-parse dependencies |
| `datasource` | SpecDatasource | `{name, type}` |
| `script` | SpecScript | Code and runtime |
| `trigger` | SpecTrigger | Schedule |
| `runtimeResource` | SpecRuntimeResource | Resource group |
| `fileResources` | SpecFileResource[] | Referenced resources |
| `functions` | SpecFunction[] | Referenced UDFs |
| `inputs` | Object | `{nodeOutputs[], tables[], variables[]}` |
| `outputs` | Object | `{nodeOutputs[], tables[], variables[]}` |
| `reference` | SpecNodeRef | `{output}` |
| `strategy` | SpecScheduleStrategy | Strategy override |
| `component` | SpecComponent | Component ref |
| `datasets` | SpecDataset[] | Dataset mounts |
| **Control Flow** | | |
| `branch` | SpecBranch | Branch conditions |
| `join` | SpecJoin | Join conditions |
| `doWhile` / `do-while` | SpecDoWhile | Loop |
| `foreach` / `for-each` | SpecForEach | Iteration |
| `combined` | SpecSubFlow | Sub-flow |
| `subflow` | SpecSubFlow | Sub-workflow |
| `paramHub` / `param-hub` | SpecParamHub | Param hub |
| `paiflow` | SpecPaiflow | PAI flow |

## SpecScript

| Field | Type |
|-------|------|
| `path` | String |
| `language` | String (LanguageEnum) |
| `runtime` | SpecScriptRuntime |
| `content` | String |
| `parameters` | SpecVariable[] |
| `extension` | String |

## SpecScriptRuntime

| Field | Type | Description |
|-------|------|-------------|
| `engine` | String | Engine name |
| `command` | String | CodeProgramType name |
| `commandTypeId` | Integer | Numeric code |
| `template` | Object | General template (EMR launcher etc.) |
| `emrJobConfig` | Object | EMR job config |
| `cdhJobConfig` | Object | CDH job config |
| `adbJobConfig` | Object | ADB job config |
| `lindormJobConfig` | Object | Lindorm config |
| `sparkConf` | Object | Spark properties |
| `flinkConf` | Object | Flink properties |
| `streamJobConfig` | Object | Streaming config |
| `paiflowConf` | Object | PAI flow config |
| `maxComputeConf` | Object | MaxCompute config |
| `container` | SpecContainer | `{image, command[], args[], env[]}` |
| `linkedRoleArn` | String | RAM role ARN |
| `cu` | String | CU spec |

## SpecTrigger

| Field | Type | Values |
|-------|------|--------|
| `type` | TriggerType | `Scheduler`/`Manual`/`Streaming`/`None`/`Custom` |
| `cron` | String | 6-field: `sec min hour day month weekday` |
| `cycleType` | CycleType | `Daily`/`NotDaily` |
| `recurrence` | NodeRecurrenceType | `Normal`/`Pause`/`Skip` |
| `startTime` | String | `yyyy-MM-dd HH:mm:ss` |
| `endTime` | String | |
| `timezone` | String | e.g. `Asia/Shanghai` |
| `delaySeconds` | Integer | |
| `calendarId` | Long | |

## SpecVariable

| Field | Type | Values |
|-------|------|--------|
| `name` | String | |
| `scope` | VariableScopeType | `Tenant`/`Workspace`/`Workflow`/`NodeParameter`/`NodeContext` |
| `type` | VariableType | `System`/`Constant`/`NodeOutput`/`PaiOutput`/`PassThrough`/`NoKvVariableExpression` |
| `value` | String | e.g. `$[yyyymmdd-1]` |
| `description` | String | |
| `artifactType` | ArtifactType | Always `Variable` |

### System Variable Expressions

| Expression | Description |
|-----------|-------------|
| `$[yyyymmdd]` | Business date |
| `$[yyyymmdd-1]` | Yesterday |
| `$[yyyymmdd+1]` | Tomorrow |
| `$[yyyy-mm-dd]` | Date with dashes |
| `$[hh24miss]` | Current time |
| `${bizdate}` | Business date param |

## SpecScheduleStrategy

| Field | Type |
|-------|------|
| `priority` | Integer |
| `priorityWeightStrategy` | `Disabled`/`Upstream` |
| `maxInternalConcurrency` | Integer |
| `timeout` | Integer |
| `timeoutUnit` | TimeUnit |
| `instanceMode` | NodeInstanceModeType |
| `rerunMode` | NodeRerunModeType |
| `rerunTimes` | Integer |
| `rerunInterval` | Integer |
| `failureStrategy` | `Continue`/`Break` |
| `recurrenceType` | NodeRecurrenceType |

## Flow Dependencies

```json
{"nodeId": "B", "depends": [{"nodeId": "A", "type": "Normal"}]}
```

### DependencyType

| Value | Description |
|-------|-------------|
| `Normal` | Run after upstream succeeds |
| `CrossCycleDependsOnSelf` | Depends on own previous cycle |
| `CrossCycleDependsOnChildren` | Depends on children of previous cycle |
| `CrossCycleDependsOnOtherNode` | Depends on other node's previous cycle |

## Control Flow Nodes

### SpecBranch
```json
{"branches": [{"when": "expr", "output": {"data": "..."}, "desc": "...", "valueType": "...", "fromVariable": "..."}]}
```

### SpecJoin
```json
{"branches": [{"name": "b1", "nodeId": "...", "output": {"data": "..."}, "assertion": {"field": "status", "in": {"value": ["SUCCESS"]}}}], "logic": {"expression": "b1 and b2"}, "resultStatus": "..."}
```

### SpecDoWhile (`do-while` in JSON)
```json
{"nodes": [...], "while": {"script": {...}}, "flow": [...], "maxIterations": 10, "parallelism": 1}
```

### SpecForEach (`for-each` in JSON)
```json
{"array": {"name": "...", "type": "Constant", "value": "a,b,c"}, "nodes": [...], "flow": [...], "maxIterations": 100, "parallelism": 5}
```

### SpecParamHub (`param-hub` in JSON)
```json
{"variables": [{"name": "env", "type": "Constant", "value": "prod"}]}
```

## SpecFileResource

| Field | Type |
|-------|------|
| `name` | String |
| `script` | SpecScript |
| `runtimeResource` | SpecRuntimeResource |
| `type` | `python`/`jar`/`archive`/`file` |
| `file` | SpecObjectStorageFile |
| `datasource` | SpecDatasource |

## SpecFunction

| Field | Type |
|-------|------|
| `name` | String |
| `className` | String |
| `type` | `math`/`aggregate`/`string`/`date`/`analytic`/`other` |
| `script` | SpecScript |
| `datasource` | SpecDatasource |
| `runtimeResource` | SpecRuntimeResource |
| `fileResources` | SpecFileResource[] |
| `embeddedCodeType` | `python2`/`python3`/`java8`/`java11`/`java17` |
| `embeddedCode` | String |

## SpecComponent

| Field | Type |
|-------|------|
| `name` | String |
| `owner` | String |
| `description` | String |
| `script` | SpecScript (uses `@@{param}` syntax) |
| `inputs` (JSON: `input`) | SpecComponentParameter[] |
| `outputs` (JSON: `output`) | SpecComponentParameter[] |

SpecComponentParameter: `{name, type, value, defaultValue, description}`

## All Enums

### LanguageEnum
`odps-sql`, `odps-script`, `hive-sql`, `spark-sql`, `presto-sql`, `trino-sql`, `hologres-sql`, `flink-sql`, `clickhouse-sql`, `mysql-sql`, `adbmysql-sql`, `postgresql-sql`, `t-sql`, `plsql`, `starrocks-sql`, `doris-sql`, `impala-sql`, `obmysql-sql`, `oboracle-sql`, `sql`, `shell-script`, `python2`, `python3`, `json`, `java`, `yaml`

### CalcEngineType
| Engine | ID |
|--------|----|
| General | 0 |
| MaxCompute (ODPS) | 1 |
| EMR | 2 |
| Blink | 3 |
| Hologres | 4 |
| CDH | 11 |
| ClickHouse | 14 |
| Flink | 15 |
| Database | 100 |
| Data Integration | 101 |
| Algorithm | 102 |
| ADB Spark | 10003 |
| Custom | 99999 |

### ArtifactType
`Table`, `File`, `NodeOutput`, `Variable`

### SourceType
`System`, `Manual`, `CodeParse`

### SpecEntityType
`Workflow`, `Node`, `Resource`, `Function`, `Component`
