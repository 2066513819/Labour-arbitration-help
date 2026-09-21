from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.case_record import CaseRecord, EvidenceFile
from app.models.user import User

router = APIRouter(prefix="/cases", tags=["案件管理"])


class CreateCaseRequest(BaseModel):
    title: Optional[str] = None
    scenario_id: str
    dispute_summary: Optional[str] = None
    case_notes: Optional[str] = None
    entry_date: Optional[str] = None
    quit_date: Optional[str] = None
    average_salary: Optional[str] = None
    bonus_info: Optional[str] = None


class UpdateCaseRequest(BaseModel):
    title: Optional[str] = None
    case_notes: Optional[str] = None
    case_status: Optional[str] = None
    entry_date: Optional[str] = None
    quit_date: Optional[str] = None
    average_salary: Optional[str] = None
    bonus_info: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    progress_stage: str


class UpdateDocumentRequest(BaseModel):
    document_draft: str


@router.get("")
def list_cases(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取用户的所有案件列表"""
    rows = (
        db.query(CaseRecord)
        .filter(CaseRecord.user_id == user.id)
        .order_by(CaseRecord.updated_at.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "scenario_id": r.scenario_id,
                "title": r.title,
                "case_notes": r.case_notes,
                "case_status": r.case_status,
                "progress_stage": r.progress_stage,
                "entry_date": r.entry_date,
                "quit_date": r.quit_date,
                "average_salary": r.average_salary,
                "bonus_info": r.bonus_info,
                "evidence_count": len(r.evidences) if r.evidences else 0,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.post("")
def create_case(
    body: CreateCaseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建新案件"""
    title = body.title or f"案件-{body.scenario_id}"
    rec = CaseRecord(
        user_id=user.id,
        scenario_id=body.scenario_id,
        title=title,
        case_notes=body.case_notes,
        case_status="进行中",
        dispute_summary=body.dispute_summary,
        progress_stage="evidence",
        entry_date=body.entry_date,
        quit_date=body.quit_date,
        average_salary=body.average_salary,
        bonus_info=body.bonus_info,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"id": rec.id, "title": rec.title, "ui_meta": {"goto": "evidence"}}


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取案件详情"""
    rec = db.get(CaseRecord, case_id)
    if not rec or rec.user_id != user.id:
        raise HTTPException(404, "案件不存在")

    # 获取证据统计
    evidence_count = len(rec.evidences) if rec.evidences else 0
    evidence_stats = {
        "total": evidence_count,
        "image_count": sum(1 for e in rec.evidences if e.evidence_type == "image"),
        "doc_count": sum(1 for e in rec.evidences if e.evidence_type == "doc"),
        "audio_count": sum(1 for e in rec.evidences if e.evidence_type == "audio"),
        "video_count": sum(1 for e in rec.evidences if e.evidence_type == "video"),
    }

    return {
        "id": rec.id,
        "scenario_id": rec.scenario_id,
        "title": rec.title,
        "case_notes": rec.case_notes,
        "case_status": rec.case_status,
        "dispute_summary": rec.dispute_summary,
        "document_draft": rec.document_draft,
        "progress_stage": rec.progress_stage,
        "entry_date": rec.entry_date,
        "quit_date": rec.quit_date,
        "average_salary": rec.average_salary,
        "bonus_info": rec.bonus_info,
        "evidence_stats": evidence_stats,
        "extra_meta": rec.extra_meta,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
    }


@router.patch("/{case_id}")
def update_case(
    case_id: int,
    body: UpdateCaseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新案件信息（标题、备注、状态）"""
    rec = db.get(CaseRecord, case_id)
    if not rec or rec.user_id != user.id:
        raise HTTPException(404, "案件不存在")

    if body.title is not None:
        rec.title = body.title
    if body.case_notes is not None:
        rec.case_notes = body.case_notes
    if body.case_status is not None:
        rec.case_status = body.case_status
    if body.entry_date is not None:
        rec.entry_date = body.entry_date
    if body.quit_date is not None:
        rec.quit_date = body.quit_date
    if body.average_salary is not None:
        rec.average_salary = body.average_salary
    if body.bonus_info is not None:
        rec.bonus_info = body.bonus_info

    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "success": True,
        "data": {
            "id": rec.id,
            "title": rec.title,
            "case_notes": rec.case_notes,
            "case_status": rec.case_status,
            "entry_date": rec.entry_date,
            "quit_date": rec.quit_date,
            "average_salary": rec.average_salary,
            "bonus_info": rec.bonus_info,
        },
    }


@router.patch("/{case_id}/document")
def patch_document(
    case_id: int,
    body: UpdateDocumentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新案件文书草稿"""
    rec = db.get(CaseRecord, case_id)
    if not rec or rec.user_id != user.id:
        raise HTTPException(404, "案件不存在")
    rec.document_draft = body.document_draft
    db.add(rec)
    db.commit()
    return {"ok": True}


@router.patch("/{case_id}/progress")
def patch_progress(
    case_id: int,
    body: ProgressUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新案件进度"""
    rec = db.get(CaseRecord, case_id)
    if not rec or rec.user_id != user.id:
        raise HTTPException(404, "案件不存在")
    rec.progress_stage = body.progress_stage
    db.add(rec)
    db.commit()
    return {"ok": True, "progress_stage": rec.progress_stage}


@router.delete("/{case_id}")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除案件"""
    rec = db.get(CaseRecord, case_id)
    if not rec or rec.user_id != user.id:
        raise HTTPException(404, "案件不存在")

    db.delete(rec)
    db.commit()
    return {"success": True, "message": "案件已删除"}
