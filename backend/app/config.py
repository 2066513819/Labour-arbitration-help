from __future__ import annotations

import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "劳动仲裁辅助系统"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # 本地调试可用 SQLite；生产建议改为 MySQL，例如：
    # mysql+pymysql://user:pass@127.0.0.1:3306/labor_arb?charset=utf8mb4
    database_url: str = "sqlite:///./labor_arb.db"

    # 得理法律 API（按需配置）
    deli_api_base: str = ""
    deli_api_key: str = ""

    # 元器智能体 API（智能对话）
    yuanqi_api_base: str = ""
    yuanqi_api_key: str = ""
    yuanqi_agent_id: str = ""

    # 文书起草智能体 API（图片上传）
    document_agent_id: str = ""
    document_agent_api_key: str = ""

    # 文书起草工作流 API
    workflow_agent_id: str = ""
    workflow_api_key: str = ""
    workflow_api_base: str = "https://yuanqi.tencent.com/openapi/v1"

    # 案例检索工作流 API
    case_search_agent_id: str = ""
    case_search_api_key: str = ""

    # 法条检索工作流 API
    law_search_agent_id: str = ""
    law_search_api_key: str = ""

    # OCR（可对接腾讯云/百度等；未配置时使用本地解析占位）
    ocr_api_base: str = ""
    ocr_api_key: str = ""

    # ── 开发环境验证码（留空自动生成随机码） ──
    dev_sms_code: str = ""

    # ── 邮箱验证码服务（SMTP，零资质门槛，推荐使用） ──
    # QQ邮箱 SMTP 获取授权码：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 生成授权码
    # 163邮箱 SMTP 获取授权码：163邮箱 → 设置 → POP3/SMTP/IMAP → 开启并获取授权码
    email_smtp_host: str = ""        # SMTP 服务器地址 (QQ: smtp.qq.com, 163: smtp.163.com)
    email_smtp_port: int = 465       # SMTP 端口 (SSL: 465, STARTTLS: 587)
    email_smtp_user: str = ""        # SMTP 登录账号（即邮箱地址）
    email_smtp_pass: str = ""        # SMTP 授权码（非邮箱密码！）
    email_sender_name: str = "劳动仲裁帮"  # 发件人显示名称

    # ── 腾讯云 SMS 配置（可选，需企业资质审核） ──
    sms_secret_id: str = ""
    sms_secret_key: str = ""
    sms_sdk_app_id: str = ""
    sms_sign_name: str = ""
    sms_template_id: str = ""
    sms_region: str = "ap-guangzhou"

    # CORS 允许的前端来源
    cors_origins: str = "http://localhost:5173"

    # 运行环境：development / production
    environment: str = "development"


settings = Settings()

# 安全启动检查
if not settings.secret_key or settings.secret_key == "change-me-in-production-use-openssl-rand-hex-32":
    if settings.environment == "production":
        raise RuntimeError(
            "生产环境必须设置强随机 SECRET_KEY。请运行: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    # 开发环境自动生成，保证 JWT 可用
    settings.secret_key = secrets.token_hex(32)
    print("[安全] 开发环境自动生成了随机 SECRET_KEY")

if settings.environment == "development" and not settings.dev_sms_code:
    settings.dev_sms_code = "".join(secrets.choice("0123456789") for _ in range(6))
    print(f"[开发] 短信验证码: {settings.dev_sms_code}（仅开发环境使用，生产环境走腾讯云 SMS）")
