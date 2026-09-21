from typing import Optional, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import base64

from app.database import get_db
from app.deps import get_current_user
from app.models.case_record import CaseRecord, EvidenceFile
from app.models.user import User
from app.data.scenario_catalog import get_scenarios
from app.services.deli_service import generate_arbitration_document
from app.services.image_agent_service import call_document_agent, call_chat_agent
from app.services.document_workflow_service import (
    call_workflow_with_image,
    call_workflow_with_document,
    call_workflow_chat,
)

router = APIRouter(prefix="/document", tags=["document"])


class DocumentGenerateRequest(BaseModel):
    extra_facts: Optional[str] = Field(default=None, max_length=4000)


@router.post("/generate/{case_id}")
async def generate(
    case_id: int,
    body: DocumentGenerateRequest = DocumentGenerateRequest(),
    laborer_type: str = Query(...),
    scenario_id: str = Query(...),
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    case = db.get(CaseRecord, case_id)
    if not case or case.user_id != user.id:
        raise HTTPException(404, "案件不存在")
    scenario = next((s for s in get_scenarios(laborer_type) if s["id"] == scenario_id), None)
    if not scenario:
        raise HTTPException(400, "场景不存在")
    evs = db.query(EvidenceFile).filter(EvidenceFile.case_id == case_id).all()
    ocr_snippets = [e.ocr_result or {} for e in evs]
    facts = (case.dispute_summary or "").strip()
    extra = (body.extra_facts or "").strip()
    if extra:
        facts = (facts + "\n\n补充说明：\n" + extra).strip()
    text = await generate_arbitration_document(
        laborer_type=laborer_type,
        scenario_id=scenario_id,
        scenario_title=scenario["title"],
        law_refs=scenario.get("law_refs", []),
        user_phone=user.phone,
        facts=facts or None,
        ocr_snippets=ocr_snippets,
    )
    case.document_draft = text
    case.progress_stage = "document"
    db.add(case)
    db.commit()
    return {
        "document": text,
        "ui_meta": {"loading_style": "skeleton", "toast": "文书已生成", "duration_ms": 260},
    }


class ImageUploadRequest(BaseModel):
    """图片上传请求"""
    image_base64: str = Field(..., description="图片的base64编码（不包含data URI前缀）")
    context: Optional[str] = Field(default=None, description="额外的上下文信息")


class ImageUrlRequest(BaseModel):
    """通过URL获取图片并分析"""
    image_url: str = Field(..., description="图片URL地址")
    context: Optional[str] = Field(default=None, description="额外的上下文信息")


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    context: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
):
    """
    上传图片到智能体进行分析/文书起草
    支持格式: jpeg, png, jpg
    """
    # 读取文件内容
    contents = await file.read()
    
    # 检查文件大小（限制 10MB）
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "图片大小不能超过 10MB")
    
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"不支持的图片格式，仅支持: {', '.join(allowed_types)}")
    
    # 转换为 base64
    image_base64 = base64.b64encode(contents).decode("utf-8")
    
    print(f"[文书起草] 收到图片上传，大小: {len(contents)} bytes")
    
    # 调用工作流
    try:
        result = await call_workflow_with_image(
            image_data=image_base64,
            user_message=context or "请分析这张图片内容，帮助我生成劳动仲裁申请书",
            user_id=str(user.id),
        )
        return {
            "result": result,
            "file_name": file.filename,
            "file_size": len(contents),
        }
    except Exception as e:
        print(f"[文书起草] 工作流调用失败: {str(e)}")
        raise HTTPException(500, f"工作流调用失败: {str(e)}")


@router.post("/analyze-image")
async def analyze_image(
    body: ImageUploadRequest,
    user: User = Depends(get_current_user),
):
    """
    使用 base64 编码的图片进行分析
    """
    print(f"[图片分析] 收到图片，大小: {len(body.image_base64)} bytes")
    
    # 调用工作流
    try:
        result = await call_workflow_with_image(
            image_data=body.image_base64,
            user_message=body.context or "请分析这张图片内容，帮助我生成劳动仲裁申请书",
            user_id=str(user.id),
        )
        return {
            "result": result,
        }
    except Exception as e:
        print(f"[图片分析] 工作流调用失败: {str(e)}")
        raise HTTPException(500, f"工作流调用失败: {str(e)}")


@router.post("/analyze-image-url")
async def analyze_image_url(
    body: ImageUrlRequest,
    user: User = Depends(get_current_user),
):
    """
    通过URL下载图片并进行分析（用于证据管理跳转）
    """
    import httpx
    print(f"[图片URL分析] 收到URL: {body.image_url[:100]}...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(body.image_url)
            response.raise_for_status()
            image_data = base64.b64encode(response.content).decode("utf-8")
            print(f"[图片URL分析] 下载成功，大小: {len(response.content)} bytes")
        
        result = await call_workflow_with_image(
            image_data=image_data,
            user_message=body.context or "请分析这张图片内容，帮助我生成劳动仲裁申请书",
            user_id=str(user.id),
        )
        return {
            "result": result,
        }
    except httpx.HTTPError as e:
        print(f"[图片URL分析] 下载失败: {str(e)}")
        raise HTTPException(500, f"图片下载失败: {str(e)}")
    except Exception as e:
        print(f"[图片URL分析] 工作流调用失败: {str(e)}")
        raise HTTPException(500, f"工作流调用失败: {str(e)}")


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    context: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
):
    """
    上传文档到工作流进行分析/文书起草
    支持格式: pdf, doc, docx, txt 等
    """
    # 读取文件内容
    contents = await file.read()
    
    # 检查文件大小（限制 20MB）
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(400, "文档大小不能超过 20MB")
    
    filename = file.filename or "document"
    
    print(f"[文档上传] 收到文档: {filename}, 大小: {len(contents)} bytes")
    
    # 调用工作流
    try:
        result = await call_workflow_with_document(
            file_content=contents,
            filename=filename,
            user_message=context or "请分析这份文档内容，帮助我生成劳动仲裁申请书",
            user_id=str(user.id),
        )
        return {
            "result": result,
            "file_name": filename,
            "file_size": len(contents),
        }
    except Exception as e:
        print(f"[文档上传] 工作流调用失败: {str(e)}")
        raise HTTPException(500, f"工作流调用失败: {str(e)}")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    history: Optional[List[dict]] = Field(default=None, description="对话历史")
    file_type: Optional[str] = Field(default="image", description="附件类型: image 或 doc")
    file_content: Optional[str] = Field(default=None, description="附件内容: base64 或 bytes")
    file_name: Optional[str] = Field(default=None, description="文件名")


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
):
    """
    与智能体进行文字对话
    """
    print(f"[文书聊天] 收到消息: {body.message}")
    print(f"[文书聊天] 历史消息数: {len(body.history) if body.history else 0}")
    print(f"[文书聊天] 附件类型: {body.file_type}")
    
    try:
        result = await call_workflow_chat(
            message=body.message,
            file_type=body.file_type,
            file_content=body.file_content,
            filename=body.file_name,
            history=body.history,
            user_id=str(user.id),
        )
        return {
            "result": result,
        }
    except Exception as e:
        print(f"[文书聊天] 工作流调用失败: {str(e)}")
        raise HTTPException(500, f"工作流调用失败: {str(e)}")


class GenerateFromChatRequest(BaseModel):
    """从对话历史生成文书"""
    history: List[dict] = Field(..., description="对话历史")


@router.post("/generate-from-chat")
async def generate_from_chat(
    body: GenerateFromChatRequest,
    user: User = Depends(get_current_user),
):
    """
    根据对话历史生成完整的仲裁申请书
    """
    print(f"[生成文书] 对话历史消息数: {len(body.history)}")
    
    try:
        result = await call_chat_agent(
            message="请根据以上对话内容，生成一份完整的劳动仲裁申请书。",
            history=body.history,
            system_prompt="你是一个专业的劳动法律文书助手。用户会提供对话内容，请根据对话中提到的信息生成规范的劳动仲裁申请书，包括：申请人信息、被申请人信息、仲裁请求、事实与理由等部分。",
        )
        return {
            "document": result,
        }
    except Exception as e:
        print(f"[生成文书] 智能体调用失败: {str(e)}")
        raise HTTPException(500, f"智能体调用失败: {str(e)}")
