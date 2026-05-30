from src.workflows.types import ApplicationNode, NodesTypeEnum
from src.integrations.llms.groq_client import GroqClient, GroqCallParams
from src.integrations.llms.types import DynamicOutput
from temporalio import activity
import json

@activity.defn
async def groq_llm_call(params: GroqCallParams) -> dict:
    client = GroqClient()
    result: str = await client.inference(params)
    print(f"\nThe result is {result}\n")
    return json.loads(result)


GROQ_LLM_NODE = ApplicationNode(
    name="groq_llm_node",
    description="This uses groq provider to use llm models",
    fn=groq_llm_call,
    key="llm.groq",
    service="groq",
    valid_permissions=None,
    type=NodesTypeEnum.LLM,
    node_input_model=GroqCallParams,
    node_output_model=DynamicOutput,
)
