from abc import ABC
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    model_validator,
    ValidationError,
    ValidationInfo,
)
from starlette.requests import Request


class ServiceType(str, Enum):
    github = "github"


class ServiceBase(BaseModel, ABC):
    """
    Base: Service
    """

    model_config = ConfigDict(from_attributes=True)
    uuid: str
    name: str
    type: ServiceType
    desc: str
    token: str
    creation_date: datetime


class ServiceExternal(ServiceBase):
    webhook_url: HttpUrl | None = None

    @model_validator(mode="after")
    def build_url(cls, data: "ServiceExternal", info: ValidationInfo):
        if data.webhook_url is None and info.context is None:
            raise ValidationError("The request must be set in the context of model_validate()")
        request: Request = info.context["request"]
        data.webhook_url = HttpUrl(str(request.url_for("create_message", uuid=data.uuid)))
        return data


class ServiceInternal(ServiceBase):
    id: str


class ServiceRequestMain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: ServiceType
    desc: Optional[str]


class ServiceRequest(BaseModel):
    data: ServiceRequestMain


class ServiceUpdateMain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = ""
    type: Optional[str] = ""
    desc: Optional[str] = ""
    username: Optional[str] = ""


class ServiceUpdate(BaseModel):
    data: ServiceUpdateMain


class ServiceResult(BaseModel):
    data: ServiceExternal


class ServiceManyResult(BaseModel):
    data: List[ServiceExternal] = []
