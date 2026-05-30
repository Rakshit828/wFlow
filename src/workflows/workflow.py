from temporalio import workflow, activity
import json
from datetime import timedelta
from typing import Any

with workflow.unsafe.imports_passed_through():
    from src.workflows.types import WorkflowInput, NodeDependency, Pipeline, Node
    from src.workflows.nodes import NODES_MAP
    from src.workflows.pipeline_parser import parse_pipeline
    from src.workflows.utils import resolve_configs, resolve_inputs, topological_sort


@activity.defn
async def resolve_configs_activity(inputs: WorkflowInput) -> dict[str, Any]:

    pipeline_str = inputs.pipeline_str
    user_id = inputs.configs.get("user_id", None)

    pipeline = Pipeline(**json.loads(pipeline_str))
    resolved_configs = await resolve_configs(pipeline, user_id)
    activity.logger.info(f"Configs resolved for {len(resolved_configs)} nodes")

    return resolved_configs


@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, inputs: WorkflowInput) -> dict:
        workflow.logger.info("Running the workflow...")
        pipeline: Pipeline = Pipeline(**json.loads(inputs.pipeline_str))
        dependency: NodeDependency = parse_pipeline(pipeline)
        nodes_order = topological_sort(dependency, pipeline.nodes)

        workflow.logger.info(f"Execution order: {nodes_order}")

        # Step 1: Resolve configurations for all nodes
        resolved_configs = await workflow.execute_activity(
            resolve_configs_activity,
            inputs,
            start_to_close_timeout=timedelta(seconds=300),
        )
        workflow.logger.info(f"Configurations resolved for {len(resolved_configs)} nodes")

        # Step 2: Execute nodes in topological order
        outputs = {}
        for node_name in nodes_order:
            # Find the node in the pipeline by name
            node: Node = next(
                (n for n in pipeline.nodes if n.name == node_name),
                None
            )
            node_def = NODES_MAP.get(node.key)
            
            if not node:
                workflow.logger.error(f"Node {node_name} not found in pipeline")
                continue

            if not node_def:
                raise ValueError(f"Node {node.key} not found in NODES_MAP")
            

            resolved_node_inputs = resolve_inputs(node.inputs, outputs)

            if not "config" in resolved_node_inputs:
                resolved_node_inputs.update({"config": {}})

            if resolved_configs.get(node.key):
                resolved_node_inputs["config"].update(resolved_configs.get(node.key))
            if node.config:
                resolved_node_inputs["config"].update(node.config)
            
            full_input_model = node_def.node_input_model(**resolved_node_inputs)
            
            # Execute the node activity
            node_output = await workflow.execute_activity(
                node_def.fn,
                full_input_model,
                start_to_close_timeout=timedelta(seconds=300),
            )

            outputs[node_name] = node_output
            workflow.logger.info(f"Node '{node_name}' completed successfully")

        workflow.logger.info("Workflow completed successfully")
        return {
            "outputs": outputs,
            "resolved_configs": resolved_configs,
        }
