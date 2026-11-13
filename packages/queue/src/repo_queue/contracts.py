from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EXAMPLE_TASK_NAME = "example.process"


class ExampleJob(BaseModel):
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        if not (value := value.strip()):
            raise ValueError("Message is required.")
        return value


class ExampleJobResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    processed_at: datetime = Field(serialization_alias="processedAt")
