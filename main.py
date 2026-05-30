import asyncio
import json
import uuid
from temporalio.client import Client
from src.workflows.types import WorkflowInput


async def main(pipeline_str: str):

    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        "DynamicWorkflow",
        WorkflowInput(
            pipeline_str=pipeline_str, configs={"user_id": "69ea34d032f5e9adcfbabe33"}
        ),
        id=f"dynamic-workflow-{uuid.uuid4()}",
        task_queue="default",
    )

    print("Workflow result:", result)


if __name__ == "__main__":
    pipeline = {
        "nodes": [
            {
                "key": "llm.groq",
                "name": "groq_llm_node1",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a essay on political situation of Nepal."
                },
                "config": {"response_model": {"output": {"essay": "str"}}},
                "outputs": {},
            },
            {
                "key": "gmail.send",
                "name": "send_gmail_node1",
                "type": "ACTION",
                "inputs": {
                    "to": ["bhattarianita2014@gmail.com"],
                    "subject": "Nepal Current Politics",
                    "body": "groq_llm_node1.outputs.output.essay",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            {
                "source": "groq_llm_node1",
                "target": "send_gmail_node1",
                "type": "linear",
            },
            {"source": "send_gmail_node1", "target": "end", "type": "linear"},
        ],
    }
    asyncio.run(main(pipeline_str=json.dumps(pipeline)))
