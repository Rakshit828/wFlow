from temporalio import workflow, activity
import json
from datetime import timedelta
from typing import Any

with workflow.unsafe.imports_passed_through():
    from src.workflows.types import WorkflowInput, NodeDependency, Pipeline
    from src.workflows.nodes import NODES_MAP
    from src.workflows.pipeline_parser import parse_pipeline
    from src.workflows.utils import resolve_configs, resolve_inputs, topological_sort



@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, inputs: WorkflowInput) -> dict:
        workflow.logger.info("Running the workflow...")
        pipeline: Pipeline = Pipeline(**json.loads(inputs.pipeline_str))
        user_id = inputs.configs.get("user_id", None)
        dependency: NodeDependency = parse_pipeline(pipeline)
        nodes_order = topological_sort(dependency, pipeline.nodes)

        resolved_configs = await resolve_configs(pipeline, user_id)

        print(f"Resolved configs types: {[type(modle) for modle in resolved_configs.values()]}")

        return resolved_configs
