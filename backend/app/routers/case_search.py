from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import traceback

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.case_search_workflow_service import (
    search_cases,
    parse_case_results,
)

router = APIRouter(prefix="/case-search", tags=["case-search"])


class CaseSearchRequest(BaseModel):
    """案例检索请求"""
    situation: str  # 用户描述的情况
    laborer_type: Optional[str] = None  # 劳动者类型


class CaseResult(BaseModel):
    """案例结果"""
    case_title: str  # 案例标题
    case_type: str  # 案例类型
    case_summary: str  # 案例摘要
    ruling_result: str  # 裁决结果
    key_evidence: List[str] = []  # 关键证据
    law_basis: List[str] = []  # 法律依据
    relevance: float = 1.0  # 相关度


class CaseSearchResponse(BaseModel):
    """案例检索响应"""
    success: bool
    total_count: int  # 匹配案例总数
    cases: List[CaseResult]  # 案例列表
    analysis: str  # 案例分析总结
    suggestions: List[str]  # 维权建议


@router.post("/search", response_model=CaseSearchResponse)
async def search_case(
    body: CaseSearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    案例检索接口
    
    根据用户描述的情况，检索相似的劳动争议案例
    """
    lt = body.laborer_type or user.laborer_type
    if not lt:
        raise HTTPException(400, "请先选择劳动者类型")

    try:
        # 调用专属案例检索工作流
        raw_text = await search_cases(
            situation=body.situation,
            laborer_type=lt,
        )

        # 从工作流返回结果中解析案例
        parsed_cases = parse_case_results(raw_text)

        if parsed_cases:
            cases = []
            for c in parsed_cases[:5]:
                cases.append(CaseResult(
                    case_title=c.get("case_title", "劳动争议案例"),
                    case_type=c.get("case_type", "劳动争议"),
                    case_summary=c.get("case_summary", ""),
                    ruling_result=c.get("ruling_result", ""),
                    key_evidence=c.get("key_evidence", []),
                    law_basis=c.get("law_basis", []),
                    relevance=c.get("relevance", 0.85),
                ))
        else:
            # 解析失败，返回空列表 + 原始文本作为分析
            cases = []
            raw_text = raw_text or "工作流未返回有效案例数据"

        return CaseSearchResponse(
            success=True,
            total_count=len(cases),
            cases=cases,
            analysis=raw_text[:800] if raw_text else "根据您的情况，已为您匹配相似案例",
            suggestions=[
                "参考相似案例的裁决结果",
                "准备相关证据材料",
                "必要时可咨询专业律师",
            ],
        )

    except ValueError as e:
        # 配置错误
        raise HTTPException(500, f"案例检索配置错误: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"案例检索失败: {str(e)}")


@router.get("/quick-types")
async def get_quick_case_types():
    """
    获取常用案例检索分类
    """
    return {
        "types": [
            {
                "id": "no_contract",
                "name": "未签劳动合同",
                "icon": "📝",
                "description": "入职后未签订书面劳动合同的相关案例"
            },
            {
                "id": "illegal_dismissal",
                "name": "违法解除",
                "icon": "🚪",
                "description": "公司违法解除或终止劳动合同的案例"
            },
            {
                "id": "wage_arreas",
                "name": "工资拖欠",
                "icon": "💰",
                "description": "拖欠工资、加班费的劳动争议案例"
            },
            {
                "id": "work_injury",
                "name": "工伤纠纷",
                "icon": "🏥",
                "description": "工伤认定、工伤赔偿的相关案例"
            },
            {
                "id": "dispatch_dispute",
                "name": "劳务派遣争议",
                "icon": "📋",
                "description": "劳务派遣中的同工不同酬、退回等案例"
            },
            {
                "id": "platform_dispute",
                "name": "平台用工争议",
                "icon": "🚗",
                "description": "外卖骑手、网约车等新就业形态案例"
            },
            {
                "id": "overtime_dispute",
                "name": "加班费争议",
                "icon": "⏰",
                "description": "加班费计算、支付的劳动争议案例"
            },
            {
                "id": "social_insurance",
                "name": "社保公积金",
                "icon": "🏦",
                "description": "未缴社保、公积金补缴的相关案例"
            },
        ]
    }





