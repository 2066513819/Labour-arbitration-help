from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.verification_code import VerificationCode
from app.schemas.auth import (
    EmailLoginRequest,
    LoginRequest,
    SendCodeRequest,
    SendEmailCodeRequest,
    SetLaborerTypeRequest,
    TokenResponse,
)
from app.security import create_access_token, hash_password
from app.services.sms_service import (
    check_rate_limit as sms_rate_limit,
    code_expires_at,
    generate_code,
    send_verification_code,
)
from app.services.email_service import (
    check_rate_limit as email_rate_limit,
    code_expires_at as email_code_expires_at,
    send_verification_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DAILY_SEND_LIMIT = 10

# ──────────────────────────── 手机短信（开发模式） ────────────────────────────


@router.post("/send-code")
def send_code(body: SendCodeRequest, request: Request, db: Session = Depends(get_db)):
    """发送短信验证码（开发环境打印验证码到控制台）。"""
    phone = body.phone

    if not sms_rate_limit(phone, interval_seconds=60):
        raise HTTPException(status_code=429, detail="验证码发送过于频繁，请 60 秒后再试")

    code = generate_code()
    send_verification_code(phone, code)

    record = VerificationCode(
        phone=phone,
        code=code,
        expires_at=code_expires_at(),
        ip_address=request.client.host if request.client else "",
    )
    db.add(record)
    db.commit()

    return {
        "ok": True,
        "message": "验证码已发送，5 分钟内有效",
        "ui_meta": {"animation": "toast", "duration_ms": 250},
    }


@router.post("/sms-login", response_model=TokenResponse)
def sms_login(body: LoginRequest, db: Session = Depends(get_db)):
    """短信验证码登录。"""
    return _verify_and_login(db, body.phone, body.code.strip())


# ──────────────────────────── 邮箱验证码（真实发送） ────────────────────────────


@router.post("/send-email-code")
def send_email_code(body: SendEmailCodeRequest, request: Request, db: Session = Depends(get_db)):
    """发送邮箱验证码（真实发邮件，零资质门槛）。"""

    email = body.email.strip()

    # 1️⃣ 频率限制
    if not email_rate_limit(email, interval_seconds=60):
        raise HTTPException(status_code=429, detail="验证码发送过于频繁，请 60 秒后再试")

    # 2️⃣ 每日上限
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(VerificationCode).where(
        VerificationCode.phone == email,
        VerificationCode.created_at >= today_start,
    ).count()
    if today_count >= DAILY_SEND_LIMIT:
        raise HTTPException(status_code=429, detail="今日发送次数已达上限，请明天再试")

    # 3️⃣ 生成验证码
    code = generate_code()

    # 4️⃣ 发送邮件
    ok = send_verification_email(email, code)
    if not ok:
        raise HTTPException(status_code=500, detail="邮件发送失败，请确认邮箱 SMTP 配置正确")

    # 5️⃣ 存入数据库（复用 phone 字段存邮箱）
    client_ip = request.client.host if request.client else ""
    record = VerificationCode(
        phone=email,  # 字段名叫 phone，但可以存邮箱地址
        code=code,
        expires_at=email_code_expires_at(),
        ip_address=client_ip,
    )
    db.add(record)
    db.commit()

    return {
        "ok": True,
        "message": "验证码已发送到您的邮箱，5 分钟内有效",
        "ui_meta": {"animation": "toast", "duration_ms": 250},
    }


@router.post("/email-login", response_model=TokenResponse)
def email_login(body: EmailLoginRequest, db: Session = Depends(get_db)):
    """邮箱验证码登录。"""
    email = body.email.strip()
    return _verify_and_login(db, email, body.code.strip(), is_email=True)


# ──────────────────────────── 通用校验与登录逻辑 ────────────────────────────


def _verify_and_login(db: Session, identifier: str, input_code: str, is_email: bool = False):
    """校验验证码并完成登录，identifier 可以是手机号或邮箱。"""

    now = datetime.utcnow()
    record = db.execute(
        select(VerificationCode)
        .where(
            VerificationCode.phone == identifier,
            VerificationCode.used == False,
            VerificationCode.expires_at > now,
        )
        .order_by(VerificationCode.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=400, detail="验证码不存在或已过期，请重新获取")

    if record.code != input_code:
        raise HTTPException(status_code=400, detail="验证码错误")

    record.used = True
    db.add(record)
    db.commit()

    if is_email:
        # 邮箱登录：使用邮箱作为唯一标识
        user = db.execute(
            select(User).where(User.phone == identifier)
        ).scalar_one_or_none()
        if not user:
            user = User(phone=identifier, hashed_password=hash_password(identifier + ":email"))
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        user = db.execute(
            select(User).where(User.phone == identifier)
        ).scalar_one_or_none()
        if not user:
            user = User(phone=identifier, hashed_password=hash_password(identifier + ":sms"))
            db.add(user)
            db.commit()
            db.refresh(user)

    token = create_access_token(user.id, {"phone": user.phone})
    return TokenResponse(
        access_token=token,
        ui_meta={"transition": "fade", "duration_ms": 280, "next": "laborer_type_modal"},
    )


# ──────────────────────────── 用户信息 ────────────────────────────


@router.put("/me/laborer-type", response_model=dict)
def set_laborer_type(
    body: SetLaborerTypeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.laborer_type = body.laborer_type.value
    user.inferred_from_flow = body.inferred_from_flow
    db.add(user)
    db.commit()
    return {
        "ok": True,
        "laborer_type": user.laborer_type,
        "ui_meta": {"animation": "highlight", "duration_ms": 260},
    }


@router.get("/me", response_model=dict)
def me(user: User = Depends(get_current_user)):
    identifier = user.phone or ""
    if "@" in identifier:
        # 邮箱：只显示用户名前3位
        parts = identifier.split("@")
        shown = parts[0][:3] + "***@" + parts[-1] if len(parts[0]) > 3 else "***@" + parts[-1]
    else:
        # 手机号
        shown = identifier[:3] + "****" + identifier[-4:]
    return {
        "id": user.id,
        "phone": shown,
        "account": identifier,
        "laborer_type": user.laborer_type,
        "inferred_from_flow": user.inferred_from_flow,
    }
