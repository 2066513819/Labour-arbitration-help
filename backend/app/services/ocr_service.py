"""OCR：未配置外部服务时返回结构化占位，便于联调与演示。"""

import re
from typing import Any, Dict, List

from app.config import settings


async def run_ocr(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    if settings.ocr_api_base and settings.ocr_api_key:
        return await _remote_ocr(image_bytes, filename)
    return _mock_extract(image_bytes, filename)


async def _remote_ocr(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.ocr_api_base.rstrip('/')}/ocr",
            headers={"Authorization": f"Bearer {settings.ocr_api_key}"},
            files={"file": (filename, image_bytes)},
        )
        r.raise_for_status()
        data = r.json()
        return {"raw": data, "fields": _normalize_fields(str(data))}


def _mock_extract(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    size_kb = max(1, len(image_bytes) // 1024)
    phrases: List[str] = ["订单", "考勤", "工资", "罚款", "实习协议", "派遣"]
    return {
        "engine": "mock",
        "filename": filename,
        "image_size_kb": size_kb,
        "fields": {
            "推测金额": _guess_money(filename),
            "推测日期": "请核对图片中的日期",
            "关键短语": phrases[hash(filename) % 6],
        },
        "confidence": 0.72,
        "note": "未配置 OCR_API：当前为演示解析。配置 ocr_api_base + ocr_api_key 后走真实识别。",
    }


def _guess_money(name: str) -> str:
    m = re.search(r"(\d+\.?\d*)", name)
    return f"约 {m.group(1)} 元（文件名推断，需人工核对）" if m else "未识别到金额"


def _normalize_fields(text: str) -> Dict[str, Any]:
    return {"summary": text[:2000]}
