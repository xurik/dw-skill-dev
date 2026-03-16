# DataWorks Public API Reference (2024-05-18)

Complete parameter and response reference for all DataWorks data development APIs.

**Base endpoint**: `dataworks.<region>.aliyuncs.com`
**Authentication**: AccessKey ID + Secret (AK)
**SDK package**: `alibabacloud_dataworks_public20240518`

---

## Table of Contents

1. [Nodes (节点)](#nodes)
2. [Workflows (工作流)](#workflows)
3. [Components (组件)](#components)
4. [Resources (文件资源)](#resources)
5. [Functions (UDF函数)](#functions)
6. [Pipeline Runs (发布流程)](#pipeline-runs)

---

## Nodes

### CreateNode

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | DataWorks workspace ID |
| Scene | string | Yes | formData | `DATAWORKS_PROJECT`, `DATAWORKS_MANUAL_WORKFLOW`, `DATAWORKS_MANUAL_TASK` |
| Spec | string | Yes | formData | FlowSpec JSON (kind: "Node") |
| ContainerId | string | No | formData | Container (workflow/container node) ID; overrides FlowSpec path |

**Response**: `{ "RequestId": "string", "Id": "string" }`

**Notes**: Only processes the first node in FlowSpec. ContainerId type is String (SDK v8.0.0+).

### GetNode

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Node ID |
| ProjectId | int64 | No | query | Workspace ID |

**Response**:
```
{
  "RequestId": "string",
  "Node": {
    "Id": "string",
    "Name": "string",
    "ProjectId": int64,
    "Owner": "string",
    "Spec": "string (FlowSpec JSON)",
    "TaskId": int64,
    "CreateTime": int64 (ms timestamp),
    "ModifyTime": int64 (ms timestamp)
  }
}
```

### ListNodes

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Scene | string | No | query | `DataworksProject`, `DataworksManualWorkflow`, `DataworksManualTask` |
| ContainerId | string | No | query | Filter by container |
| Recurrence | string | No | query | `Normal`, `Pause`, `Skip` |
| RerunMode | string | No | query | `Allowed`, `FailureAllowed`, `Denied` |
| Name | string | No | query | Fuzzy match by name |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**:
```
{
  "RequestId": "string",
  "PagingInfo": {
    "TotalCount": "string",
    "PageSize": "string",
    "PageNumber": "string",
    "Nodes": [
      {
        "Id": "string",
        "Name": "string",
        "Description": "string",
        "ProjectId": int64,
        "Owner": "string",
        "CreateTime": int64,
        "ModifyTime": int64,
        "DataSource": { "Name": "string", "Type": "string" },
        "TaskId": int64,
        "Recurrence": "string",
        "Strategy": {
          "Timeout": int32,
          "InstanceMode": "string",
          "RerunMode": "string",
          "RerunTimes": int32,
          "RerunInterval": int32
        },
        "Script": { ... },
        "Trigger": { ... },
        "RuntimeResource": { ... },
        "Inputs": { ... },
        "Outputs": { ... }
      }
    ]
  }
}
```

### UpdateNode

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Node ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Incremental FlowSpec JSON — only include changed fields |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### DeleteNode

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Node ID |
| ProjectId | int64 | Yes | formData | Workspace ID |

**Response**: `{ "RequestId": "string", "Success": boolean }`

**Constraint**: Cannot delete published nodes. Published nodes must be taken offline first (via pipeline run with `type='Offline'`).

### MoveNode

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Node ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Path | string | Yes | formData | Target path in DataWorks directory |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### RenameNode

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Node ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Name | string | Yes | formData | New node name |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### ListNodeDependencies

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Node ID |
| ProjectId | int64 | Yes | query | Workspace ID |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: Same paging structure as ListNodes, with dependent nodes listed.

---

## Workflows

### CreateWorkflowDefinition

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | FlowSpec JSON (kind: "CycleWorkflow" or "ManualWorkflow") |

**Response**: `{ "RequestId": "string", "Id": "string" }`

### ImportWorkflowDefinition

**Method**: POST | **Auth**: AK | **Async**: Yes (poll via GetJobStatus)

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Complete FlowSpec with all nodes and dependencies. If entity ID exists, it updates; otherwise creates. |

**Response**:
```
{
  "RequestId": "string",
  "AsyncJob": {
    "Id": "string",
    "Completed": boolean,
    "Status": "string",  // Running, Success, Fail, Cancel
    "Progress": int32,   // 0-100
    "Response": "string", // Created workflow ID on success
    "Error": "string"
  }
}
```

**Notes**: This is an **async API**. Poll `GetJobStatus` (interval: 1s, max 10 attempts) to check completion. Only the first workflow in the FlowSpec is processed.

### GetWorkflowDefinition

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Workflow ID |
| ProjectId | int64 | No | query | Workspace ID |
| IncludeScriptContent | boolean | No | query | Whether to include script content of internal nodes (may increase latency) |

**Response**:
```
{
  "RequestId": "string",
  "WorkflowDefinition": {
    "Id": "string",
    "Name": "string",
    "ProjectId": int64,
    "Owner": "string",
    "Spec": "string (FlowSpec JSON)",
    "WorkflowId": int64,  // scheduling-side ID after publishing
    "CreateTime": int64,
    "ModifyTime": int64
  }
}
```

### ListWorkflowDefinitions

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Type | string | No | query | `CycleWorkflow` or `ManualWorkflow` |
| Name | string | No | query | Fuzzy match |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: PagingInfo with WorkflowDefinitions array.

### UpdateWorkflowDefinition

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Workflow ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Incremental FlowSpec JSON |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### DeleteWorkflowDefinition

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Workflow ID |
| ProjectId | int64 | Yes | formData | Workspace ID |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### MoveWorkflowDefinition

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Workflow ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Path | string | Yes | formData | Target path |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### RenameWorkflowDefinition

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Workflow ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Name | string | Yes | formData | New workflow name |

**Response**: `{ "RequestId": "string", "Success": boolean }`

---

## Components

### CreateComponent

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Component FlowSpec JSON |

**Response**: `{ "RequestId": "string", "Id": "string" }`

### GetComponent

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Component ID |
| ProjectId | int64 | No | query | Workspace ID |

**Response**: Component object with Id, Name, Spec, Owner, timestamps.

### ListComponents

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Name | string | No | query | Fuzzy match |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: PagingInfo with Components array.

### UpdateComponent

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Component ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Incremental FlowSpec JSON |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### DeleteComponent

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Component ID |
| ProjectId | int64 | Yes | formData | Workspace ID |

**Response**: `{ "RequestId": "string", "Success": boolean }`

---

## Resources

### CreateResource

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Resource FlowSpec JSON |
| ResourceFile | string | No | formData | File stream or OSS download URL for resource content |

**Response**: `{ "RequestId": "string", "Id": "string" }`

**Notes**: Only the first resource in the FlowSpec is created. Spec should include `type` (e.g., `"python"`, `"jar"`, `"file"`) and `datasource` info.

### GetResource

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Resource ID |
| ProjectId | int64 | No | query | Workspace ID |

**Response**: Resource object with Id, Name, Spec, Owner, timestamps.

### ListResources

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Name | string | No | query | Fuzzy match |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: PagingInfo with Resources array.

### UpdateResource

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Resource ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Incremental FlowSpec JSON |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### DeleteResource

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Resource ID |
| ProjectId | int64 | Yes | formData | Workspace ID |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### MoveResource

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Resource ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Path | string | Yes | formData | Target path |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### RenameResource

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Resource ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Name | string | Yes | formData | New resource name |

**Response**: `{ "RequestId": "string", "Success": boolean }`

---

## Functions

### CreateFunction

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Function FlowSpec JSON |

**Response**: `{ "RequestId": "string", "Id": "string" }`

### GetFunction

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Function ID |
| ProjectId | int64 | No | query | Workspace ID |

**Response**: Function object with Id, Name, Spec, Owner, timestamps.

### ListFunctions

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Name | string | No | query | Fuzzy match |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: PagingInfo with Functions array.

### UpdateFunction

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Function ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Spec | string | Yes | formData | Incremental FlowSpec JSON |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### DeleteFunction

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Function ID |
| ProjectId | int64 | Yes | formData | Workspace ID |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### MoveFunction

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Function ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Path | string | Yes | formData | Target path |

**Response**: `{ "RequestId": "string", "Success": boolean }`

### RenameFunction

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Function ID |
| ProjectId | int64 | Yes | formData | Workspace ID |
| Name | string | Yes | formData | New function name |

**Response**: `{ "RequestId": "string", "Success": boolean }`

---

## Pipeline Runs

### CreatePipelineRun

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | formData | Workspace ID |
| Type | string | Yes | formData | `Online` (deploy) or `Offline` (undeploy) |
| ObjectIds | array[string] | Yes | formData | Entity IDs to publish (min: 1, max: 10). Only the first entity + its children are actually published. |
| Description | string | No | formData | Deployment description |

**Response**: `{ "RequestId": "string", "Id": "string" }`

**Notes**: Only the first entity in ObjectIds is processed; the rest are ignored.

### GetPipelineRun

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Pipeline run ID |
| ProjectId | int64 | Yes | query | Workspace ID |

**Response**:
```
{
  "RequestId": "string",
  "PipelineRun": {
    "Id": "string",
    "ProjectId": int64,
    "Status": "string",  // Init, Running, Success, Fail, Termination, Cancel
    "Creator": "string",
    "CreateTime": int64,
    "ModifyTime": int64,
    "Description": "string",
    "Stages": [
      {
        "Code": "string",
        "Name": "string",
        "Status": "string",
        "Detail": "string"
      }
    ]
  }
}
```

### ListPipelineRuns

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Status | string | No | query | Filter: `Init`, `Running`, `Success`, `Fail`, `Termination`, `Cancel` |
| Creator | string | No | query | Filter by creator |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: PagingInfo with PipelineRuns array.

### ListPipelineRunItems

**Method**: GET | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | query | Pipeline run ID |
| ProjectId | int64 | Yes | query | Workspace ID |
| PageNumber | int32 | No | query | Default: 1 |
| PageSize | int32 | No | query | Default: 10, Max: 100 |

**Response**: PagingInfo with deployment item details.

### ExecPipelineRunStage

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| ProjectId | int64 | Yes | query | Workspace ID |
| Id | string | Yes | formData | Pipeline run ID |
| Code | string | Yes | formData | Stage code (from GetPipelineRun response) |

**Response**: `{ "RequestId": "string", "Success": boolean }`

**Notes**: Stages must be executed in order. Response is async — use GetPipelineRun to check actual completion.

### AbolishPipelineRun

**Method**: POST | **Auth**: AK

| Parameter | Type | Required | Location | Description |
|-----------|------|----------|----------|-------------|
| Id | string | Yes | formData | Pipeline run ID |
| ProjectId | int64 | Yes | formData | Workspace ID |

**Response**: `{ "RequestId": "string", "Success": boolean }`

**Notes**: Sets status to terminated but does not delete the pipeline run. Still queryable via Get/List APIs.

---

## Common Patterns

### Pagination

All List APIs use:
- `PageNumber` (int32, default 1, min 1)
- `PageSize` (int32, default 10, max 100)

Response PagingInfo always contains: `TotalCount`, `PageSize`, `PageNumber`, plus the data array.

### Error Codes

Common error patterns from the API:
- `InvalidParameterValue` — invalid parameter value
- `ResourceNotFound` — entity not found
- `Forbidden` — insufficient permissions
- `InternalError` — server error, retry with exponential backoff
- `Throttling` — rate limited, retry after delay

### FlowSpec Version

Always use `"version": "1.1.0"` for the current API version.

### SDK Method Naming Convention

Python SDK methods use snake_case:
- `CreateNode` → `client.create_node()`
- `GetWorkflowDefinition` → `client.get_workflow_definition()`
- `ListPipelineRuns` → `client.list_pipeline_runs()`
- `ExecPipelineRunStage` → `client.exec_pipeline_run_stage()`

Request classes follow PascalCase: `CreateNodeRequest`, `ListNodesRequest`, etc.
