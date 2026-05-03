from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Literal, Any

class GroqModelEnum(str, Enum):
    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"
    LLAMA_3_3_70B_VERSATILE = "llama-3.3-70b-versatile"
    KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    QWEN3_32B = "qwen/qwen3-32b"


class GroqModelConfig(BaseModel):
    response_model: dict 
    model: GroqModelEnum = GroqModelEnum.GPT_OSS_120B
    max_tokens: int | None = None
    reasoning_effort: Literal["low", "medium", "high", "none", "default"] = "default"
    system_prompt: str = "Your are a helpful AI Assistant."


class GroqCallParams(BaseModel):
    prompt: str
    config: GroqModelConfig

    model_config = ConfigDict(extra="allow")


class DynamicOutput(BaseModel):
    output: dict[str, Any]
