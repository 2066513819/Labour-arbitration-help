from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import traceback

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.law_search_workflow_service import (
    search_laws,
    parse_law_results,
    extract_suggestions,
)

router = APIRouter(prefix="/law", tags=["law"])


class LawSearchRequest(BaseModel):
    """法律条文检索请求"""
    situation: str  # 用户描述的情况
    laborer_type: Optional[str] = None  # 劳动者类型
    keywords: Optional[List[str]] = None  # 关键词（可选）


class LawClause(BaseModel):
    """法条条目"""
    law_name: str  # 法律名称
    article_number: str  # 条款编号
    content: str  # 条款内容
    relevance: float = 1.0  # 相关度 0-1
    title: Optional[str] = None  # 法条主题标题
    keyword: Optional[str] = None  # 关键词标签


class LawSearchResponse(BaseModel):
    """法律条文检索响应"""
    success: bool
    matched_clauses: List[LawClause]
    summary: str  # AI总结
    suggestions: List[str]  # 维权建议
    raw_response: Optional[str] = None  # 原始AI回复


@router.post("/search", response_model=LawSearchResponse)
async def search_law(
    body: LawSearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    法律条文检索接口
    
    根据用户描述的情况，检索相关的劳动法律法规条文
    """
    lt = body.laborer_type or user.laborer_type
    if not lt:
        raise HTTPException(400, "请先选择劳动者类型")
    
    try:
        # 调用专属法条检索工作流
        raw_text = await search_laws(
            situation=body.situation,
            laborer_type=lt,
        )

        # 从工作流返回结果中解析法条
        matched_clauses = parse_law_results(raw_text)
        suggestions = extract_suggestions(raw_text)
        summary = raw_text[:500] if raw_text else "根据您的情况，已为您匹配相关法律条文"

        if not matched_clauses:
            # 解析失败，使用默认法条兜底
            matched_clauses = [
                LawClause(
                    law_name="《中华人民共和国劳动合同法》",
                    article_number="第10条",
                    content="建立劳动关系，应当订立书面劳动合同。",
                    relevance=0.6,
                ),
                LawClause(
                    law_name="《中华人民共和国劳动合同法》",
                    article_number="第82条",
                    content="用人单位自用工之日起超过一个月不满一年未与劳动者订立书面劳动合同的，应当向劳动者每月支付二倍的工资。",
                    relevance=0.6,
                ),
            ]
            summary = raw_text[:500] if raw_text else "工作流未返回有效数据，以下为通用法条建议"

        return LawSearchResponse(
            success=True,
            matched_clauses=matched_clauses,
            summary=summary,
            suggestions=suggestions,
            raw_response=raw_text,
        )

    except ValueError as e:
        raise HTTPException(500, f"法条检索配置错误: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"法律条文检索失败: {str(e)}")


@router.get("/quick-categories")
async def get_quick_categories():
    """
    获取常用法律检索分类（快速入口）
    """
    return {
        "categories": [
            {
                "id": "contract",
                "name": "劳动合同签订",
                "icon": "📝",
                "examples": ["未签劳动合同", "合同到期不续签", "劳动合同条款不合理"]
            },
            {
                "id": "wages",
                "name": "工资与加班",
                "icon": "💰",
                "examples": ["拖欠工资", "加班费不给", "扣押工资"]
            },
            {
                "id": "dismissal",
                "name": "解除与终止",
                "icon": "🚪",
                "examples": ["违法解除", "强制离职", "经济性裁员"]
            },
            {
                "id": "work_injury",
                "name": "工伤认定",
                "icon": "🏥",
                "examples": ["工伤认定", "工伤赔偿", "职业病"]
            },
            {
                "id": "social",
                "name": "社会保险",
                "icon": "🏦",
                "examples": ["未缴社保", "社保转移", "公积金"]
            },
            {
                "id": "leave",
                "name": "休假与福利",
                "icon": "🏖️",
                "examples": ["年假未休", "产假待遇", "病假工资"]
            },
            {
                "id": "dispatch",
                "name": "劳务派遣",
                "icon": "📋",
                "examples": ["同工不同酬", "派遣转外包", "退回派遣工"]
            },
            {
                "id": "platform",
                "name": "新就业形态",
                "icon": "🚗",
                "examples": ["外卖骑手", "网约车司机", "平台主播"]
            }
        ]
    }
