from typing import Optional

from pydantic import BaseModel


class CreateCaseRequest(BaseModel):
    scenario_id: str
    title: Optional[str] = None
    dispute_summary: Optional[str] = None


class UpdateDocumentRequest(BaseModel):
    document_draft: str


class ProgressUpdateRequest(BaseModel):
    progress_stage: str


class EvidenceUploadMeta(BaseModel):
    case_id: Optional[int] = None
