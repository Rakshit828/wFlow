import asyncio as aio
from typing import Any, AsyncGenerator
import google.genai as genai
from google.genai import types
from google.genai.errors import APIError
from loguru import logger

from src.config import CONFIG
from src.integrations.llms.base import LLMClient
from src.integrations.llms.types import GoogleCallParams, GoogleModelEnum


class GoogleClient(LLMClient):
    def __init__(self, api_key: str | None = None):
        # 1. Initialize the regular client
        self._client = genai.Client(
            api_key=api_key if api_key else CONFIG.GEMINI_API_KEY
        )

    async def inference(
        self,
        params: GoogleCallParams | dict[str, Any],
    ) -> str | None:
        if not isinstance(params, GoogleCallParams):
            params = GoogleCallParams(**params)

        logger.info(f"Using model {params.config.model.value} for inference.")
        logger.info(f"\n\nThe prompt is {params.prompt}\n\n")

        config_args = {
            "system_instruction": params.config.system_prompt,
        }
        if params.config.response_model:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = params.config.response_model

        config = types.GenerateContentConfig(**config_args)

        try:
            # 2. Access the async framework using `self._client.aio`
            response = await self._client.aio.models.generate_content(
                model=params.config.model.value,
                contents=params.prompt,
                config=config,
            )
            logger.info(f"The response is {response}")

            # 3. Cleanly pull text using the built-in .text property
            return response.text

        except APIError as err:
            logger.error(f"Google API Error: {err}")
            raise err

    async def stream(
        self,
        params: GoogleCallParams | dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        if not isinstance(params, GoogleCallParams):
            params = GoogleCallParams(**params)

        config = types.GenerateContentConfig(
            system_instruction=params.config.system_prompt,
        )

        try:
            # 4. Use `self._client.aio` here as well
            response_stream = await self._client.aio.models.generate_content_stream(
                model=params.config.model.value,
                contents=params.prompt,
                config=config,
            )

            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except APIError as err:
            logger.error(f"Google API Streaming Error: {err}")
            raise err


async def main():
    google_client = GoogleClient()

    payload = {
        "config": {
            "model": GoogleModelEnum.GEMINI_2_5_FLASH,
            "system_prompt": "You are a helpful AI assistant",
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
        "prompt": "What is life?",
    }

    # 5. Await the response smoothly
    async_response = await google_client.inference(GoogleCallParams(**payload))
    print(async_response)


if __name__ == "__main__":
    aio.run(main())
