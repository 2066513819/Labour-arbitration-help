"""法条检索工作流 API —— 调用专属元器工作流进行法律条文检索。"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.base_agent_service import YuanqiAPIClient, TextCleaner

logger = logging.getLogger(__name__)

# 初始化 API 客户端
_law_search_client: YuanqiAPIClient | None = None


def _get_client() -> YuanqiAPIClient:
    """获取或创建法条检索客户端（单例模式）。"""
    global _law_search_client
    if _law_search_client is None:
        _law_search_client = YuanqiAPIClient(
            agent_id=settings.law_search_agent_id,
            api_key=settings.law_search_api_key,
        )
    return _law_search_client


async def search_laws(
    situation: str,
    laborer_type: str,
) -> str:
    """
    调用法条检索工作流

    Args:
        situation: 用户描述的情况
        laborer_type: 劳动者类型

    Returns:
        工作流返回的原始文本
    """
    client = _get_client()

    if not client.agent_id or not client.api_key:
        raise ValueError("法条检索工作流未配置（LAW_SEARCH_AGENT_ID / LAW_SEARCH_API_KEY）")

    custom_vars = {"text": "法规检索", "Worktype": laborer_type}

    data, _ = await client.call_simple_text(
        text=situation,
        custom_variables=custom_vars,
        experience=True,
        log_prefix="[法条检索工作流]",
    )

    return YuanqiAPIClient.parse_response_text(data)


def parse_law_results(raw_text: str, max_items: int = 10) -> List[Dict[str, Any]]:
    """
    从工作流返回的原始文本中解析法条列表。
    兼容多种格式：
      A) 结构化 JSON 数组
      B) Markdown 格式：### 📍 标题 · 【关键词】\n<small>正文</small>
      C) 数字编号格式：1. 《法律名称》... 2. 《法律名称》...\n
    """
    if not raw_text:
        return []

    # 先清理 HTML
    clean_text = TextCleaner.strip_html(raw_text)

    clauses = []

    # 方式1：尝试 JSON 解析
    try:
        parsed = json.loads(clean_text.strip())
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    clause = {
                        "law_name": item.get("law_name") or item.get("lawName") or "相关法律",
                        "article_number": item.get("article_number") or item.get("articleNumber") or "",
                        "content": item.get("content") or item.get("条款内容", ""),
                        "relevance": float(item.get("relevance") or item.get("相关度", 0.8)),
                    }
                    if clause["content"]:
                        clauses.append(clause)
            if clauses:
                return clauses[:max_items]
    except (json.JSONDecodeError, TypeError):
        pass

    # 方式2：按数字编号格式分割（如 1. 《劳动合同法》... 2. 《司法解释》...）
    numbered_blocks = _split_by_numbered_items(clean_text)
    logger.info(f"[法条解析] 编号分割得到 {len(numbered_blocks)} 个块")
    if numbered_blocks:
        for idx, block in enumerate(numbered_blocks):
            clause = _parse_single_law_block(block)
            logger.info(f"[法条解析] 块{idx+1}解析结果: {clause is not None}, 名称={clause['law_name'] if clause else 'None'}")
            if clause:
                clauses.append(clause)
        if clauses:
            return clauses[:max_items]

    # 方式3：按 Markdown 标题分割法条条目（兜底）
    body_text = re.sub(r"^(.*?)(?=###\s+📍|###\s+[一-龥]|📍)", "", clean_text, flags=re.DOTALL)
    if not body_text.strip():
        body_text = clean_text

    blocks = re.split(
        r"\n(?=###\s+📍\s+)|\n(?=###\s+[一-龥])|\n(?=📍\s+)",
        body_text,
    )

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 10:
            continue

        title_match = re.match(
            r"#{0,3}\s*📍?\s*(.+?)(?:\s*[·•]\s*【(.+?)】)?\s*(?:\n|$)",
            block,
        )
        if not title_match:
            continue

        title = title_match.group(1).strip()
        keyword = title_match.group(2) or ""
        full_title = f"{title} · 【{keyword}】" if keyword else title

        body = block[title_match.end():].strip()
        body = TextCleaner.strip_markdown(body)

        if not body or len(body) < 5:
            continue

        article = _extract_article_from_text(body, title)

        clauses.append({
            "law_name": _detect_law_name(block),
            "article_number": article or "相关条款",
            "content": body,
            "title": full_title,
            "keyword": keyword,
            "relevance": 0.85,
        })

    # 去重
    seen = set()
    unique = []
    for c in clauses:
        key = (c["law_name"], c["article_number"], c["content"][:30])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique[:max_items]


def _split_by_numbered_items(text: str) -> List[str]:
    """
    按数字编号分割文本块。
    直接在文本中搜索 "N. 《名称》" 的位置并切片，不依赖换行。
    """
    text = text.strip()
    # 找出所有匹配 "N. 《名称》" 的起始位置
    matches = list(re.finditer(r'\d+[\.、\)）]?\s*《[^》]+》', text))
    if not matches:
        return []

    blocks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        if block:
            blocks.append(block)
    return blocks


def _parse_single_law_block(block: str) -> Optional[Dict[str, Any]]:
    """
    解析单个法条编号块，返回干净的结构化数据。
    """
    # 提取法律名称（第一个《...》）
    name_match = re.search(r'《([^》]+)》', block)
    law_name = f"《{name_match.group(1)}》" if name_match else getattr(settings, 'DEFAULT_LAW_NAME', "相关法律")

    # 提取文号行
    doc_match = re.search(r'文号[：:]\s*([^\n]+)', block)
    doc_number = doc_match.group(1).strip().rstrip('，。,') if doc_match else ""

    # 提取效力状态
    status_match = re.search(r'(已被修改|有效|失效|废止)', block)
    status = status_match.group(1) if status_match else ""

    # 提取条款编号
    article = _extract_article_from_text(block, law_name)

    # === 清理 content ===
    content = block

    # 1. 去掉开头的编号（如 "1. " / "1、"）
    content = re.sub(r'^\d+[\.、\)）]?\s*', '', content)

    # 2. 去掉法律名称（行首或紧跟编号，不依赖换行）
    content = re.sub(r'^《[^》]+》\s*', '', content)

    # 3. 去掉文号行
    content = re.sub(r'文号[：:]\s*[^\n]*', '', content)

    # 4. 去掉效力状态（作为整行，或独立词）
    content = re.sub(r'^[\s]*(?:已被修改|有效|失效|废止)[\s]*$', '', content, flags=re.MULTILINE)

    # 5. 去掉 "核心法条摘要" / "CONTENTS SUMMARY" 及其组合
    content = re.sub(r'🔍?\s*核心法条摘要\s*CONTENTS\s*SUMMARY', '', content, flags=re.IGNORECASE)
    content = re.sub(r'🔍?\s*核心法条摘要', '', content)
    content = re.sub(r'CONTENTS\s*SUMMARY', '', content, flags=re.IGNORECASE)

    # 6. 去掉 "总则"（作为整行）
    content = re.sub(r'^[\s]*总则[\s]*$', '', content, flags=re.MULTILINE)

    # 7. 去掉截断提示
    content = re.sub(r'[…\.]+\s*\(正文较长，此处仅展示核心概要\)', '', content)
    content = re.sub(r'\(正文较长，此处仅展示核心概要\)', '', content)

    # 8. 合并多余空白和换行
    content = re.sub(r'\n{2,}', '\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = content.strip()
    content = content.strip('\n，。 ')

    if not content or len(content) < 5:
        return None

    return {
        "law_name": law_name,
        "article_number": article or "相关条款",
        "content": content,
        "doc_number": doc_number,
        "status": status,
        "relevance": 0.85,
    }


def extract_suggestions(raw_text: str) -> List[str]:
    """从法条检索结果中提取维权建议"""
    if not raw_text:
        return [
            "建议保留相关证据材料",
            "及时向劳动仲裁机构申请仲裁",
            "必要时可咨询专业律师",
        ]

    clean_text = TextCleaner.strip_html(raw_text)
    clean_text = TextCleaner.strip_markdown(clean_text)

    suggestions = []

    suggestion_section = re.search(
        r"(?:维权建议|建议|注意事项)[：:]\s*(.+?)(?:\Z)",
        clean_text,
        re.DOTALL,
    )

    if suggestion_section:
        sug_text = suggestion_section.group(1).strip()
        items = re.split(r"[\n；;]", sug_text)
        for item in items:
            item = re.sub(r"^\d+[\.\、\)）]\s*", "", item).strip()
            if item and len(item) > 4:
                suggestions.append(item)

    if not suggestions:
        suggestions = [
            "建议保留相关证据材料",
            "及时向劳动仲裁机构申请仲裁",
            "必要时可咨询专业律师",
        ]

    return suggestions[:8]


def _detect_law_name(raw_text: str) -> str:
    """从文本中推断法律名称"""
    text = raw_text[:500]
    mapping = {
        "劳动合同法": "《中华人民共和国劳动合同法》",
        "劳动法": "《中华人民共和国劳动法》",
        "劳动争议调解仲裁法": "《劳动争议调解仲裁法》",
        "工伤保险条例": "《工伤保险条例》",
        "工资支付暂行规定": "《工资支付暂行规定》",
        "社会保险法": "《中华人民共和国社会保险法》",
    }
    for key, val in mapping.items():
        if key in text:
            return val
    if "主席令" in text and "劳动合同" in text:
        return "《中华人民共和国劳动合同法》"
    return "相关法律"


# 标题→条款编号的映射（劳动合同法常见条目）
_TITLE_TO_ARTICLE = {
    "加班": "第31条",
    "加班费": "第31条",
    "经济补偿": "第46条",
    "经济补偿的计算": "第47条",
    "违法解除": "第48条",
    "违法解除或者终止劳动合同法律后果": "第48条",
    "解除和终止": "第44条",
    "劳动合同的解除和终止": "第44条",
    "劳动合同的履行和变更": "第29条",
    "履行和变更": "第29条",
    "试用期": "第19条",
    "劳动合同期限": "第12条",
    "无固定期限": "第14条",
    "订立": "第10条",
    "劳动合同的订立": "第10条",
    "工资": "第30条",
    "社会保险": "第17条",
    "服务期": "第22条",
    "竞业限制": "第23条",
    "培训": "第22条",
    "保密": "第23条",
    "劳务派遣": "第58条",
    "非全日制": "第68条",
}

# 中文数字→阿拉伯数字
_CN_NUMS = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
    "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
    "二十一": 21, "二十二": 22, "二十三": 23, "二十四": 24, "二十五": 25,
    "二十六": 26, "二十七": 27, "二十八": 28, "二十九": 29, "三十": 30,
    "三十一": 31, "三十二": 32, "三十三": 33, "三十四": 34, "三十五": 35,
    "三十六": 36, "三十七": 37, "三十八": 38, "三十九": 39, "四十": 40,
    "四十一": 41, "四十二": 42, "四十三": 43, "四十四": 44, "四十五": 45,
    "四十六": 46, "四十七": 47, "四十八": 48, "四十九": 49, "五十": 50,
    "八十二": 82, "八十七": 87,
}


def _cn_to_arabic(cn: str) -> str:
    """中文数字如'八十七' → '87'"""
    cn = cn.strip()
    if cn.isdigit():
        return cn
    if cn in _CN_NUMS:
        return str(_CN_NUMS[cn])
    if len(cn) == 2 and cn[0] in _CN_NUMS and cn[1] in _CN_NUMS:
        return str(_CN_NUMS[cn[0]] * 10 + _CN_NUMS[cn[1]])
    if cn.startswith("十") and len(cn) == 2 and cn[1] in _CN_NUMS:
        return str(10 + _CN_NUMS[cn[1]])
    return cn


def _extract_article_from_text(text: str, title: str) -> str:
    """从正文和标题中提取条款编号"""
    m = re.search(r"第([一二三四五六七八九十百千\d]+)条", text)
    if m:
        return f"第{_cn_to_arabic(m.group(1))}条"

    m2 = re.search(r"(?:本法|本条款?|依照本法)(?:第)?([一二三四五六七八九十百千\d]+)[条章]", text)
    if m2:
        return f"第{_cn_to_arabic(m2.group(1))}条"

    for kw, article in _TITLE_TO_ARTICLE.items():
        if kw in title:
            return article

    return ""
