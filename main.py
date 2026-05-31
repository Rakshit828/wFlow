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
            # ── Step 1: Generate 9 outlines ───────────────────────────────────────
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
            # ── Step 2: Write 3 article sections in parallel ──────────────────────
            {
                "key": "llm.google",
                "name": "google_llm_node2",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed article section on these topics: {topics}",
                    "topics": (
                        "google_llm_node1.outputs.output.outlines[0] "
                        "google_llm_node1.outputs.output.outlines[1] "
                        "google_llm_node1.outputs.output.outlines[2]"
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
                "key": "llm.google",
                "name": "google_llm_node3",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed article section on these topics: {topics}",
                    "topics": (
                        "google_llm_node1.outputs.output.outlines[3] "
                        "google_llm_node1.outputs.output.outlines[4] "
                        "google_llm_node1.outputs.output.outlines[5]"
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
                "key": "llm.google",
                "name": "google_llm_node4",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a detailed article section on these topics: {topics}",
                    "topics": (
                        "google_llm_node1.outputs.output.outlines[6] "
                        "google_llm_node1.outputs.output.outlines[7] "
                        "google_llm_node1.outputs.output.outlines[8]"
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
                "key": "llm.google",
                "name": "google_llm_node5",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Merge these article sections into one cohesive final article: {articles}"
                    ),
                    "articles": (
                        "google_llm_node2.outputs.output.article "
                        "google_llm_node3.outputs.output.article "
                        "google_llm_node4.outputs.output.article"
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
                        "word_count": "google_llm_node5.outputs.output.word_count",
                        "min_words": 500,
                    },
                },
                "config": {},
                "outputs": {},
            },
            # ── Step 5a (True branch): Classify publishing channel ────────────────
            {
                "key": "llm.google",
                "name": "channel_classifier",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Read the article below and respond with exactly one word "
                        "indicating the best publishing channel: "
                        "'blog', 'newsletter', or 'social'.\n\nArticle: {article}"
                    ),
                    "article": "google_llm_node5.outputs.output.final_article",
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
                "key": "llm.google",
                "name": "rewrite_node",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "The following article is too short. "
                        "Expand it to at least 500 words while preserving its meaning.\n\n"
                        "Article: {article}"
                    ),
                    "article": "google_llm_node5.outputs.output.final_article",
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
                "key": "llm.google",
                "name": "blog_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Format the following article for a blog post "
                        "with proper headings and an SEO meta description:\n\n{article}"
                    ),
                    "article": "google_llm_node5.outputs.output.final_article",
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
                    "prompt": (
                        "Format the following article as an email newsletter "
                        "with a subject line and preview text:\n\n{article}"
                    ),
                    "article": "google_llm_node5.outputs.output.final_article",
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
                    "prompt": (
                        "Summarise the following article into 3 punchy social media "
                        "posts (Twitter/LinkedIn):\n\n{article}"
                    ),
                    "article": "google_llm_node5.outputs.output.final_article",
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
            {"source": "start", "target": "google_llm_node1", "type": "linear"},
            # ── Parallel fan-out ───────────────────────────────────────────────────
            {
                "source": "google_llm_node1",
                "target": "google_llm_node2",
                "type": "parallel",
            },
            {
                "source": "google_llm_node1",
                "target": "google_llm_node3",
                "type": "parallel",
            },
            {
                "source": "google_llm_node1",
                "target": "google_llm_node4",
                "type": "parallel",
            },
            # ── Fan-in (wait for all three sections) ──────────────────────────────
            {"source": "google_llm_node2", "target": "google_llm_node5", "type": "merge"},
            {"source": "google_llm_node3", "target": "google_llm_node5", "type": "merge"},
            {"source": "google_llm_node4", "target": "google_llm_node5", "type": "merge"},
            # ── Quality gate ───────────────────────────────────────────────────────
            {"source": "google_llm_node5", "target": "quality_gate", "type": "linear"},
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
    asyncio.run(main(pipeline_str=json.dumps(pipeline_with_control_flow)))
