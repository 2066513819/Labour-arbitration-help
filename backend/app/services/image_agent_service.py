"""图片上传智能体 API（文书起草）。"""

import base64
import logging
from typing import Dict, List, Optional

from app.config import settings
from app.services.base_agent_service import YuanqiAPIClient

logger = logging.getLogger(__name__)

# 初始化 API 客户端
_image_agent_client: YuanqiAPIClient | None = None


def _get_client() -> YuanqiAPIClient:
    """获取或创建图片智能体客户端（单例模式）。"""
    global _image_agent_client
    if _image_agent_client is None:
        _image_agent_client = YuanqiAPIClient(
            agent_id=settings.document_agent_id,
            api_key=settings.document_agent_api_key,
            api_base="https://yuanqi.tencent.com/openapi/v1",
        )
    return _image_agent_client


async def call_document_agent(
    image_data: str,
    context: Optional[str] = None,
) -> str:
    """调用文书起草智能体，支持图片输入

    Args:
        image_data: base64 编码的图片数据（不带 data URI 前缀）
        context: 额外的上下文提示
    """
    client = _get_client()

    if not client.agent_id or not client.api_key:
        raise RuntimeError("未配置文书起草智能体 API 密钥 (DOCUMENT_AGENT_ID / DOCUMENT_AGENT_API_KEY)")

    # 构建 prompt
    prompt = "请根据上传的文书图片内容，帮我生成或完善劳动仲裁申请书。"
    if context:
        prompt = context + "\n\n" + prompt

    # 构建消息
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            }
        ]
    }]

    data, _ = await client.call(
        messages=messages,
        user_id="document_user",
        log_prefix="[文书智能体]",
    )

    return YuanqiAPIClient.parse_response_text(data)


async def call_chat_agent(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """调用文字聊天智能体

    Args:
        message: 用户消息
        history: 历史消息列表
        system_prompt: 系统提示词
    """
    client = _get_client()

    if not client.agent_id or not client.api_key:
        raise RuntimeError("未配置文书起草智能体 API 密钥 (DOCUMENT_AGENT_ID / DOCUMENT_AGENT_API_KEY)")

    # 构建消息列表
    messages: List[Dict] = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        })

    if history:
        for msg in history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": [{"type": "text", "text": msg.get("content", "")}]
            })

    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": message}]
    })

    data, _ = await client.call(
        messages=messages,
        user_id="document_chat_user",
        log_prefix="[文字聊天]",
    )

    return YuanqiAPIClient.parse_response_text(data)
