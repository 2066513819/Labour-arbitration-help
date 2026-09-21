"""短信发送服务 — 支持腾讯云 SMS（生产）和开发模式（控制台打印）。"""

from __future__ import annotations

import json
import logging
import secrets
import time
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


def generate_code() -> str:
    """生成 6 位数字验证码。"""
    return "".join(secrets.choice("0123456789") for _ in range(6))


def send_verification_code(phone: str, code: str) -> bool:
    """
    发送短信验证码。

    生产环境调用腾讯云 SMS API，开发环境打印到控制台。
    返回 True/False 表示是否发送成功。
    """
    if settings.environment == "production":
        return _send_via_tencent(phone, code)
    else:
        return _send_via_dev(phone, code)


def code_expires_at() -> datetime:
    """验证码过期时间：当前时间 + 5 分钟。"""
    return datetime.utcnow() + timedelta(minutes=5)


def _send_via_dev(phone: str, code: str) -> bool:
    """开发环境：打印验证码到控制台。"""
    print(f"\n{'='*50}")
    print(f"  [开发] 手机号 {phone} 的验证码: {code}")
    print(f"  有效期: 5 分钟")
    print(f"{'='*50}\n")
    return True


def _send_via_tencent(phone: str, code: str) -> bool:
    """
    通过腾讯云 SMS 发送短信。

    需要提前在腾讯云控制台：
    1. 开通短信服务 (https://console.cloud.tencent.com/smsv2)
    2. 创建短信签名（如"劳动仲裁助手"）
    3. 创建短信模板（如"您的验证码为{1}，{2}分钟内有效"）
    4. 获取 SDK AppID
    """
    sdk_app_id = settings.sms_sdk_app_id
    template_id = settings.sms_template_id
    sign_name = settings.sms_sign_name

    if not all([sdk_app_id, template_id, sign_name]):
        logger.error("腾讯云 SMS 未完整配置（SDK_APP_ID / TEMPLATE_ID / SIGN_NAME），短信发送失败")
        return False

    try:
        from tencentcloud.common import credential
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
            TencentCloudSDKException,
        )
        from tencentcloud.sms.v20210111 import models, sms_client

        cred = credential.Credential(
            settings.sms_secret_id or settings.sms_secret_id,
            settings.sms_secret_key or settings.sms_secret_key,
        )
        client = sms_client.SmsClient(cred, settings.sms_region or "ap-guangzhou")

        req = models.SendSmsRequest()
        req.SmsSdkAppId = sdk_app_id
        req.SignName = sign_name
        req.TemplateId = template_id
        req.TemplateParamSet = [code, "5"]  # {1}=验证码, {2}=5分钟
        req.PhoneNumberSet = [f"+86{phone}"]  # 默认中国区号

        resp = client.SendSms(req)
        result = json.loads(resp.to_json_string())
        send_status = result.get("SendStatusSet", [{}])[0]

        if send_status.get("Code") == "Ok":
            logger.info(f"短信发送成功: phone={phone[:3]}****{phone[-4:]}, "
                        f"requestId={result.get('RequestId')}")
            return True
        else:
            logger.error(f"短信发送失败: {send_status.get('Message', '未知错误')}")
            return False

    except TencentCloudSDKException as e:
        logger.error(f"腾讯云 SMS SDK 异常: {e}")
        return False
    except ImportError:
        logger.error(
            "未安装腾讯云 SMS SDK，请执行: pip install tencentcloud-sdk-python"
        )
        return False
    except Exception as e:
        logger.error(f"短信发送未知异常: {e}")
        return False


# ── 发送频率限制（内存级） ──
_send_records: dict[str, float] = {}  # phone -> last_send_timestamp


def check_rate_limit(phone: str, interval_seconds: int = 60) -> bool:
    """
    检查发送频率限制。

    Args:
        phone: 手机号
        interval_seconds: 同一号码两次发送的最小间隔（秒），默认 60 秒

    Returns:
        True = 允许发送, False = 过于频繁
    """
    now = time.time()
    last = _send_records.get(phone, 0)
    if now - last < interval_seconds:
        return False
    _send_records[phone] = now
    return True
