from pydantic import BaseModel, EmailStr, Field
from typing import Literal, List

class PartnerAccessProperties(BaseModel):
    secLevel: int = Field(ge=1, le=10, description="This is the seclevel of the partner")
    sources: List[str]

class Subject(BaseModel, extra="ignore"):
    id: str
    type: Literal["partner", "project manager"]
    properties:  PartnerAccessProperties

