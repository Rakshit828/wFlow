from src.workflows.types import ApplicationNode, NodesTypeEnum
from src.integrations.llms.groq_client import GroqClient, GroqCallParams
from src.integrations.llms.gemini import GoogleClient, GoogleCallParams
from src.integrations.llms.types import DynamicOutput
from temporalio import activity
import json
from loguru import logger


@activity.defn
async def groq_llm_call(params: GroqCallParams) -> dict:
    client = GroqClient()
    result = await client.inference(params)
    if not isinstance(result, dict):
        result = json.loads(result)
    logger.info(f"The result is {result}, [TYPE]: {type(result)}")
    return result


@activity.defn
async def google_llm_call(params: GoogleCallParams) -> dict:
    client = GoogleClient()
    result = await client.inference(params)
    result = json.loads(result)
    logger.info(f"The result is {result}. Of type: {type(result)}")
    return result


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

GOOGLE_LLM_NODE = ApplicationNode(
    name="google_llm_node",
    description="This uses google provider to use llm models",
    fn=google_llm_call,
    key="llm.google",
    service="google",
    valid_permissions=None,
    type=NodesTypeEnum.LLM,
    node_input_model=GoogleCallParams,
    node_output_model=DynamicOutput,
)
