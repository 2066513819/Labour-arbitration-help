from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CaseRecord(Base):
    __tablename__ = "case_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    case_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 案件备注
    case_status: Mapped[str] = mapped_column(String(32), default="进行中")  # 案件状态：进行中/已完成/已搁置
    dispute_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_draft: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress_stage: Mapped[str] = mapped_column(String(64), default="draft")
    entry_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # 入职日期
    quit_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)   # 离职日期
    average_salary: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # 平均工资
    bonus_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 奖金信息
    extra_meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    evidences: Mapped[List["EvidenceFile"]] = relationship(
        "EvidenceFile", back_populates="case", cascade="all, delete-orphan"
    )


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("case_records.id"), index=True)
    evidence_name: Mapped[str] = mapped_column(String(255))  # 证据名称（如：劳动合同、工资条）
    evidence_type: Mapped[str] = mapped_column(String(32), default="image")  # 证据类型：image/doc/audio/video
    filename: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 原始文件名
    file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # COS URL
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 文件大小(bytes)
    content_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 证据描述/备注
    ocr_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["CaseRecord"] = relationship("CaseRecord", back_populates="evidences")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    structured_reply: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ui_meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
