from groq import AsyncGroq
from enum import Enum
from pydantic import BaseModel
from typing import Literal

from src.config import CONFIG


class GroqModelEnum(str, Enum):
    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"
    LLAMA_3_3_70B_VERSATILE = "llama-3.3-70b-versatile"
    KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    QWEN3_32B = "qwen/qwen3-32b"

class GroqCallParams(BaseModel):
    model: GroqModelEnum
    system_prompt: str
    prompt: str
    max_tokens: int
    reasoning_effort: Literal["low", "medium", "high", "medium", "none"]


class GroqClient:
    def __init__(self, api_key: str | None = None):
        self._client: AsyncGroq = AsyncGroq(
            api_key=api_key if api_key else CONFIG.GROQ_API_KEY,
        )

    async def _non_streaming_llm_call(
        self, params: GroqCallParams
    ):
        response = await self._client.chat.completions.create(
            model=params.model.value,
            messages=[
                {"role": "system", "content": params.system_prompt},
                {"role": "user", "content": params.prompt},
            ],
            reasoning_effort=params.reasoning_effort,
            max_completion_tokens=params.max_tokens,
            stream=False
        )
        return response.choices[0].message
    

    async def _streaming_llm_call(
        self, params: GroqCallParams
    ):
        pass

    async def call_groq(self, params: GroqCallParams, stream: bool = False):
        pass
