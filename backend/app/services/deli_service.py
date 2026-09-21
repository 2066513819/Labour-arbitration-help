"""得理 API：生成仲裁文书骨架 + 法律依据占位。"""

from typing import Any, Dict, List, Optional

import httpx

from app.config import settings


async def generate_arbitration_document(
    *,
    laborer_type: str,
    scenario_id: str,
    scenario_title: str,
    law_refs: List[str],
    user_phone: str,
    facts: Optional[str],
    ocr_snippets: List[Dict[str, Any]],
) -> str:
    payload = {
        "laborer_type": laborer_type,
        "scenario_id": scenario_id,
        "scenario_title": scenario_title,
        "law_refs": law_refs,
        "applicant_phone": user_phone[:3] + "****" + user_phone[-4:],
        "facts": facts or "（事实与理由请根据证据补充）",
        "ocr_snippets": ocr_snippets,
    }
    if settings.deli_api_base and settings.deli_api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{settings.deli_api_base.rstrip('/')}/document/arbitration",
                headers={"Authorization": f"Bearer {settings.deli_api_key}"},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("content") or data.get("document") or str(data)
    return _local_template(payload)


def _local_template(payload: Dict[str, Any]) -> str:
    phone = payload["applicant_phone"]
    title = payload["scenario_title"]
    laws = "、".join(payload["law_refs"])
    facts = payload["facts"]
    return f"""劳动人事争议仲裁申请书（示例稿）

申请人：________（姓名）  联系电话：{phone}
被申请人：________（单位名称）  住所地：________

案由：{title}

仲裁请求：
1. 请求依法裁决被申请人承担相应法律责任（请按实际诉求修改具体金额与事项）；
2. 本案仲裁费用由被申请人承担（如适用）。

事实与理由：
{facts}

法律依据（系统提示，不构成正式法律意见）：{laws}

此致
________劳动人事争议仲裁委员会

申请人：________（签名）
____年____月____日

附：证据目录（上传材料自动生成编号后打印）
"""
