# Building a frontend for an AI Workflow Automation Tool (wFlow)

I am building an ai workflow automation tool where users are able to connect various nodes and able to run complex workflows. The prototype for the backend is ready. Now, you have to study the backend APIs and design a modular, scalable and production ready frontend using the following stacks. Do not enforce all the stack below. Use when necessary.

### **Frontend Stacks**
- React 19
- TypeScript
- Vite
- React Flow
- Zustand
- TanStack Query
- TanStack Router
- React Hook Form
- Zod
- Tailwind
- shadcn/ui
- Sentry

# Design System Considerations

- **Modular Components**: Create a component library with reusable UI components that can be used across the application.
- **Type Safety**: Ensure type safety throughout the application using TypeScript.
- **Performance**: Optimize the application for performance.
- **Security**: Implement security measures to protect user data.


### Core Desgin Complexity
The frontend should be simple where users will be able to drag and drop the nodes, connect them with the edges, save and run the pipeline. The UI should be responsive accross the possible devices and should look smooth. It should have light/dark/system toggle.

The main logic is, we have to track the json of the workflow. We have to build that JSON according to how the user interact with the nodes and how they will connect them. 

Here is the example of the json to build:

```json
{
        "nodes": [
            {
                "key": "llm.groq",
                "name": "groq_llm_node1",
                "type": "LLM",
                "inputs": {"prompt": "Generate me 9 outlines for an essay on Nepal."},
                "config": {"response_model": {"output": {"outlines": "list.str"}}},
                "outputs": {},
            },
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
                "config": {"response_model": {"output": {"article": "str"}}},
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
                "config": {"response_model": {"output": {"article": "str"}}},
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
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
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
                        "output": {"final_article": "str", "word_count": "int"}
                    }
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
                        "word_count": "groq_llm_node5.outputs.output.word_count",
                        "min_words": 500,
                    },
                },
                "config": {},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "channel_classifier",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "Read the article below and respond with exactly one word "
                        "indicating the best publishing channel: 'blog', 'newsletter', or 'social'.\n\n"
                        "Article: {article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
                },
                "config": {"response_model": {"output": {"channel": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "rewrite_node",
                "type": "LLM",
                "inputs": {
                    "prompt": (
                        "The following article is too short. "
                        "Expand it to at least 500 words while preserving the original meaning.\n\n"
                        "Article: {article}"
                    ),
                    "article": "groq_llm_node5.outputs.output.final_article",
                },
                "config": {"response_model": {"output": {"final_article": "str"}}},
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
                "key": "llm.groq",
                "name": "blog_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": "Format the following article for a blog post with proper headings and SEO meta description:\n\n{article}",
                    "article": "groq_llm_node5.outputs.output.final_article",
                },
                "config": {"response_model": {"output": {"published_content": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "newsletter_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": "Format the following article as an email newsletter with a subject line and preview text:\n\n{article}",
                    "article": "groq_llm_node5.outputs.output.final_article",
                },
                "config": {"response_model": {"output": {"published_content": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "social_publisher",
                "type": "LLM",
                "inputs": {
                    "prompt": "Summarise the following article into 3 punchy social media posts (Twitter/LinkedIn):\n\n{article}",
                    "article": "groq_llm_node5.outputs.output.final_article",
                },
                "config": {"response_model": {"output": {"published_content": "str"}}},
                "outputs": {},
            },
        ],
        "edges": [
            # Linear start
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            # Parallel article generation
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
            # Merge into final article
            {"source": "groq_llm_node2", "target": "groq_llm_node5", "type": "merge"},
            {"source": "groq_llm_node3", "target": "groq_llm_node5", "type": "merge"},
            {"source": "groq_llm_node4", "target": "groq_llm_node5", "type": "merge"},
            # Quality gate (if)
            {"source": "groq_llm_node5", "target": "quality_gate", "type": "linear"},
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
            # rewrite_node routes onward to the classifier
            {"source": "rewrite_node", "target": "channel_classifier", "type": "linear"},
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
``` 

The necessary infomation is in the backend folders for the workflow. 
Workflow/Nodes/Edges : backend/workflows
APIs: backend/routes

**Currently focus on the tracking, UI smoothness and all the above criterias. I want this platform to be very smooth, user-friendly and interactive.**

The API for running the workflow is not ready yet. Only integrate the Ready APIs properly. Don't use or touch any new API for now. Focus on the requirements above. Focus on building **only the frontend.**