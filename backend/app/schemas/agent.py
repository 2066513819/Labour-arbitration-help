from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class AgentAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    laborer_type: Optional[str] = Field(default=None, description="劳动者类型")
    is_first: bool = Field(default=False, description="是否为首次提问")
    history: Optional[List[Message]] = Field(default=None, description="对话历史")


class AgentStructuredReply(BaseModel):
    restate: str
    law_refs: List[str]
    interpretation: str
    suggested_actions: List[str]
    linked_scenario_ids: List[str] = Field(default_factory=list)


class AgentAskResponse(BaseModel):
    message_id: int
    reply: AgentStructuredReply
    ui_meta: Optional[Dict[str, object]] = None
    latency_ms: int
