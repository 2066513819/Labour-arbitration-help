"""元器 API：智能法律咨询（未配置时本地规则回复，保证可用）。"""

import json
import logging
import time
import uuid
from typing import List, Optional, Tuple

from app.config import settings
from app.data.scenario_catalog import SCENARIOS
from app.schemas.agent import AgentStructuredReply, Message
from app.services.base_agent_service import YuanqiAPIClient

logger = logging.getLogger(__name__)

# 劳动者类型英文→中文映射
_LABOR_TYPE_CN = {
    "regular": "正式工",
    "dispatch": "劳务派遣",
    "intern": "实习/兼职",
    "platform": "平台工",
    "courier": "其他/不确定",
    "other_uncertain": "其他/不确定",
    "formal": "正式工",  # 兼容前端部分页面使用的 formal
}

# 初始化 API 客户端
_yuanqi_client: Optional[YuanqiAPIClient] = None


def _get_client() -> YuanqiAPIClient:
    """获取或创建元器 API 客户端（单例模式）。"""
    global _yuanqi_client
    if _yuanqi_client is None:
        if settings.yuanqi_agent_id and settings.yuanqi_api_key:
            _yuanqi_client = YuanqiAPIClient(
                agent_id=settings.yuanqi_agent_id,
                api_key=settings.yuanqi_api_key,
                api_base=settings.yuanqi_api_base,
            )
    return _yuanqi_client


async def ask_agent(
    *,
    question: str,
    laborer_type: Optional[str],
    history: Optional[List[Message]] = None,
    is_first: bool = False,
    user_id: Optional[str] = None,
) -> Tuple[AgentStructuredReply, int]:
    """智能咨询主入口。

    如果配置了 API 则调用远程服务，否则使用本地规则回复。

    Args:
        user_id: 持久化用户标识。传入真实用户 ID 可确保元器平台维持稳定的
                 session 上下文，避免 "redis: nil" 错误。
    """
    t0 = time.perf_counter()
    client = _get_client()

    if client:
        reply, ms = await _remote(client, question, laborer_type, history, user_id=user_id)
        return reply, ms

    reply = _local_fallback(question, laborer_type)
    ms = int((time.perf_counter() - t0) * 1000)
    return reply, ms


async def _remote(
    client: YuanqiAPIClient,
    question: str,
    laborer_type: Optional[str],
    history: Optional[List[Message]] = None,
    user_id: Optional[str] = None,
) -> Tuple[AgentStructuredReply, int]:
    """调用腾讯元器智能体 API。"""
    t0 = time.perf_counter()

    # 构建消息列表
    messages = []
    if history:
        for msg in history:
            role = msg.role.lower() if msg.role in ["user", "assistant"] else "user"
            messages.append({
                "role": role,
                "content": [{"type": "text", "text": msg.content}],
            })

    # 添加当前用户消息
    messages.append({"role": "user", "content": [{"type": "text", "text": question}]})

    # 自定义变量
    custom_vars = None
    if laborer_type:
        cn_type = _LABOR_TYPE_CN.get(laborer_type, laborer_type)
        custom_vars = {"text": cn_type, "Worktype": cn_type}
        logger.info(f"[元器API] 传递 text/Worktype: {cn_type} (原始: {laborer_type})")

    try:
        data, api_ms = await client.call(
            messages=messages,
            user_id=user_id,
            custom_variables=custom_vars,
            experience=True,
            log_prefix="[元器API]",
        )

        # 解析响应
        reply = _parse_yuanqi_response(data, question, laborer_type)
        return reply, api_ms

    except Exception as e:
        logger.error(f"[元器API] 调用失败: {e}")
        total_ms = int((time.perf_counter() - t0) * 1000)
        fallback = _local_fallback(question, laborer_type)
        fallback.interpretation = (
            "元器 API 返回错误，已自动切换到离线演示模式。\n"
            f"错误信息：{str(e)[:400]}"
        )
        return fallback, total_ms


def _parse_yuanqi_response(
    data: dict, original_question: str, laborer_type: Optional[str]
) -> AgentStructuredReply:
    """解析元器 API 响应，提取结构化内容。"""
    logger.debug(f"[元器API] 开始解析响应: {json.dumps(data, ensure_ascii=False)[:2000]}")

    # 使用基础客户端的解析方法
    parsed = YuanqiAPIClient.parse_structured_response(
        data,
        default_restate=f"您的问题涉及：{original_question[:50]}...",
        default_interpretation="正在处理您的问题...",
    )

    # 如果返回了纯文本（没有解析出JSON），尝试提取关键信息
    if not parsed["law_refs"]:
        text = parsed["interpretation"]
        parsed["law_refs"] = _extract_law_refs(text)
        parsed["suggested_actions"] = _extract_suggested_actions(text)

    return AgentStructuredReply(
        restate=parsed["restate"],
        law_refs=parsed["law_refs"],
        interpretation=parsed["interpretation"],
        suggested_actions=parsed["suggested_actions"],
        linked_scenario_ids=parsed["linked_scenario_ids"],
    )


def _extract_law_refs(text: str) -> List[str]:
    """从文本中提取法律依据。"""
    law_refs = []
    laws = [
        "中华人民共和国劳动合同法",
        "中华人民共和国劳动法",
        "劳动争议调解仲裁法",
        "工伤保险条例",
        "最高人民法院关于审理劳动争议案件适用法律问题的解释",
        "工资支付暂行规定",
        "社会保险法",
    ]

    for law in laws:
        if law in text:
            law_refs.append(f"《{law}》")

    if not law_refs:
        law_refs = [
            "《中华人民共和国劳动合同法》",
            "《劳动争议调解仲裁法》",
        ]

    return law_refs


def _extract_suggested_actions(text: str) -> List[str]:
    """从文本中提取建议操作。"""
    actions = []

    if any(kw in text for kw in ["收集证据", "证据", "保存"]):
        actions.append("收集并保存相关证据材料")
    if any(kw in text for kw in ["协商", "调解"]):
        actions.append("尝试与用人单位协商或申请调解")
    if any(kw in text for kw in ["仲裁", "仲裁委"]):
        actions.append("向当地劳动争议仲裁委员会申请仲裁")
    if any(kw in text for kw in ["诉讼", "法院"]):
        actions.append("对仲裁裁决不服可向人民法院提起诉讼")

    if not actions:
        actions = [
            "详细记录事件经过和关键时间点",
            "收集整理相关证据材料",
            "如有需要可咨询专业律师",
        ]

    return actions


def _local_fallback(question: str, laborer_type: Optional[str]) -> AgentStructuredReply:
    """本地回退逻辑（当未配置 API 时使用）。"""
    scenarios = SCENARIOS.get(laborer_type or "other_uncertain", SCENARIOS["other_uncertain"])
    linked: List[str] = [s["id"] for s in scenarios[:2]]
    return AgentStructuredReply(
        restate=f"您的问题涉及：{question[:120]}{'…' if len(question) > 120 else ''}",
        law_refs=[
            "《中华人民共和国劳动合同法》",
            "《劳动争议调解仲裁法》",
            "与场景匹配的具体条款请以仲裁委审查为准",
        ],
        interpretation=(
            "当前为离线演示模式：已根据问题生成结构化指引。"
            "配置元器 API 后将返回更精准的条文匹配与维权建议。"
            "建议同步整理合同、工资流水、考勤、聊天截图等证据。"
        ),
        suggested_actions=[
            "在系统中选择对应劳动者类型与细分纠纷场景",
            "上传关键证据并完成 OCR 校对",
            "生成仲裁申请书并前往当地仲裁委提交",
        ],
        linked_scenario_ids=linked,
    )
