from groq import AsyncGroq
from typing import Any, AsyncGenerator
import asyncio as aio
import groq
from loguru import logger

from src.integrations.llms.base import LLMClient
from src.config import CONFIG
from src.integrations.llms.types import GroqCallParams, GroqModelEnum


class GroqClient(LLMClient):
    def __init__(self, api_key: str | None = None):
        self._client: AsyncGroq = AsyncGroq(
            api_key=api_key if api_key else CONFIG.GROQ_API_KEY,
        )

    async def inference(
        self,
        params: GroqCallParams | dict[str, Any],
    ):
        if not isinstance(params, GroqCallParams):
            params = GroqCallParams(**params)

        logger.info(f"Using model {params.config.model.value} for inference.")
        logger.info(f"\n\nThe prompt is {params.prompt}\n\n")
        try:
            response = await self._client.chat.completions.create(
                model=params.config.model.value,
                messages=[
                    {"role": "system", "content": params.config.system_prompt},
                    {"role": "user", "content": params.prompt},
                ],
                response_format={
                    "json_schema": {
                        "name": "output_schema",
                        "schema": params.config.response_model,
                    },
                    "type": "json_schema",
                },
                stream=False,
            )
            return response.choices[0].message.content
        except groq.BadRequestError as err:
            raise err

    async def stream(
        self,
        params: GroqCallParams | dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        if not isinstance(params, GroqCallParams):
            params = GroqCallParams(**params)

        stream = await self._client.chat.completions.create(
            messages=[
                {"role": "system", "content": params.system_prompt},
                {"role": "user", "content": params.prompt},
            ],
            model=params.model.value,
            stream=True,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


async def main():
    groq = GroqClient()
    async for chunk in groq.stream(
        {
            "model": GroqModelEnum.GPT_OSS_120B,
            "max_tokens": 1000,
            "system_prompt": "You are helpful AI assistant",
            "prompt": "What is life.",
        }
    ):
        print(chunk, end=" ", flush=True)


if __name__ == "__main__":
    aio.run(main())
