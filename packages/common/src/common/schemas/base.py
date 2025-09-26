from pydantic import BaseModel, ConfigDict

class ORMBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,   # <-- key line
    )