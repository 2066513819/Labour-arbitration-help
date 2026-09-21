"""元器工作流 API（文书起草）- 使用腾讯云COS上传。"""

import base64
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.config import settings
from app.services.base_agent_service import YuanqiAPIClient

logger = logging.getLogger(__name__)

# 初始化 API 客户端
_workflow_client: YuanqiAPIClient | None = None


def _get_client() -> YuanqiAPIClient:
    """获取或创建工作流客户端（单例模式）。"""
    global _workflow_client
    if _workflow_client is None:
        _workflow_client = YuanqiAPIClient(
            agent_id=settings.workflow_agent_id,
            api_key=settings.workflow_api_key,
        )
    return _workflow_client


def _upload_to_cos(content: bytes, filename: str) -> str:
    """上传文件到腾讯云COS，返回公网URL"""
    import os

    from qcloud_cos import CosConfig, CosS3Client

    cos_secret_id = os.getenv("COS_SECRET_ID", "")
    cos_secret_key = os.getenv("COS_SECRET_KEY", "")
    cos_bucket = os.getenv("COS_BUCKET", "")
    cos_region = os.getenv("COS_REGION", "ap-guangzhou")
    cos_base_url = os.getenv("COS_BASE_URL", "")

    config = CosConfig(
        Region=cos_region,
        SecretId=cos_secret_id,
        SecretKey=cos_secret_key,
    )
    client = CosS3Client(config)

    ext = filename.split('.')[-1] if '.' in filename else ''
    key = f"document/{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4().hex}.{ext}"

    client.put_object(
        Bucket=cos_bucket,
        Body=content,
        Key=key,
        EnableMD5=False,
    )

    # 构建URL
    if cos_base_url and cos_base_url.startswith("http"):
        url = f"{cos_base_url.rstrip('/')}/{key}"
    else:
        url = f"https://{cos_bucket}.cos.{cos_region}.myqcloud.com/{key}"

    logger.info(f"[COS] 上传成功: {url}")
    return url


def _decode_base64_image(image_data: str) -> tuple[bytes, str]:
    """解码 base64 图片数据，返回 (bytes, extension)"""
    if image_data.startswith("data:"):
        # 提取类型和base64数据
        if "image/png" in image_data:
            ext = "png"
        elif "image/gif" in image_data:
            ext = "gif"
        elif "image/webp" in image_data:
            ext = "webp"
        else:
            ext = "jpg"
        base64_data = image_data.split(",", 1)[1] if "," in image_data else image_data
    else:
        ext = "jpg"
        base64_data = image_data

    image_bytes = base64.b64decode(base64_data)
    return image_bytes, ext


async def call_workflow_with_image(
    image_data: str,
    user_message: str = "请分析这张图片内容，帮助我生成劳动仲裁申请书",
    user_id: str | None = None,
) -> str:
    """调用工作流，上传图片进行分析"""
    client = _get_client()

    # 检测是 base64 还是 URL
    if image_data.startswith("http://") or image_data.startswith("https://"):
        image_url = image_data
    else:
        image_bytes, ext = _decode_base64_image(image_data)
        filename = f"image_{uuid.uuid4().hex[:8]}.{ext}"
        image_url = _upload_to_cos(image_bytes, filename)

    # 构建请求
    messages = [{"role": "user", "content": [{"type": "text", "text": user_message}]}]
    custom_vars = {"image_file": image_url}

    data, _ = await client.call(
        messages=messages,
        user_id=user_id or f"doc_img_{uuid.uuid4().hex[:8]}",
        custom_variables=custom_vars,
        experience=True,
        log_prefix="[工作流-图片]",
    )

    logger.info(f"[工作流-图片] image_file: {image_url}")

    return YuanqiAPIClient.parse_response_text(data)


async def call_workflow_with_document(
    file_content: bytes,
    filename: str,
    user_message: str = "请分析这份文档内容，帮助我生成劳动仲裁申请书",
    user_id: str | None = None,
) -> str:
    """调用工作流，上传文档进行分析"""
    client = _get_client()

    # 上传到COS
    upload_url = _upload_to_cos(file_content, filename)

    # 构建请求
    messages = [{"role": "user", "content": [{"type": "text", "text": user_message}]}]
    custom_vars = {"doc_file": upload_url}

    data, _ = await client.call(
        messages=messages,
        user_id=user_id or f"doc_file_{uuid.uuid4().hex[:8]}",
        custom_variables=custom_vars,
        experience=True,
        log_prefix="[工作流-文档]",
    )

    logger.info(f"[工作流-文档] 文件名: {filename}, doc_file: {upload_url}")

    return YuanqiAPIClient.parse_response_text(data)


async def call_workflow_chat(
    message: str,
    file_type: str = "image",
    file_content: Optional[str] = None,
    filename: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    user_id: str | None = None,
) -> str:
    """在工作流启动后进行对话"""
    client = _get_client()

    custom_vars: Dict[str, str] = {}

    # 处理文件/图片上传
    if file_content:
        if file_type == "image":
            if file_content.startswith("http://") or file_content.startswith("https://"):
                image_url = file_content
            else:
                image_bytes, ext = _decode_base64_image(file_content)
                image_url = _upload_to_cos(image_bytes, f"image_{uuid.uuid4().hex[:8]}.{ext}")
            custom_vars["image_file"] = image_url
            logger.info(f"[工作流聊天] 图片已上传: {image_url}")

        elif file_type == "doc":
            file_bytes = base64.b64decode(file_content) if isinstance(file_content, str) else file_content
            upload_url = _upload_to_cos(file_bytes, filename or "document.pdf")
            custom_vars["doc_file"] = upload_url
            logger.info(f"[工作流聊天] 文档已上传: {upload_url}")

    # 构建消息列表
    messages = []

    if history:
        for msg in history:
            msg_content = msg.get("content", "")
            if isinstance(msg_content, str) and msg_content.startswith("[图片]"):
                text = msg_content.replace("[图片] ", "")
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": [{"type": "text", "text": text}]
                })
            else:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": [{"type": "text", "text": str(msg_content)}]
                })

    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": message}]
    })

    # 构建请求
    data, _ = await client.call(
        messages=messages,
        user_id=user_id or f"doc_chat_{uuid.uuid4().hex[:8]}",
        custom_variables=custom_vars if custom_vars else None,
        experience=True,
        log_prefix="[工作流聊天]",
    )

    return YuanqiAPIClient.parse_response_text(data)
