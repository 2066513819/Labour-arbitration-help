"""
证据文件服务 - 处理证据上传到COS并存储到数据库
"""
import base64
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.case_record import EvidenceFile
from app.services.document_workflow_service import _upload_to_cos


class EvidenceService:
    """证据文件服务"""

    # 证据类型
    TYPE_IMAGE = "image"
    TYPE_DOC = "doc"
    TYPE_AUDIO = "audio"
    TYPE_VIDEO = "video"

    # 证据类型映射
    TYPE_MAP = {
        "image": {"label": "图片", "icon": "📷", "color": "#67C23A"},
        "doc": {"label": "文档", "icon": "📄", "color": "#409EFF"},
        "audio": {"label": "录音", "icon": "🎵", "color": "#E6A23C"},
        "video": {"label": "视频", "icon": "🎬", "color": "#F56C6C"},
    }

    # 允许的文件类型
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/jpg"}
    ALLOWED_DOC_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }
    ALLOWED_AUDIO_TYPES = {
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/mp3",
        "audio/x-m4a",
        "audio/webm",
    }
    ALLOWED_VIDEO_TYPES = {
        "video/mp4",
        "video/webm",
        "video/ogg",
    }
    ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES | ALLOWED_AUDIO_TYPES | ALLOWED_VIDEO_TYPES

    @staticmethod
    def detect_evidence_type(content_type: str) -> str:
        """根据MIME类型检测证据类型"""
        ct = content_type.lower()
        if ct in EvidenceService.ALLOWED_IMAGE_TYPES or ct.startswith("image/"):
            return EvidenceService.TYPE_IMAGE
        if ct in EvidenceService.ALLOWED_AUDIO_TYPES or ct.startswith("audio/"):
            return EvidenceService.TYPE_AUDIO
        if ct in EvidenceService.ALLOWED_VIDEO_TYPES or ct.startswith("video/"):
            return EvidenceService.TYPE_VIDEO
        return EvidenceService.TYPE_DOC

    @staticmethod
    def upload_evidence(
        db: Session,
        case_id: int,
        file_content: bytes,
        filename: str,
        content_type: str,
        evidence_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> EvidenceFile:
        """
        上传证据文件到COS，并保存记录到数据库

        Args:
            db: 数据库会话
            case_id: 案件ID
            file_content: 文件内容(bytes)
            filename: 原始文件名
            content_type: 文件MIME类型
            evidence_name: 证据名称
            description: 证据描述

        Returns:
            EvidenceFile: 创建的证据记录
        """
        # 验证文件类型
        if content_type.lower() not in EvidenceService.ALLOWED_TYPES:
            raise ValueError(
                f"不支持的文件类型: {content_type}。"
                f"支持的类型: {', '.join(sorted(EvidenceService.ALLOWED_TYPES))}"
            )

        # 检测证据类型
        evidence_type = EvidenceService.detect_evidence_type(content_type)

        # 生成唯一文件名
        ext = filename.split(".")[-1] if "." in filename else ""
        unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

        # 上传到COS
        cos_url = _upload_to_cos(file_content, unique_filename)

        # 如果没有提供证据名称，使用文件名
        if not evidence_name:
            evidence_name = filename or f"未命名{evidence_type}"

        # 创建数据库记录
        evidence = EvidenceFile(
            case_id=case_id,
            evidence_name=evidence_name,
            evidence_type=evidence_type,
            filename=filename,
            file_url=cos_url,
            file_size=len(file_content),
            content_type=content_type,
            description=description,
        )

        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        print(f"[证据上传] {evidence_type}: {evidence_name} -> {cos_url}")
        return evidence

    @staticmethod
    def upload_from_base64(
        db: Session,
        case_id: int,
        base64_content: str,
        filename: str,
        content_type: str,
        evidence_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> EvidenceFile:
        """从base64内容上传证据文件"""
        # 解码base64
        file_content = base64.b64decode(base64_content)

        return EvidenceService.upload_evidence(
            db=db,
            case_id=case_id,
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            evidence_name=evidence_name,
            description=description,
        )

    @staticmethod
    def get_evidences(db: Session, case_id: int) -> List[EvidenceFile]:
        """获取案件的所有证据"""
        return (
            db.query(EvidenceFile)
            .filter(EvidenceFile.case_id == case_id)
            .order_by(EvidenceFile.created_at.desc())
            .all()
        )

    @staticmethod
    def get_evidence(db: Session, evidence_id: int) -> Optional[EvidenceFile]:
        """获取单个证据记录"""
        return db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()

    @staticmethod
    def delete_evidence(db: Session, evidence_id: int) -> bool:
        """删除证据记录"""
        evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
        if evidence:
            db.delete(evidence)
            db.commit()
            print(f"[证据删除] 成功: {evidence.evidence_name}")
            return True
        return False

    @staticmethod
    def update_evidence(
        db: Session,
        evidence_id: int,
        evidence_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[EvidenceFile]:
        """更新证据信息"""
        evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
        if evidence:
            if evidence_name is not None:
                evidence.evidence_name = evidence_name
            if description is not None:
                evidence.description = description
            db.commit()
            db.refresh(evidence)
        return evidence

    @staticmethod
    def get_evidence_summary(case_id: int, db: Session) -> Dict[str, Any]:
        """获取案件证据汇总"""
        evidences = EvidenceService.get_evidences(db, case_id)

        # 按类型统计
        stats = {
            "total": len(evidences),
            "image_count": 0,
            "doc_count": 0,
            "audio_count": 0,
            "video_count": 0,
            "total_size": 0,
        }

        for e in evidences:
            if e.evidence_type == EvidenceService.TYPE_IMAGE:
                stats["image_count"] += 1
            elif e.evidence_type == EvidenceService.TYPE_DOC:
                stats["doc_count"] += 1
            elif e.evidence_type == EvidenceService.TYPE_AUDIO:
                stats["audio_count"] += 1
            elif e.evidence_type == EvidenceService.TYPE_VIDEO:
                stats["video_count"] += 1
            stats["total_size"] += e.file_size or 0

        return {
            **stats,
            "evidences": [EvidenceService._format_evidence(e) for e in evidences],
        }

    @staticmethod
    def _format_evidence(e: EvidenceFile) -> Dict[str, Any]:
        """格式化证据对象"""
        type_info = EvidenceService.TYPE_MAP.get(e.evidence_type, EvidenceService.TYPE_MAP["doc"])
        return {
            "id": e.id,
            "case_id": e.case_id,
            "evidence_name": e.evidence_name,
            "evidence_type": e.evidence_type,
            "type_label": type_info["label"],
            "type_icon": type_info["icon"],
            "type_color": type_info["color"],
            "filename": e.filename,
            "file_url": e.file_url,
            "content_type": e.content_type,
            "file_size": e.file_size,
            "description": e.description,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }


# 导出单例
evidence_service = EvidenceService()
