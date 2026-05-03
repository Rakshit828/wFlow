from src.workflows.types import ApplicationNode, NodesTypeEnum
from src.integrations.llms.groq_client import GroqClient, GroqCallParams
from src.integrations.llms.types import DynamicOutput

GROQ_LLM_NODE = ApplicationNode(
    name="groq_llm_node",
    description="This uses groq provider to use llm models",
    fn=GroqClient.inference,
    key="llm.groq",
    service="groq",
    valid_permissions=None,
    type=NodesTypeEnum.LLM,
    node_input_model=GroqCallParams,
    node_output_model=DynamicOutput,
)
