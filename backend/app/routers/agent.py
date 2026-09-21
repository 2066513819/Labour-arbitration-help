from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.case_record import AgentMessage
from app.schemas.agent import AgentAskRequest, AgentAskResponse
from app.services.yuanqi_service import ask_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class SidebarChatRequest(BaseModel):
    question: str
    history: list[dict] | None = None


@router.post("/ask", response_model=AgentAskResponse)
async def ask(
    body: AgentAskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lt = body.laborer_type or user.laborer_type
    if not lt:
        raise HTTPException(400, "请先选择劳动者类型")
    
    print(f"[后端Router] history长度: {len(body.history) if body.history else 0}")
    
    reply, latency_ms = await ask_agent(
        question=body.question, 
        laborer_type=lt,
        history=body.history,
        user_id=str(user.id),
    )
    db.add(AgentMessage(user_id=user.id, role="user", content=body.question))
    assistant = AgentMessage(
        user_id=user.id,
        role="assistant",
        content=reply.interpretation[:2000],
        structured_reply=reply.model_dump() if hasattr(reply, "model_dump") else reply.dict(),
        ui_meta={"layout": "restate-law-interpret-actions", "accent": "gradient"},
        latency_ms=latency_ms,
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return AgentAskResponse(
        message_id=assistant.id,
        reply=reply,
        ui_meta={"transition": "fade", "duration_ms": 280},
        latency_ms=latency_ms,
    )


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(AgentMessage)
        .filter(AgentMessage.user_id == user.id)
        .order_by(AgentMessage.id.desc())
        .limit(50)
        .all()
    )
    out = []
    for r in rows:
        if r.role == "assistant" and r.structured_reply:
            out.append(
                {
                    "id": r.id,
                    "created_at": r.created_at.isoformat(),
                    "structured_reply": r.structured_reply,
                    "latency_ms": r.latency_ms,
                }
            )
    return {"items": out}


@router.delete("/history/{message_id}")
def delete_history(message_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(AgentMessage, message_id)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "记录不存在")
    db.delete(r)
    db.commit()
    return {"ok": True}


# ── 侧边栏知识库问答（调用用户指定的知识库应用）──
import httpx
import json as _json
import uuid
import os

YUANQI_SIDEBAR_API_KEY = os.getenv("YUANQI_SIDEBAR_API_KEY", "")
YUANQI_SIDEBAR_APP_ID = os.getenv("YUANQI_SIDEBAR_APP_ID", "")
YUANQI_SIDEBAR_API_URL = os.getenv(
    "YUANQI_SIDEBAR_API_URL",
    "https://yuanqi.tencent.com/openapi/v1/agent/chat/completions",
)


@router.post("/sidebar-chat")
async def sidebar_chat(
    body: SidebarChatRequest,
    user: User = Depends(get_current_user),
):
    """
    侧边栏智能助手：调用知识库问答应用
    前端直接调用此接口，避免跨域和 API Key 暴露
    """
    messages = []

    # 构建历史消息（确保第一条是 user，且 user/assistant 交替）
    if body.history:
        for msg in body.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content.strip():
                messages.append({
                    "role": role,
                    "content": [{"type": "text", "text": content}],
                })

    # 如果历史为空或第一条不是 user，清空历史（API 要求第一条必须是 user）
    if messages and messages[0]["role"] != "user":
        messages = []

    # 确保 user/assistant 交替，去除连续相同角色的消息
    filtered = []
    for m in messages:
        if filtered and filtered[-1]["role"] == m["role"]:
            # 连续相同角色，跳过或合并（这里跳过旧的）
            filtered[-1] = m
        else:
            filtered.append(m)
    messages = filtered

    # 添加当前问题
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": body.question}],
    })

    body_data = {
        "assistant_id": YUANQI_SIDEBAR_APP_ID,
        "user_id": f"sidebar_{user.id}",
        "stream": False,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {YUANQI_SIDEBAR_API_KEY}",
        "Content-Type": "application/json",
        "X-Source": "openapi",
    }

    print(f"[侧边栏] 请求URL: {YUANQI_SIDEBAR_API_URL}")
    print(f"[侧边栏] assistant_id={YUANQI_SIDEBAR_APP_ID}")
    print(f"[侧边栏] 用户问题: {body.question[:80]}...")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
            r = await client.post(YUANQI_SIDEBAR_API_URL, headers=headers, json=body_data)

            print(f"[侧边栏] 响应状态码: {r.status_code}")

            # 400 可能是 content 格式问题，降级为字符串 content 重试
            if r.status_code == 400:
                print(f"[侧边栏] 400 响应体: {r.text[:500]}")
                print(f"[侧边栏] 尝试降级为字符串 content 格式")
                try_body = dict(body_data)
                try_body["messages"] = [
                    {
                        "role": m.get("role", "user"),
                        "content": (m.get("content") or [{"type": "text", "text": ""}])[0].get("text", ""),
                    }
                    for m in messages
                ]
                r = await client.post(YUANQI_SIDEBAR_API_URL, headers=headers, json=try_body)
                print(f"[侧边栏] 重试后状态码: {r.status_code}")

            if r.status_code != 200:
                print(f"[侧边栏] API 调用失败, 状态码={r.status_code}")
                print(f"[侧边栏] 错误响应体: {r.text[:500]}")
                raise Exception(f"status={r.status_code}")
            data = r.json()
            print(f"[侧边栏] 成功响应: {_json.dumps(data, ensure_ascii=False)[:500]}")

        # 解析响应
        reply_text = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            if isinstance(content, list):
                reply_text = "".join(
                    item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"
                )
            elif isinstance(content, str):
                reply_text = content

        if not reply_text:
            if data.get("reply"):
                reply_text = data["reply"]
            elif isinstance(data.get("data"), dict):
                reply_text = data["data"].get("reply", "") or data["data"].get("answer", "")
            elif data.get("answer"):
                reply_text = data["answer"]

        if reply_text:
            return {"reply": reply_text}
        else:
            print(f"[侧边栏] 无法提取回复，原始: {_json.dumps(data, ensure_ascii=False)[:300]}")
            raise Exception("no_reply_content")

    except Exception as e:
        print(f"[侧边栏] 知识库调用异常: {e}")
        return {"reply": f"⚠️ 智能助手请求失败：{str(e)[:200]}，请检查 API Key 和 App ID 配置是否正确。"}
