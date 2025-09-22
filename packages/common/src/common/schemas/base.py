from pydantic import BaseModel

class ORMBase(BaseModel):
    model_config = {"from_attributes": True}