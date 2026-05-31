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
                "inputs": {"prompt": "Write the advantages of Social Media"},
                "config": {"response_model": {"output": {"advantages": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node2",
                "type": "LLM",
                "inputs": {"prompt": "Write the disadvantages of Social Media"},
                "config": {"response_model": {"output": {"disadvantages": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node3",
                "type": "LLM",
                "inputs": {
                    "prompt": "Merge the advantages and disadvantages to make a essay. Advantages : {groq_llm_node1.outputs.output.advantages} \n Disadvantages : {groq_llm_node2.outputs.output.disadvantages}"
                },
                "config": {"response_model": {"output": {"essay": "str"}}},
                "outputs": {},
            },
            {
                "key": "gmail.send",
                "name": "send_gmail_node1",
                "type": "ACTION",
                "inputs": {
                    "to": ["horizonsjf14@gmail.com"],
                    "subject": "Social Media.",
                    "body": "groq_llm_node3.outputs.output.essay",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            {"source": "start", "target": "groq_llm_node2", "type": "linear"},
            {"source": "groq_llm_node1", "target": "groq_llm_node3", "type": "linear"},
            {"source": "groq_llm_node2", "target": "groq_llm_node3", "type": "linear"},
            {
                "source": "groq_llm_node3",
                "target": "send_gmail_node1",
                "type": "linear",
            },
            {"source": "send_gmail_node1", "target": "end", "type": "linear"},
        ],
    }
    asyncio.run(main(pipeline_str=json.dumps(pipeline)))
