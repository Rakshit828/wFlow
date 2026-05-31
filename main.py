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

    pipeline2 = {
        "nodes": [
            {
                "key": "llm.groq",
                "name": "groq_llm_node1",
                "type": "LLM",
                "inputs": {"prompt": "Generate me 9 outlines for essay on Nepal"},
                "config": {"response_model": {"output": {"outlines": "list.str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node2",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a description on topics {topics}",
                    "topics": "groq_llm_node1.outputs.output.outlines[0] groq_llm_node1.outputs.output.outlines[1] groq_llm_node1.outputs.output.outlines[2]",
                },
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node3",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a description on topics {topics}",
                    "topics": "groq_llm_node1.outputs.output.outlines[3] groq_llm_node1.outputs.output.outlines[4] groq_llm_node1.outputs.output.outlines[5]",
                },
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node4",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a description on topics {topics}",
                    "topics": "groq_llm_node1.outputs.output.outlines[6] groq_llm_node1.outputs.output.outlines[7] groq_llm_node1.outputs.output.outlines[8]",
                },
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node5",
                "type": "LLM",
                "inputs": {
                    "prompt": "Merge these different articles to produce a single best article. Articles are : {articles}",
                    "articles": "groq_llm_node2.outputs.output.article groq_llm_node3.outputs.output.article groq_llm_node4.outputs.output.article",
                },
                "config": {"response_model": {"output": {"final_article": "str"}}},
                "outputs": {},
            },
        ],
        "edges": [
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node2",
                "type": "parallel",
            },
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node3",
                "type": "parallel",
            },
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node4",
                "type": "parallel",
            },
            {"source": "groq_llm_node2", "target": "groq_llm_node5", "type": "linear"},
            {"source": "groq_llm_node3", "target": "groq_llm_node5", "type": "linear"},
            {"source": "groq_llm_node4", "target": "groq_llm_node5", "type": "linear"},
            {"source": "groq_llm_node5", "target": "end", "type": "linear"},

        ],
    }
    asyncio.run(main(pipeline_str=json.dumps(pipeline2)))
