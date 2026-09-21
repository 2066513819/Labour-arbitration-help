"""案例检索工作流 API —— 调用专属元器工作流进行案例检索。"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.base_agent_service import YuanqiAPIClient, TextCleaner

logger = logging.getLogger(__name__)

# 初始化 API 客户端
_case_search_client: YuanqiAPIClient | None = None


def _get_client() -> YuanqiAPIClient:
    """获取或创建案例检索客户端（单例模式）。"""
    global _case_search_client
    if _case_search_client is None:
        _case_search_client = YuanqiAPIClient(
            agent_id=settings.case_search_agent_id,
            api_key=settings.case_search_api_key,
        )
    return _case_search_client


async def search_cases(
    situation: str,
    laborer_type: str,
) -> str:
    """
    调用案例检索工作流

    Args:
        situation: 用户描述的情况
        laborer_type: 劳动者类型

    Returns:
        工作流返回的原始文本
    """
    client = _get_client()

    if not client.agent_id or not client.api_key:
        raise ValueError("案例检索工作流未配置（CASE_SEARCH_AGENT_ID / CASE_SEARCH_API_KEY）")

    custom_vars = {"text": "案例检索", "Worktype": laborer_type}

    data, _ = await client.call_simple_text(
        text=situation,
        custom_variables=custom_vars,
        experience=True,
        log_prefix="[案例检索工作流]",
    )

    return YuanqiAPIClient.parse_response_text(data)


def parse_case_results(raw_text: str) -> List[Dict[str, Any]]:
    """
    从工作流返回的原始文本中解析案例结果
    尝试多种格式：Markdown、JSON、纯文本
    """
    if not raw_text:
        return []

    # 方式1：尝试 JSON 解析
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            cases = parsed.get("cases") or parsed.get("data") or []
            if isinstance(cases, list):
                return cases
    except (json.JSONDecodeError, TypeError):
        pass

    cases = []

    # 方式2：按 "案例" 或数字编号拆分 Markdown 结构
    case_blocks = re.split(
        r"\n(?=#{2,3}\s*(?:案例|案件))|"
        r"\n(?=(?:\d+[\.\、\)）])\s*(?:案例|案件))|"
        r"\n(?=#{2,3}\s*\d+\.)",
        raw_text,
    )

    if len(case_blocks) <= 1:
        case_blocks = re.split(r"\n---+\n|\n{3,}", raw_text)

    for block in case_blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue
        case = _extract_single_case(block)
        if case:
            cases.append(case)

    return cases


def _extract_single_case(text: str) -> Optional[Dict[str, Any]]:
    """从一段文本中提取单个案例信息"""
    clean_text = TextCleaner.strip_html(text)
    clean_text = TextCleaner.strip_markdown(clean_text)

    # 提取案号
    case_number = ""
    cn_match = re.search(r"(?:案号|案件编号)[：:]\s*([^\n【】]+?)(?:\n|$|【|\|)", clean_text)
    if cn_match:
        case_number = cn_match.group(1).strip()
    else:
        alt = re.search(r"[（(]\d{4}[）)]\s*[一-龥]+\d+[一-龥]*\d*号", clean_text)
        if alt:
            case_number = alt.group(0).strip()

    # 提取审理法院
    court_name = ""
    court_match = re.search(r"(?:审理法院|法院)[：:]\s*([^\n【】|]+?)(?:\n|$|【|\|)", clean_text)
    if court_match:
        court_name = court_match.group(1).strip()

    # 提取标题
    first_line = clean_text.split("\n")[0] if clean_text else ""
    title_match = re.search(
        r"(?:#{1,3}\s*)?(?:案例\d*[：:]?\s*)?(?:\d+[\.\、\)）\s]+)?(.+?)(?:[\n]|$)",
        first_line,
    )
    case_title = title_match.group(1).strip().lstrip("#0123456789.、)） ") if title_match else ""
    case_title = re.sub(r"^[#\d\.\、\)）\s]+", "", case_title).strip()
    case_title = TextCleaner.strip_html(case_title)
    case_title = TextCleaner.strip_markdown(case_title)
    if not case_title or len(case_title) < 3:
        case_title = "劳动争议案例"

    case = {
        "case_title": case_title[:80],
        "case_type": "",
        "case_summary": "",
        "ruling_result": "",
        "key_evidence": [],
        "law_basis": [],
        "relevance": 0.85,
        "case_number": case_number,
        "court_name": court_name,
    }

    # 提取案由/类型
    type_match = re.search(r"(?:案由|案件类型|类型)[：:]\s*(.+?)(?:\n|$)", clean_text)
    if type_match:
        case["case_type"] = type_match.group(1).strip()

    # 提取基本事实/案情
    fact_matches = re.search(
        r"(?:基本事实|案情简介|案件事实|案情|案情描述|正文)[：:]\s*(.+?)"
        r"(?=\n(?:裁决|判决|仲裁|案件结果|法院|结果|处理结果|证据|法律)|$)",
        clean_text, re.DOTALL,
    )
    if fact_matches:
        case["case_summary"] = fact_matches.group(1).strip()[:500]

    # 提取裁决结果
    ruling_match = re.search(
        r"(?:裁决结果|判决结果|仲裁结果|结果|处理结果)[：:]\s*(.+?)"
        r"(?=\n(?:证据|法律|法条|依据|关键|$)|\n\n)",
        clean_text, re.DOTALL,
    )
    if ruling_match:
        case["ruling_result"] = ruling_match.group(1).strip()[:300]

    # 提取关键证据
    evidence_section = re.search(
        r"(?:关键证据|证据|主要证据|胜诉证据)[：:]\s*(.+?)"
        r"(?=\n(?:法律|法条|依据|$)|\n\n)",
        clean_text, re.DOTALL,
    )
    if evidence_section:
        ev_text = evidence_section.group(1).strip()
        case["key_evidence"] = [
            e.strip().lstrip("-0123456789.、)） ")
            for e in re.split(r"[\n；;]", ev_text)
            if e.strip()
        ]

    # 提取法律依据
    law_section = re.search(
        r"(?:法律依据|法条依据|适用法律|依据)[：:]\s*(.+?)"
        r"(?=\n(?:$)|\n\n|\Z)",
        clean_text, re.DOTALL,
    )
    if law_section:
        law_text = law_section.group(1).strip()
        case["law_basis"] = [
            l.strip().lstrip("-0123456789.、)） ")
            for l in re.split(r"[\n；;]", law_text)
            if l.strip()
        ]

    # 如果没解析到摘要，去掉标题和元数据行后取剩余内容
    if not case["case_summary"]:
        remainder = clean_text
        remainder = re.sub(r"^[^\n]*案例\d*[：:]?\s*", "", remainder).strip()
        remainder = re.sub(r"^\d+[\.\、\:：\s]+", "", remainder)
        remainder = re.sub(r"^[\.\、\)）\s]+", "", remainder)
        remainder = re.sub(r"【[^】]+】\s*[^【\n]+?(?=【|$|\n)", "", remainder)
        remainder = re.sub(r"^\s*[【】]\s*", "", remainder).strip()
        if len(remainder) < 20:
            remainder = clean_text
        case["case_summary"] = remainder[:500]

    # 清理摘要
    for prefix_len in [len(case_title), len(case_title) + 1, len(case_title) + 2]:
        if prefix_len <= len(case["case_summary"]) and case["case_summary"][:prefix_len].startswith(case_title):
            case["case_summary"] = case["case_summary"][prefix_len:].strip()
            case["case_summary"] = re.sub(r"^[\.\、\)）\s：:]+", "", case["case_summary"])
            break

    case["case_summary"] = re.sub(r"^\d+[\.\、\:：\s]+", "", case["case_summary"])
    case["case_summary"] = re.sub(r"【审理法院】\s*[^【\n]*", "", case["case_summary"])
    case["case_summary"] = re.sub(r"【案号】\s*[^【\n]*", "", case["case_summary"])
    case["case_summary"] = re.sub(r"【[^】]+】", "", case["case_summary"])
    case["case_summary"] = re.sub(r"\|", " ", case["case_summary"])
    case["case_summary"] = re.sub(r"\s+", " ", case["case_summary"]).strip()
    case["case_summary"] = re.sub(r"^正文\s*", "", case["case_summary"])

    # 如果没解析到类型，尝试从标题推断
    if not case["case_type"]:
        type_keywords = [
            ("确认劳动关系", "确认劳动关系纠纷"),
            ("违法解除", "解除劳动合同纠纷"),
            ("未签合同", "劳动合同纠纷"),
            ("工资", "劳动报酬纠纷"),
            ("加班", "劳动报酬纠纷"),
            ("工伤", "工伤赔偿纠纷"),
            ("社保", "社会保险纠纷"),
            ("派遣", "劳务派遣纠纷"),
            ("平台", "新就业形态纠纷"),
            ("竞业", "竞业限制纠纷"),
            ("保密", "商业秘密纠纷"),
        ]
        for kw, tp in type_keywords:
            if kw in case_title or kw in case["case_summary"]:
                case["case_type"] = tp
                break
        if not case["case_type"]:
            case["case_type"] = "劳动争议"

    return case
