import asyncio
import json
import uuid
from temporalio.client import Client
from src.workflows.types import WorkflowInput


async def main(workflow_str: str):

    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        "DynamicWorkflow",
        WorkflowInput(
            workflow_str=workflow_str, configs={"user_id": "69ea34d032f5e9adcfbabe33"}
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
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node3",
                "type": "linear",
            },
            {
                "source": "groq_llm_node2",
                "target": "groq_llm_node3",
                "type": "linear",
            },
            {
                "source": "groq_llm_node3",
                "target": "send_gmail_node1",
                "type": "linear",
            },
            {"source": "send_gmail_node1", "target": "end", "type": "linear"},
        ],
    }
    drive_upload_pipeline = {
        "nodes": [
            {
                "key": "llm.groq",
                "name": "groq_llm_node1",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me very very short essay on Social Media."
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"essay": {"type": "string"}},
                                "required": ["essay"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            {
                "key": "drive.upload",
                "name": "drive_upload_node1",
                "type": "ACTION",
                "inputs": {
                    "content_ref": "groq_llm_node1.outputs.output.essay",
                    "filename": "social_media_essay.txt",
                    "mime_type": "text/plain",
                },
            },
        ],
        "edges": [
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            {
                "source": "groq_llm_node1",
                "target": "drive_upload_node1",
                "type": "linear",
            },
            {"source": "drive_upload_node1", "target": "end", "type": "linear"},
        ],
    }
    pipeline_with_control_flow = {
        "nodes": [
            # ── Step 1: Generate 9 outlines ───────────────────────────────────────
            {
                "key": "llm.groq",
                "name": "groq_llm_node1",
                "type": "LLM",
                "inputs": {"prompt": "Generate me 9 outlines for an essay on Nepal."},
                "config": {
                    "response_model": {
                        "name": "outline_model",
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
            # ── Step 2: Write 3 article sections in parallel ──────────────────────
            {
                "key": "llm.groq",
                "name": "groq_llm_node2",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed article section on these topics: {topics}",
                    "topics": (
                        "groq_llm_node1.outputs.output.outlines[0] "
                        "groq_llm_node1.outputs.output.outlines[1] "
                        "groq_llm_node1.outputs.output.outlines[2]"
                    ),
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
                "key": "llm.groq",
                "name": "groq_llm_node3",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed article section on these topics: {topics}",
                    "topics": (
                        "groq_llm_node1.outputs.output.outlines[3] "
                        "groq_llm_node1.outputs.output.outlines[4] "
                        "groq_llm_node1.outputs.output.outlines[5]"
                    ),
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
                "key": "llm.groq",
                "name": "groq_llm_node4",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed article section on these topics: {topics}",
                    "topics": (
                        "groq_llm_node1.outputs.output.outlines[6] "
                        "groq_llm_node1.outputs.output.outlines[7] "
                        "groq_llm_node1.outputs.output.outlines[8]"
                    ),
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
            # ── Step 3: Merge all sections into one final article ─────────────────
            {
                "key": "llm.groq",
                "name": "groq_llm_node5",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Merge these article sections into one cohesive final article: {articles}"
                    ),
                    "articles": (
                        "groq_llm_node2.outputs.output.article "
                        "groq_llm_node3.outputs.output.article "
                        "groq_llm_node4.outputs.output.article"
                    ),
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {
                                    "final_article": {"type": "string"},
                                    "word_count": {"type": "integer"},
                                },
                                "required": ["final_article", "word_count"],
                            }
                        },
                        "required": ["output"],
                    }
                },
                "outputs": {},
            },
            # ── Step 4: Quality gate — is the article long enough? ────────────────
            {
                "key": "if_node",
                "name": "quality_gate",
                "type": "CONTROL_FLOW",
                "inputs": {
                    "condition": "word_count >= min_words",
                    "values": {
                        "word_count": "groq_llm_node5.outputs.output.word_count",
                        "min_words": 500,
                    },
                },
                "config": {},
                "outputs": {},
            },
            # ── Step 5a (True branch): Classify publishing channel ────────────────
            {
                "key": "llm.groq",
                "name": "channel_classifier",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Read the article below and respond with exactly one word "
                        "indicating the best publishing channel: "
                        "'blog', 'newsletter', or 'social'.\n\nArticle: {article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
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
            # ── Step 5b (False branch): Rewrite the article ───────────────────────
            {
                "key": "llm.groq",
                "name": "rewrite_node",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "The following article is too short. "
                        "Expand it to at least 500 words while preserving its meaning.\n\n"
                        "Article: {article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
                },
                "config": {
                    "response_model": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "object",
                                "properties": {"final_article": {"type": "string"}},
                                "required": ["final_article"],
                            },
                            "continue_loop": {"type": "boolean"},
                        },
                        "required": ["output", "continue_loop"],
                    }
                },
                "outputs": {},
            },
            # ── Step 6: Route to publishing channel ───────────────────────────────
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
            # ── Step 7: Publishers ────────────────────────────────────────────────
            {
                "key": "llm.groq",
                "name": "blog_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Format the following article for a blog post "
                        "with proper headings and an SEO meta description:\n\n{article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
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
                "key": "llm.groq",
                "name": "newsletter_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Format the following article as an email newsletter "
                        "with a subject line and preview text:\n\n{article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
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
                "key": "llm.groq",
                "name": "social_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Summarise the following article into 3 punchy social media "
                        "posts (Twitter/LinkedIn):\n\n{article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
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
            # ── Entry ──────────────────────────────────────────────────────────────
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            # ── Parallel fan-out ───────────────────────────────────────────────────
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
            # ── Fan-in (wait for all three sections) ──────────────────────────────
            {"source": "groq_llm_node2", "target": "groq_llm_node5", "type": "merge"},
            {"source": "groq_llm_node3", "target": "groq_llm_node5", "type": "merge"},
            {"source": "groq_llm_node4", "target": "groq_llm_node5", "type": "merge"},
            # ── Quality gate ───────────────────────────────────────────────────────
            {"source": "groq_llm_node5", "target": "quality_gate", "type": "linear"},
            # ── If branches ────────────────────────────────────────────────────────
            {
                "source": "quality_gate",
                "target": "channel_classifier",
                "type": "if",
                "decision": True,
            },
            {
                "source": "quality_gate",
                "target": "rewrite_node",
                "type": "if",
                "decision": False,
            },
            # ── Alternate routing after rewrite ─────────────────────────────────────
            {
                "source": "rewrite_node",
                "target": "channel_classifier",
                "type": "linear",
            },
            # ── Channel routing ────────────────────────────────────────────────────
            {
                "source": "channel_classifier",
                "target": "channel_router",
                "type": "linear",
            },
            # ── Switch cases ───────────────────────────────────────────────────────
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
            # ── Terminal edges ─────────────────────────────────────────────────────
            {"source": "blog_publisher", "target": "end", "type": "linear"},
            {"source": "newsletter_publisher", "target": "end", "type": "linear"},
            {"source": "social_publisher", "target": "end", "type": "linear"},
            {"source": "rewrite_node", "target": "end", "type": "linear"},
        ],
    }
    asyncio.run(main(workflow_str=json.dumps(drive_upload_pipeline)))
