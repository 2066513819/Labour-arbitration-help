"""
证据文件 API 接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.evidence_service import evidence_service

router = APIRouter(prefix="/evidence", tags=["证据管理"])


@router.post("/upload")
async def upload_evidence(
    case_id: int = Form(..., description="案件ID"),
    file: UploadFile = File(..., description="证据文件"),
    evidence_name: Optional[str] = Form(None, description="证据名称"),
    description: Optional[str] = Form(None, description="证据描述"),
    db: Session = Depends(get_db),
):
    """
    上传证据文件（支持图片、文档、录音、视频）

    支持的文件类型:
    - 图片: jpeg, png, gif, webp
    - 文档: pdf, doc, docx, txt
    - 录音: mp3, wav, ogg, m4a
    - 视频: mp4, webm, ogg
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 获取文件类型
        content_type = file.content_type or "application/octet-stream"

        evidence = evidence_service.upload_evidence(
            db=db,
            case_id=case_id,
            file_content=content,
            filename=file.filename or "unknown",
            content_type=content_type,
            evidence_name=evidence_name,
            description=description,
        )

        return {
            "success": True,
            "data": evidence_service._format_evidence(evidence),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[证据上传失败] {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/base64")
async def upload_evidence_base64(
    case_id: int,
    base64_content: str,
    filename: str,
    content_type: str,
    evidence_name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """从base64内容上传证据文件"""
    try:
        evidence = evidence_service.upload_from_base64(
            db=db,
            case_id=case_id,
            base64_content=base64_content,
            filename=filename,
            content_type=content_type,
            evidence_name=evidence_name,
            description=description,
        )

        return {
            "success": True,
            "data": evidence_service._format_evidence(evidence),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[证据上传失败] {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/list/{case_id}")
def get_evidences(case_id: int, db: Session = Depends(get_db)):
    """获取案件的所有证据"""
    summary = evidence_service.get_evidence_summary(case_id, db)
    return {"success": True, "data": summary}


@router.get("/{evidence_id}")
def get_evidence(evidence_id: int, db: Session = Depends(get_db)):
    """获取单个证据详情"""
    evidence = evidence_service.get_evidence(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    return {
        "success": True,
        "data": evidence_service._format_evidence(evidence),
    }


@router.patch("/{evidence_id}")
def update_evidence(
    evidence_id: int,
    evidence_name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """更新证据信息"""
    evidence = evidence_service.update_evidence(
        db, evidence_id, evidence_name=evidence_name, description=description
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    return {"success": True, "data": evidence_service._format_evidence(evidence)}


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)):
    """删除证据"""
    success = evidence_service.delete_evidence(db, evidence_id)
    if not success:
        raise HTTPException(status_code=404, detail="证据不存在")

    return {"success": True, "message": "删除成功"}
