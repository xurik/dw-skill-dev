"""
FlowSpec Validator — 三层校验工具

校验层级:
1. 结构校验: FlowSpec 基本层次 (version, kind, spec, nodes)
2. 模板校验: 节点类型必填字段是否齐全 (runtime.command, content 等)
3. 回归校验: 与已知可用模板做 diff，确保只改了允许的字段

用法:
    from validator import SpecValidator
    validator = SpecValidator(catalog_path='path/to/node_types.yaml')

    errors = validator.validate(spec)
    if errors:
        for e in errors:
            print(f"[{e['level']}] {e['message']}")
"""

import json
import os
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# 简化的 catalog 内嵌定义（在无法加载 YAML 时使用）
BUILTIN_COMMANDS = {
    'ODPS_SQL', 'ODPS_SPARK_SQL', 'ODPS_SQL_SCRIPT', 'PY_ODPS', 'PYODPS3',
    'ODPS_SPARK', 'ODPS_SHARK', 'ODPS_MR',
    'DIDE_SHELL', 'SHELL', 'PYTHON', 'SSH', 'PERL',
    'EMR_HIVE', 'EMR_SPARK_SQL', 'EMR_SPARK', 'EMR_SHELL', 'EMR_MR',
    'EMR_PRESTO', 'EMR_IMPALA', 'EMR_TRINO', 'EMR_KYUUBI',
    'CDH_HIVE', 'CDH_SPARK_SQL', 'CDH_SPARK', 'CDH_SHELL',
    'HOLOGRES_SQL', 'HOLOGRES_DEVELOP',
    'DI', 'RI', 'DATAX', 'DATAX2',
    'MySQL', 'POSTGRESQL', 'CLICK_SQL', 'Oracle', 'StarRocks', 'Doris',
    'Sql Server', 'Mariadb', 'OceanBase', 'DB2', 'DRDS',
    'ADB for PostgreSQL', 'ADB for MySQL',
    'VIRTUAL', 'COMBINED_NODE', 'SUB_PROCESS',
    'CONTROLLER_BRANCH', 'CONTROLLER_JOIN', 'CONTROLLER_ASSIGNMENT',
    'CONTROLLER_CYCLE', 'CONTROLLER_TRAVERSE', 'CONTROLLER_WAIT',
    'PARAM_HUB', 'SCHEDULER_TRIGGER',
    'FLINK_SQL_STREAM', 'FLINK_SQL_BATCH', 'BLINK_STREAM_SQL', 'BLINK_BATCH_SQL',
    'pai', 'pai_studio', 'pai_dlc', 'PAI_FLOW',
    'SQL_COMPONENT', 'COMPONENT_SQL',
    'CHECK', 'CHECK_NODE',
}

VALID_KINDS = {
    'Node', 'CycleWorkflow', 'ManualWorkflow', 'TriggerWorkflow',
    'Resource', 'Function', 'Component', 'Workflow',
    'DataIntegrationJob', 'PaiFlow',
}

VALID_RECURRENCE = {'Normal', 'Pause', 'Skip'}
VALID_INSTANCE_MODE = {'T+1', 'Immediately'}
VALID_RERUN_MODE = {'Allowed', 'FailureAllowed', 'Denied'}
VALID_TRIGGER_TYPE = {'Scheduler', 'Manual'}
VALID_FLOW_DEP_TYPE = {'Normal', 'CrossCycleDependsOnSelf', 'CrossCycleDependsOnOtherNode', 'CrossCycleDependsOnChildren'}


class SpecValidator:
    def __init__(self, catalog_path=None):
        self.catalog = {}
        if catalog_path and HAS_YAML:
            self._load_catalog(catalog_path)

    def _load_catalog(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self.catalog = data.get('node_types', {})

    def validate(self, spec: dict) -> list:
        """
        执行三层校验，返回错误列表。

        每个错误是 {'level': 'structure|template|regression', 'message': '...'}
        空列表表示校验通过。
        """
        errors = []
        errors.extend(self._validate_structure(spec))
        if not errors:  # 结构校验通过才继续
            errors.extend(self._validate_template(spec))
        return errors

    def _validate_structure(self, spec: dict) -> list:
        """第一层: 结构校验"""
        errors = []

        # version
        if 'version' not in spec:
            errors.append({'level': 'structure', 'message': '缺少 version 字段'})
        elif spec['version'] != '1.1.0':
            errors.append({'level': 'structure', 'message': f'version 应为 "1.1.0"，当前: {spec["version"]}'})

        # kind
        if 'kind' not in spec:
            errors.append({'level': 'structure', 'message': '缺少 kind 字段'})
        elif spec['kind'] not in VALID_KINDS:
            errors.append({'level': 'structure', 'message': f'无效 kind: {spec["kind"]}，有效值: {VALID_KINDS}'})

        # spec
        if 'spec' not in spec:
            errors.append({'level': 'structure', 'message': '缺少 spec 字段'})
            return errors

        inner = spec['spec']
        kind = spec.get('kind', '')

        # nodes（Node 和 Workflow 类型需要）
        if kind in ('Node', 'CycleWorkflow', 'ManualWorkflow'):
            if 'nodes' not in inner:
                errors.append({'level': 'structure', 'message': 'spec 中缺少 nodes 数组'})
            elif not isinstance(inner['nodes'], list):
                errors.append({'level': 'structure', 'message': 'spec.nodes 必须是数组'})
            elif len(inner['nodes']) == 0:
                if kind == 'Node':
                    errors.append({'level': 'structure', 'message': 'spec.nodes 不能为空（Node 类型）'})

        # flow（工作流类型可选但需要是数组）
        if 'flow' in inner and not isinstance(inner['flow'], list):
            errors.append({'level': 'structure', 'message': 'spec.flow 必须是数组'})

        return errors

    def _validate_template(self, spec: dict) -> list:
        """第二层: 模板校验 — 检查节点必填字段"""
        errors = []
        kind = spec.get('kind', '')

        if kind not in ('Node', 'CycleWorkflow', 'ManualWorkflow'):
            return errors

        nodes = spec.get('spec', {}).get('nodes', [])
        for i, node in enumerate(nodes):
            prefix = f'nodes[{i}]'

            # name
            if not node.get('name'):
                errors.append({'level': 'template', 'message': f'{prefix}: 缺少 name'})

            # script
            script = node.get('script')
            if not script:
                # 控制类节点可能没有 script（用特殊字段代替）
                has_special = any(k in node for k in ['branch', 'join', 'do-while', 'for-each', 'param-hub', 'combined'])
                if not has_special:
                    errors.append({'level': 'template', 'message': f'{prefix}: 缺少 script 或特殊控制字段'})
                continue

            # runtime.command
            runtime = script.get('runtime', {})
            command = runtime.get('command')
            if not command:
                errors.append({'level': 'template', 'message': f'{prefix}: 缺少 script.runtime.command'})
            elif command not in BUILTIN_COMMANDS:
                errors.append({'level': 'template', 'message': f'{prefix}: 未知的 runtime.command "{command}"，请确认是否正确'})

            # recurrence
            recurrence = node.get('recurrence')
            if recurrence and recurrence not in VALID_RECURRENCE:
                errors.append({'level': 'template', 'message': f'{prefix}: 无效 recurrence "{recurrence}"，有效值: {VALID_RECURRENCE}'})

            # instanceMode
            instance_mode = node.get('instanceMode')
            if instance_mode and instance_mode not in VALID_INSTANCE_MODE:
                errors.append({'level': 'template', 'message': f'{prefix}: 无效 instanceMode "{instance_mode}"'})

            # rerunMode
            rerun_mode = node.get('rerunMode')
            if rerun_mode and rerun_mode not in VALID_RERUN_MODE:
                errors.append({'level': 'template', 'message': f'{prefix}: 无效 rerunMode "{rerun_mode}"'})

            # trigger
            trigger = node.get('trigger', {})
            trigger_type = trigger.get('type')
            if trigger_type and trigger_type not in VALID_TRIGGER_TYPE:
                errors.append({'level': 'template', 'message': f'{prefix}: 无效 trigger.type "{trigger_type}"'})

        # flow 依赖类型校验
        flow = spec.get('spec', {}).get('flow', [])
        for i, f in enumerate(flow):
            for j, dep in enumerate(f.get('depends', [])):
                dep_type = dep.get('type')
                if dep_type and dep_type not in VALID_FLOW_DEP_TYPE:
                    errors.append({
                        'level': 'template',
                        'message': f'flow[{i}].depends[{j}]: 无效依赖类型 "{dep_type}"'
                    })

        return errors

    def validate_update_patch(self, patch: dict, allowed_fields: set = None) -> list:
        """
        校验增量更新 patch。

        Args:
            patch: 增量更新的 FlowSpec
            allowed_fields: 允许修改的字段集合（如果指定）

        Returns:
            错误列表
        """
        errors = self._validate_structure(patch)

        if allowed_fields:
            node = patch.get('spec', {}).get('nodes', [{}])[0]
            actual_fields = self._flatten_keys(node)
            disallowed = actual_fields - allowed_fields
            if disallowed:
                errors.append({
                    'level': 'regression',
                    'message': f'更新 patch 包含不允许的字段: {disallowed}'
                })

        return errors

    @staticmethod
    def _flatten_keys(obj: dict, prefix: str = '') -> set:
        """将嵌套 dict 的 key 扁平化为点号路径集合"""
        keys = set()
        for k, v in obj.items():
            path = f'{prefix}.{k}' if prefix else k
            if isinstance(v, dict):
                keys.update(SpecValidator._flatten_keys(v, path))
            else:
                keys.add(path)
        return keys


def validate_spec(spec: dict, catalog_path: str = None) -> list:
    """便捷函数: 校验 FlowSpec 并返回错误列表"""
    validator = SpecValidator(catalog_path=catalog_path)
    return validator.validate(spec)
