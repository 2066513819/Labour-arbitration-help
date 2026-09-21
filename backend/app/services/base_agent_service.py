"""元器 API 基础客户端 —— 封装通用的智能体调用逻辑。"""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# 默认超时配置
DEFAULT_TIMEOUT = httpx.Timeout(360.0, connect=30.0)


class YuanqiAPIClient:
    """腾讯元器 API 基础客户端。

    封装通用的 HTTP 调用逻辑：
    - 请求头构建 (Authorization Bearer)
    - 请求体构建 (assistant_id, user_id, messages, custom_variables)
    - 400 错误降级处理（数组/字符串 content 格式自动切换）
    - 响应解析
    - 耗时计算和日志记录
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        api_base: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
    ):
        """
        Args:
            agent_id: 智能体 ID
            api_key: API 密钥
            api_base: API 基础地址，默认使用 settings.workflow_api_base
            timeout: 请求超时配置
        """
        self.agent_id = agent_id
        self.api_key = api_key
        self.api_base = (api_base or settings.workflow_api_base or "").strip().strip("`").strip('"').strip("'")
        self.timeout = timeout or DEFAULT_TIMEOUT

    def _get_api_url(self) -> str:
        """获取完整的 API 调用地址。"""
        base = self.api_base.rstrip("/")
        return f"{base}/agent/chat/completions"

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头。"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Source": "openapi",
        }

    def _build_body(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        custom_variables: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **extra_fields,
    ) -> Dict[str, Any]:
        """构建请求体。

        Args:
            messages: 消息列表
            user_id: 用户 ID，默认自动生成
            custom_variables: 自定义变量
            stream: 是否流式响应
            **extra_fields: 额外字段（如 experience=True）
        """
        body: Dict[str, Any] = {
            "assistant_id": self.agent_id,
            "user_id": user_id or f"user_{uuid.uuid4().hex[:8]}",
            "stream": stream,
            "messages": messages,
        }
        if custom_variables:
            body["custom_variables"] = custom_variables
        body.update(extra_fields)
        return body

    async def call(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        custom_variables: Optional[Dict[str, str]] = None,
        log_prefix: str = "[元器API]",
        **extra_fields,
    ) -> Tuple[Dict[str, Any], int]:
        """调用元器 API。

        Args:
            messages: 消息列表
            user_id: 用户 ID
            custom_variables: 自定义变量
            log_prefix: 日志前缀
            **extra_fields: 额外请求字段

        Returns:
            (响应数据字典, 耗时毫秒数)

        Raises:
            ValueError: API 基础地址未配置
            httpx.HTTPStatusError: HTTP 请求失败（除 400 降级外）
        """
        if not self.api_base:
            raise ValueError("未配置 API 基础地址")

        t0 = time.perf_counter()
        url = self._get_api_url()
        headers = self._build_headers()
        body = self._build_body(messages, user_id, custom_variables, **extra_fields)

        logger.info(f"{log_prefix} 请求地址: {url}")
        logger.info(f"{log_prefix} 消息数: {len(messages)}, user_id: {body.get('user_id')}, experience: {body.get('experience')}")
        logger.info(f"{log_prefix} 请求体: {json.dumps(body, ensure_ascii=False)[:800]}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, headers=headers, json=body)

            logger.info(f"{log_prefix} 响应状态: {r.status_code}")

            # 400 错误降级：尝试字符串 content 格式
            if r.status_code == 400:
                try_body = dict(body)
                try_body["messages"] = [
                    {
                        "role": m.get("role", "user"),
                        "content": (
                            (m.get("content") or [{"type": "text", "text": ""}])[0].get("text", "")
                            if isinstance(m.get("content"), list)
                            else m.get("content", "")
                        ),
                    }
                    for m in messages
                ]
                logger.info(f"{log_prefix} 400 参数错误，尝试降级为字符串 content 格式")
                r = await client.post(url, headers=headers, json=try_body)
                logger.info(f"{log_prefix} 重试响应状态: {r.status_code}")

            if r.status_code != 200:
                error_text = r.text[:500]
                logger.error(f"{log_prefix} 错误响应: {error_text}")
                r.raise_for_status()

            data = r.json()
            logger.debug(f"{log_prefix} 响应数据: {json.dumps(data, ensure_ascii=False)[:1000]}")

        ms = int((time.perf_counter() - t0) * 1000)
        logger.info(f"{log_prefix} 耗时: {ms}ms")

        return data, ms

    async def call_simple_text(
        self,
        text: str,
        user_id: Optional[str] = None,
        custom_variables: Optional[Dict[str, str]] = None,
        log_prefix: str = "[元器API]",
        **extra_fields,
    ) -> Tuple[Dict[str, Any], int]:
        """调用 API 发送简单文本消息。

        Args:
            text: 用户输入文本
            user_id: 用户 ID
            custom_variables: 自定义变量
            log_prefix: 日志前缀
            **extra_fields: 额外请求字段
        """
        messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        return await self.call(
            messages=messages,
            user_id=user_id,
            custom_variables=custom_variables,
            log_prefix=log_prefix,
            **extra_fields,
        )

    @staticmethod
    def parse_response_text(data: Dict[str, Any]) -> str:
        """从响应数据中提取文本内容。

        处理两种 content 格式：
        1. 字符串格式
        2. 数组格式：[{"type": "text", "text": "..."}]
        """
        choices = data.get("choices", [])
        if not choices:
            # 兜底：尝试其他字段
            if "data" in data:
                return str(data["data"])
            return str(data)

        message = choices[0].get("message", {})
        content = message.get("content", "")

        # 处理数组格式 content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "".join(text_parts)
        elif not isinstance(content, str):
            content = str(content) if content else ""

        return content if content else ""

    @staticmethod
    def parse_structured_response(
        data: Dict[str, Any],
        default_restate: str = "",
        default_interpretation: str = "正在处理您的问题...",
    ) -> Dict[str, Any]:
        """解析结构化响应，支持 JSON 格式或文本格式。

        Returns:
            包含 restate, law_refs, interpretation, suggested_actions, linked_scenario_ids 的字典
        """
        text = YuanqiAPIClient.parse_response_text(data)

        # 尝试解析 JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return {
                    "restate": parsed.get("restate", default_restate),
                    "law_refs": list(parsed.get("law_refs", [])),
                    "interpretation": parsed.get("interpretation", text),
                    "suggested_actions": list(parsed.get("suggested_actions", [])),
                    "linked_scenario_ids": list(parsed.get("linked_scenario_ids", [])),
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # 纯文本格式
        return {
            "restate": default_restate,
            "law_refs": [],
            "interpretation": text if text else default_interpretation,
            "suggested_actions": [],
            "linked_scenario_ids": [],
        }


class TextCleaner:
    """文本清理工具类。

    统一处理 HTML 标签和 Markdown 标记的清理。
    """

    _HTML_TAG_RE = None

    @classmethod
    def _get_html_tag_re(cls):
        if cls._HTML_TAG_RE is None:
            import re

            cls._HTML_TAG_RE = re.compile(r"<[^>]+>")
        return cls._HTML_TAG_RE

    @classmethod
    def strip_html(cls, text: str) -> str:
        """清除 HTML 标签，将 <br>, <p>, <div> 等转换为换行。"""
        import re

        text = re.sub(r"<br\s*/?>|</?p>|</?div>", "\n", text, flags=re.IGNORECASE)
        text = cls._get_html_tag_re().sub("", text)
        return text

    @classmethod
    def strip_markdown(cls, text: str) -> str:
        """清理 Markdown 标记，保留纯文本。"""
        import re

        text = re.sub(r"\*\*", "", text)  # 粗体
        text = re.sub(r"__", "", text)  # 斜体
        text = re.sub(r"`", "", text)  # 代码
        text = re.sub(r"#{1,6}\s*", "", text)  # 标题
        return text


# 保持向后兼容的模块级函数
def parse_response_text(data: Dict[str, Any]) -> str:
    """从响应数据中提取文本内容（兼容函数）。"""
    return YuanqiAPIClient.parse_response_text(data)


def strip_html(text: str) -> str:
    """清除 HTML 标签（兼容函数）。"""
    return TextCleaner.strip_html(text)


def strip_markdown(text: str) -> str:
    """清理 Markdown 标记（兼容函数）。"""
    return TextCleaner.strip_markdown(text)
