"""
FlowSpec Patcher — 模板填充与增量 Patch 工具

三种操作模式:
1. create: 从模板填充业务变量，生成新的 FlowSpec
2. update: 读取现有 Spec，只修改指定字段（增量更新）
3. import_wf: 组装工作流 Spec，管理节点 ID 策略

用法:
    from patcher import SpecPatcher
    patcher = SpecPatcher(templates_dir='path/to/templates')

    # 创建新节点
    spec = patcher.create_node('ODPS_SQL', {
        'node_name': 'daily_report',
        'script_path': '业务流程/report/daily_report',
        'sql_content': 'SELECT * FROM t WHERE dt="${bizdate}";',
        'cron_expression': '00 00 06 * * ?',
        'datasource_name': 'odps_first',
        'resource_group': 'S_res_group_xxx',
        'input_dependency': 'project_root',
        'output_name': 'project.daily_report',
    })

    # 增量更新（只改变的字段）
    patch = patcher.create_update_patch(existing_spec, {
        'script.content': 'SELECT count(*) FROM t;',
        'trigger.cron': '00 30 07 * * ?',
    })

    # 组装工作流
    wf_spec = patcher.assemble_workflow(nodes_specs, flow_deps, id_policy='omit_for_create')
"""

import json
import copy
import os
from pathlib import Path


class SpecPatcher:
    def __init__(self, templates_dir=None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.templates_dir = Path(templates_dir)
        self._template_cache = {}

    def _load_template(self, node_type: str) -> dict:
        """加载节点类型的 JSON 模板"""
        if node_type in self._template_cache:
            return copy.deepcopy(self._template_cache[node_type])

        template_path = self.templates_dir / f'{node_type}.json'
        if not template_path.exists():
            raise FileNotFoundError(
                f"模板 {template_path} 不存在。\n"
                f"请先在 DataWorks 控制台创建 {node_type} 类型节点，"
                f"点击'显示 Spec'导出，保存到 {template_path}"
            )

        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        self._template_cache[node_type] = template
        return copy.deepcopy(template)

    def create_node(self, node_type: str, variables: dict) -> dict:
        """
        从模板创建新节点 Spec。

        Args:
            node_type: 节点类型（如 'ODPS_SQL', 'DIDE_SHELL'），必须在 templates/ 有对应模板
            variables: 业务变量，key 是模板中的 {{placeholder}} 名称

        Returns:
            填充后的 FlowSpec dict
        """
        template = self._load_template(node_type)
        spec_str = json.dumps(template, ensure_ascii=False)

        # 替换所有 {{placeholder}}
        for key, value in variables.items():
            placeholder = '{{' + key + '}}'
            if isinstance(value, str):
                # JSON 字符串中的特殊字符需要转义
                escaped_value = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                spec_str = spec_str.replace(placeholder, escaped_value)
            else:
                spec_str = spec_str.replace(f'"{placeholder}"', json.dumps(value, ensure_ascii=False))

        result = json.loads(spec_str)

        # 清理未填充的 placeholder — 移除包含 {{ 的字段
        self._clean_unfilled(result)

        return result

    def create_update_patch(self, existing_spec: dict, changes: dict) -> dict:
        """
        基于现有 Spec 创建增量更新 patch。

        只修改 changes 中指定的字段，保留其他字段不变。
        支持点号路径（如 'script.content', 'trigger.cron'）。

        Args:
            existing_spec: 现有的 FlowSpec dict（通常从 GetNode 获取）
            changes: 要修改的字段，{dotted_path: new_value}

        Returns:
            最小化的增量更新 FlowSpec（只包含 version/kind/spec + 变更字段）
        """
        patch = {
            'version': '1.1.0',
            'kind': existing_spec.get('kind', 'Node'),
            'spec': {
                'nodes': [{}]
            }
        }

        node_patch = patch['spec']['nodes'][0]

        for dotted_path, value in changes.items():
            self._set_nested(node_patch, dotted_path, value)

        return patch

    def assemble_workflow(
        self,
        node_specs: list,
        flow_deps: list = None,
        id_policy: str = 'omit_for_create',
        workflow_kind: str = 'CycleWorkflow',
        metadata: dict = None,
    ) -> dict:
        """
        组装工作流 Spec。

        Args:
            node_specs: 节点定义列表，每个元素是 create_node 返回的 spec 中 nodes[0]
            flow_deps: 依赖关系列表，格式: [{'nodeId': 'B', 'depends': [{'nodeId': 'A', 'type': 'Normal'}]}]
            id_policy: ID 策略
                - 'omit_for_create': 删除所有 id 字段（新建）
                - 'reuse_existing': 保留已有 id（更新）
                - 'use_name_as_id': 用 name 作为临时 id（用于 flow 引用）
            workflow_kind: 'CycleWorkflow' 或 'ManualWorkflow'
            metadata: 工作流元数据 {'owner': '...', 'description': '...'}

        Returns:
            完整的工作流 FlowSpec dict
        """
        nodes = []
        for i, spec in enumerate(node_specs):
            # 从完整 spec 中提取 node 定义
            if 'spec' in spec and 'nodes' in spec['spec']:
                node = copy.deepcopy(spec['spec']['nodes'][0])
            else:
                node = copy.deepcopy(spec)

            # 应用 ID 策略
            if id_policy == 'omit_for_create':
                node.pop('id', None)
            elif id_policy == 'use_name_as_id':
                node['id'] = node.get('name', f'node_{i}')

            nodes.append(node)

        workflow = {
            'version': '1.1.0',
            'kind': workflow_kind,
            'spec': {
                'nodes': nodes,
                'flow': flow_deps or [],
            }
        }

        if metadata:
            workflow['metadata'] = metadata

        return workflow

    def patch_existing_node(self, existing_spec: dict, changes: dict) -> dict:
        """
        在现有 Spec 上做 AST 级 patch — 保留所有未修改字段。

        与 create_update_patch 不同，这个方法返回完整的 Spec（不是最小 patch），
        适用于需要完整 Spec 的场景。

        Args:
            existing_spec: 现有的完整 FlowSpec
            changes: 要修改的字段 {dotted_path: new_value}

        Returns:
            修改后的完整 FlowSpec
        """
        result = copy.deepcopy(existing_spec)

        if 'spec' in result and 'nodes' in result['spec'] and result['spec']['nodes']:
            node = result['spec']['nodes'][0]
            for dotted_path, value in changes.items():
                self._set_nested(node, dotted_path, value)

        return result

    @staticmethod
    def _set_nested(obj: dict, dotted_path: str, value):
        """设置嵌套字典中的值，如 'script.content' → obj['script']['content']"""
        keys = dotted_path.split('.')
        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[keys[-1]] = value

    @staticmethod
    def _clean_unfilled(obj):
        """递归移除包含未填充 {{...}} 占位符的值"""
        if isinstance(obj, dict):
            keys_to_remove = []
            for key, value in obj.items():
                if isinstance(value, str) and '{{' in value:
                    keys_to_remove.append(key)
                elif isinstance(value, (dict, list)):
                    SpecPatcher._clean_unfilled(value)
            for key in keys_to_remove:
                del obj[key]
        elif isinstance(obj, list):
            items_to_remove = []
            for i, item in enumerate(obj):
                if isinstance(item, str) and '{{' in item:
                    items_to_remove.append(i)
                elif isinstance(item, (dict, list)):
                    SpecPatcher._clean_unfilled(item)
            for i in reversed(items_to_remove):
                obj.pop(i)


def create_emr_content(job_type: str, code: str, queue: str = 'default', priority: str = '1') -> str:
    """
    生成 EMR 节点的 script.content（EmrCode JSON 字符串）。

    Args:
        job_type: EmrJobType, 如 'HIVE_SQL', 'SPARK_SQL', 'SHELL'
        code: 实际的 SQL/Shell 代码
        queue: YARN 队列名
        priority: 优先级

    Returns:
        EmrCode JSON 字符串
    """
    emr_code = {
        'type': job_type,
        'launcher': {
            'allocationSpec': {
                'DATAWORKS_SESSION_DISABLE': False,
                'priority': priority,
                'queue': queue,
            }
        },
        'properties': {
            'envs': {},
            'arguments': [code],
            'tags': [],
        }
    }
    return json.dumps(emr_code, ensure_ascii=False)
