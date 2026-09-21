"""邮箱验证码发送服务 — 通过 SMTP 发送，零资质门槛。

支持 QQ邮箱 / 163邮箱 / 企业邮箱等任意 SMTP 服务。
"""

from __future__ import annotations

import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from app.config import settings

logger = logging.getLogger(__name__)


def code_expires_at() -> datetime:
    """验证码过期时间：当前时间 + 5 分钟。"""
    return datetime.utcnow() + timedelta(minutes=5)


def send_verification_email(email: str, code: str) -> bool:
    """
    发送邮箱验证码。

    只要 SMTP 配置完整（host/user/pass），就直接真实发送邮件，
    不再依赖 ENVIRONMENT 变量。未配置 SMTP 时才回退到控制台打印。
    """
    smtp_configured = all([
        settings.email_smtp_host,
        settings.email_smtp_user,
        settings.email_smtp_pass,
    ])

    if smtp_configured:
        result = _send_via_smtp(email, code)
        # 开发环境额外打印一份到控制台，方便调试
        if settings.environment == "development":
            _print_to_console(email, code, result)
        return result
    else:
        _print_to_console(email, code, False)
        logger.warning("邮箱 SMTP 未配置，验证码仅打印到控制台")
        return True  # 未配置时不报错，方便本地开发


def _print_to_console(email: str, code: str, smtp_result: bool) -> None:
    """打印验证码到控制台。"""
    status = "✅ 邮件已发送" if smtp_result else "📋 仅控制台打印"
    print(f"\n{'='*50}")
    print(f"  [{status}] 邮箱 {email} 的验证码: {code}")
    print(f"  有效期: 5 分钟")
    print(f"{'='*50}\n")


def _send_via_dev(email: str, code: str) -> bool:
    """（保留兼容）开发环境：打印验证码到控制台。"""
    _print_to_console(email, code, False)
    return True


def _send_via_dev(email: str, code: str) -> bool:
    """开发环境：打印验证码到控制台。"""
    print(f"\n{'='*50}")
    print(f"  [开发] 邮箱 {email} 的验证码: {code}")
    print(f"  有效期: 5 分钟")
    print(f"{'='*50}\n")
    return True


def _send_via_smtp(email: str, code: str) -> bool:
    """通过 SMTP 真实发送验证码邮件。"""

    smtp_host = settings.email_smtp_host
    smtp_port = settings.email_smtp_port
    smtp_user = settings.email_smtp_user
    smtp_pass = settings.email_smtp_pass
    sender_name = settings.email_sender_name

    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.error(
            "邮箱 SMTP 未完整配置（EMAIL_SMTP_HOST / EMAIL_SMTP_USER / EMAIL_SMTP_PASS），"
            "邮件发送失败"
        )
        return False

    try:
        # 构建邮件
        msg = MIMEMultipart("alternative")
        # QQ邮箱对 From 头格式要求严格，必须用 formataddr + Header 编码中文
        msg["From"] = formataddr((Header(sender_name, "utf-8").encode(), smtp_user))
        msg["To"] = email
        msg["Subject"] = Header("[劳动仲裁帮] 邮箱验证码", "utf-8").encode()

        html_body = f"""\
<html>
<body style="font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; padding: 20px;">
  <div style="max-width: 480px; margin: 0 auto; background: #fff; border-radius: 8px; 
              box-shadow: 0 2px 12px rgba(0,0,0,0.08); padding: 32px;">
    <div style="text-align: center; margin-bottom: 24px;">
      <div style="font-size: 32px;">⚖️</div>
      <h2 style="color: #303133; margin: 12px 0 4px;">劳动仲裁帮</h2>
      <p style="color: #909399; font-size: 13px;">多类劳动者细分场景 · 务实可落地</p>
    </div>
    <div style="border-top: 1px solid #ebeef5; padding-top: 24px;">
      <p style="color: #606266; font-size: 14px;">您的验证码是：</p>
      <div style="background: #f0f5ff; border-radius: 6px; padding: 16px; 
                  text-align: center; margin: 16px 0;">
        <span style="font-size: 32px; font-weight: 700; color: #396af6; 
                     letter-spacing: 8px; font-family: monospace;">{code}</span>
      </div>
      <p style="color: #909399; font-size: 12px; margin-top: 16px;">
        验证码 5 分钟内有效，请勿泄露给他人。
      </p>
    </div>
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #ebeef5;
                text-align: center;">
      <p style="color: #c0c4cc; font-size: 11px;">
        此邮件由系统自动发送，请勿回复。
      </p>
    </div>
  </div>
</body>
</html>"""

        text_body = f"【劳动仲裁帮】您的邮箱验证码是：{code}，5 分钟内有效。请勿泄露给他人。"

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # 发送
        if smtp_port == 465:
            # SSL 方式（QQ邮箱用这个）
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            # STARTTLS 方式（端口 587）
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email, msg.as_string())
        server.quit()

        logger.info(f"验证码邮件发送成功: {email[:3]}***@{email.split('@')[-1]}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "邮箱 SMTP 登录失败，请检查 EMAIL_SMTP_USER / EMAIL_SMTP_PASS。"
            "\nQQ邮箱需使用授权码而非密码，获取方式：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 生成授权码"
        )
        return False
    except smtplib.SMTPConnectError:
        logger.error(f"无法连接 SMTP 服务器 {smtp_host}:{smtp_port}")
        return False
    except Exception as e:
        logger.error(f"邮件发送异常: {e}")
        return False


# ── 发送频率限制（内存级） ──
_send_records: dict[str, float] = {}


def check_rate_limit(key: str, interval_seconds: int = 60) -> bool:
    """检查发送频率限制。key 可以是手机号或邮箱。"""
    now = time.time()
    last = _send_records.get(key, 0)
    if now - last < interval_seconds:
        return False
    _send_records[key] = now
    return True
