import uuid

from pydantic import BaseModel, ConfigDict


class TagResponse(BaseModel):
    id: uuid.UUID
    label: str

    model_config = ConfigDict(from_attributes=True)
