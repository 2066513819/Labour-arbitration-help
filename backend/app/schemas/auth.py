from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.labor import LaborerType


class SendCodeRequest(BaseModel):
    phone: str = Field(default="", min_length=0, max_length=11, pattern=r"^(1\d{10})?$")


class SendEmailCodeRequest(BaseModel):
    email: str = Field(..., max_length=120)


class LoginRequest(BaseModel):
    phone: str = Field(default="", min_length=0, max_length=11, pattern=r"^(1\d{10})?$")
    code: str = Field(..., min_length=4, max_length=8)


class EmailLoginRequest(BaseModel):
    email: str = Field(..., max_length=120)
    code: str = Field(..., min_length=4, max_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    ui_meta: Optional[Dict[str, object]] = Field(default=None, description="前端过渡/骨架屏等协同字段")


class SetLaborerTypeRequest(BaseModel):
    laborer_type: LaborerType
    inferred_from_flow: bool = False
