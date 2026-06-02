from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Type


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
    # reasoning_effort: Literal["low", "medium", "high", "none", "default"] = "default"
    system_prompt: str = "Your are a helpful AI Assistant."


class GroqCallParams(BaseModel):
    prompt: str
    config: GroqModelConfig

    model_config = ConfigDict(extra="allow")


class GoogleModelEnum(str, Enum):
    """Supported Gemini models via the google-genai SDK."""

    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"


class GoogleConfig(BaseModel):
    """Configuration options for a Google LLM call."""

    model: GoogleModelEnum = Field(
        default=GoogleModelEnum.GEMINI_2_5_FLASH,
        description="The Gemini model identifier to execute the request against.",
    )
    system_prompt: str = Field(
        default="You are a helpful AI assistant.",
        description="System instructions to guide the model's behavior and persona.",
    )
    response_model: dict = Field(
        default=None,
    )
    temperature: float | None = Field(
        default=None,
        description="Controls randomness in generation. Lower values are more deterministic.",
    )
    max_output_tokens: int | None = Field(
        default=None,
        description="The maximum number of tokens to generate in the reply.",
    )

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class GoogleCallParams(BaseModel):
    """The unified parameter payload passed directly to the GoogleClient methods."""

    prompt: str = Field(
        ..., description="The user input or prompt string for the model to process."
    )
    config: GoogleConfig = Field(
        default_factory=GoogleConfig,
        description="Execution configurations and parameters for the call.",
    )

class DynamicOutput(BaseModel):
    """A flexible output model that allows dynamic fields from LLM responses."""
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)