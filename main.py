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
                "key": "llm.google",
                "name": "google_llm_node1",
                "type": "LLM",
                "inputs": {"prompt": "Write the advantages of Social Media"},
                "config": {"response_model": {"output": {"advantages": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "google_llm_node2",
                "type": "LLM",
                "inputs": {"prompt": "Write the disadvantages of Social Media"},
                "config": {"response_model": {"output": {"disadvantages": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "google_llm_node3",
                "type": "LLM",
                "inputs": {
                    "prompt": "Merge the advantages and disadvantages to make a essay. Advantages : {google_llm_node1.outputs.output.advantages} \n Disadvantages : {google_llm_node2.outputs.output.disadvantages}"
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
                    "body": "google_llm_node3.outputs.output.essay",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "google_llm_node1", "type": "linear"},
            {"source": "start", "target": "google_llm_node2", "type": "linear"},
            {
                "source": "google_llm_node1",
                "target": "google_llm_node3",
                "type": "linear",
            },
            {
                "source": "google_llm_node2",
                "target": "google_llm_node3",
                "type": "linear",
            },
            {
                "source": "google_llm_node3",
                "target": "send_gmail_node1",
                "type": "linear",
            },
            {"source": "send_gmail_node1", "target": "end", "type": "linear"},
        ],
    }

    pipeline_with_control_flow = {
        "nodes": [
            {
                "key": "llm.google",
                "name": "google_llm_node1",
                "type": "LLM",
                "inputs": {"prompt": "Generate me 9 outlines for an essay on Nepal."},
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {
                                    "outlines": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    }
                                },
                                "required": ["outlines"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "google_llm_node2",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed essay on the topics: {topics}",
                    "topics": "google_llm_node1.outputs.output.outlines",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {
                                    "article": {"type": "string"},
                                    "word_count": {"type": "integer"},
                                },
                                "required": ["article", "word_count"],
                            }
                        },
                        "required": ["output"],
                    },
                },
                "outputs": {},
            },
            {
                "key": "if_node",
                "name": "quality_gate",
                "type": "CONTROL_FLOW",
                "inputs": {
                    "condition": "word_count >= min_words",
                    "values": {
                        "word_count": "google_llm_node2.outputs.output.word_count",
                        "min_words": 500,
                    },
                },
                "config": {},
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "channel_classifier",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Read the article below and respond with exactly one word "
                        "indicating the best publishing channel: 'blog', 'newsletter', or 'social'.\n\n"
                        "Article: {article}"
                    ),
                    "article": "google_llm_node2.outputs.output.article",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"channel": {"type": "string"}},
                                "required": ["channel"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "rewrite_node",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "The following article is too short. "
                        "Expand it to at least 500 words while preserving the original meaning.\n\n"
                        "Article: {article}"
                    ),
                    "article": "google_llm_node2.outputs.output.article",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"article": {"type": "string"}},
                                "required": ["article"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            {
                "key": "switch_node",
                "name": "channel_router",
                "type": "CONTROL_FLOW",
                "inputs": {
                    "value": "channel_classifier.outputs.output.channel",
                    "cases": ["blog", "newsletter", "social"],
                    "default": "blog",
                },
                "config": {},
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "blog_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": "Format the following article for a blog post with proper headings and SEO meta description:\n\n{article}",
                    "article": "google_llm_node2.outputs.output.article",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"published_content": {"type": "string"}},
                                "required": ["published_content"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "newsletter_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": "Format the following article as an email newsletter with a subject line and preview text:\n\n{article}",
                    "article": "google_llm_node2.outputs.output.article",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"published_content": {"type": "string"}},
                                "required": ["published_content"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            {
                "key": "llm.google",
                "name": "social_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": "Summarise the following article into 3 punchy social media posts (Twitter/LinkedIn):\n\n{article}",
                    "article": "google_llm_node2.outputs.output.article",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"published_content": {"type": "string"}},
                                "required": ["published_content"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
        ],
        "edges": [
            # Linear start
            {"source": "start", "target": "google_llm_node1", "type": "linear"},
            {
                "source": "google_llm_node1",
                "target": "google_llm_node2",
                "type": "linear",
            },
            # Quality gate (if)
            {"source": "google_llm_node2", "target": "quality_gate", "type": "linear"},
            # if True → classify channel
            {
                "source": "quality_gate",
                "target": "channel_classifier",
                "type": "if",
                "decision": True,
            },
            # if False → rewrite
            {
                "source": "quality_gate",
                "target": "rewrite_node",
                "type": "if",
                "decision": False,
            },
            # Both branches converge into the switch
            # (rewrite loops back; classifier feeds the router)
            {
                "source": "channel_classifier",
                "target": "channel_router",
                "type": "linear",
            },
            # switch cases
            {
                "source": "channel_router",
                "target": "blog_publisher",
                "type": "switch",
                "case": "blog",
            },
            {
                "source": "channel_router",
                "target": "newsletter_publisher",
                "type": "switch",
                "case": "newsletter",
            },
            {
                "source": "channel_router",
                "target": "social_publisher",
                "type": "switch",
                "case": "social",
            },
            # All publishers end
            {"source": "blog_publisher", "target": "end", "type": "linear"},
            {"source": "newsletter_publisher", "target": "end", "type": "linear"},
            {"source": "social_publisher", "target": "end", "type": "linear"},
            # Rewrite dead-ends here — you'd reconnect it to quality_gate or end
            {"source": "rewrite_node", "target": "end", "type": "linear"},
        ],
    }
    asyncio.run(main(pipeline_str=json.dumps(pipeline_with_control_flow)))
