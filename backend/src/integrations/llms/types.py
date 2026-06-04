from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class GroqModelEnum(str, Enum):
    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"
    LLAMA_3_3_70B_VERSATILE = "llama-3.3-70b-versatile"
    KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    QWEN3_32B = "qwen/qwen3-32b"


class GroqModelConfig(BaseModel):
    response_model: dict
    model: GroqModelEnum = GroqModelEnum.GPT_OSS_120B
    max_tokens: int = Field(default=None, json_schema_extra={"x-technical": True})
    # reasoning_effort: Literal["low", "medium", "high", "none", "default"] = "default"
    system_prompt: str = Field(
        default="You are a helpful AI Assistant.",
        json_schema_extra={"x-technical": True},
    )


class GroqCallParams(BaseModel):
    prompt: str
    config: GroqModelConfig

    model_config = ConfigDict(extra="allow")


class GoogleModelEnum(str, Enum):
    """Supported Gemini models."""

    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"


class GoogleConfig(BaseModel):
    """Configuration options for a Google LLM call."""

    response_model: dict
    model: GoogleModelEnum = Field(
        default=GoogleModelEnum.GEMINI_2_5_FLASH,
    )

    system_prompt: str = Field(
        default="You are a helpful AI assistant.",
        json_schema_extra={"x-technical": True},
    )
    temperature: float | None = Field(
        default=None, json_schema_extra={"x-technical": True}
    )
    max_output_tokens: int | None = Field(
        default=None, json_schema_extra={"x-technical": True}
    )

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class GoogleCallParams(BaseModel):
    """The unified parameter payload passed directly to the GoogleClient methods."""

    prompt: str
    config: GoogleConfig = Field(
        default_factory=GoogleConfig,
    )


class DynamicOutput(BaseModel):
    """A flexible output model that allows dynamic fields from LLM responses."""

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
