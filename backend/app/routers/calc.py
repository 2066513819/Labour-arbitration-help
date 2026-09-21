import datetime
import re
from typing import Optional, List

from pydantic import BaseModel, Field

from fastapi import APIRouter

router = APIRouter(prefix="/calc", tags=["calc"])


class ModifyItem(BaseModel):
    modify_items: str
    modify: str


class CalcRequest(BaseModel):
    laborer_type: str
    mode: str = Field(..., description="severance | overtime | unpaid_wage | fine_dispute")
    base_amount: Optional[float] = None
    months: Optional[float] = None
    hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    fine_amount: Optional[float] = None
    # 新增：工龄计算相关字段
    entry_date: Optional[str] = None  # 入职日期 YYYY-MM-DD
    last_working_day: Optional[str] = None  # 离职日期 YYYY-MM-DD
    salary: Optional[float] = None  # 月薪
    termination_reason: Optional[str] = None  # 离职原因
    modify_result: Optional[List[ModifyItem]] = None  # 纠错列表


def clean_number(value):
    """清洗数字，提取数字和小数点"""
    if not value:
        return 0.0
    try:
        num_str = ''.join(c for c in str(value) if c.isdigit() or c == '.')
        return float(num_str) if num_str else 0.0
    except:
        return 0.0


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    # 清洗日期格式
    clean_d = str(date_str).replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').replace('.', '-')
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(clean_d.strip(), fmt)
        except:
            continue
    return None


def calculate_severance(entry_date: str, last_working_day: str, salary: float, termination_reason: str,
                        modify_result: Optional[List[dict]] = None) -> dict:
    """
    计算经济补偿金/违法解除赔偿金
    
    参数:
        entry_date: 入职日期
        last_working_day: 离职日期  
        salary: 月薪
        termination_reason: 离职原因
        modify_result: 纠错列表，用于覆盖参数
    
    返回:
        包含 total_money, n_value, work_period, legal_type 的字典
    """
    # 处理纠错列表：动态覆盖对应变量
    if modify_result and isinstance(modify_result, list):
        for item in modify_result:
            items_str = item.get('modify_items', '')
            new_val = item.get('modify', '')
            
            if not new_val:
                continue
                
            if "离职日期" in items_str or "last_working_day" in items_str:
                last_working_day = new_val
            elif "入职日期" in items_str or "entry_date" in items_str:
                entry_date = new_val
            elif "月薪" in items_str or "salary" in items_str:
                try:
                    salary = clean_number(new_val)
                except:
                    pass
            elif "原因" in items_str or "termination_reason" in items_str:
                termination_reason = new_val

    # 解析日期
    start = parse_date(entry_date)
    end = parse_date(last_working_day)
    salary_val = clean_number(salary)
    reason = str(termination_reason) if termination_reason else ""

    if not start or not end:
        return {
            "total_money": "0.00",
            "n_value": "0",
            "work_period": "无法计算",
            "legal_type": "日期解析失败",
            "error": True
        }

    # 计算工龄
    diff = end - start
    total_days = diff.days
    
    if total_days < 0:
        return {
            "total_money": "0.00",
            "n_value": "0",
            "work_period": "无法计算",
            "legal_type": "离职时间早于入职时间",
            "error": True
        }

    # 计算总月份数（按30.44天/月计算）
    total_months = total_days / 30.44
    years = int(total_months // 12)
    remained_months = total_months % 12

    # 确定 N 值
    n_value = float(years)
    if remained_months >= 6:
        n_value += 1.0
        display_months = int(remained_months)
    elif remained_months > 0:
        n_value += 0.5
        display_months = int(remained_months)
    else:
        display_months = 0

    # 判定赔偿倍数
    illegal_keywords = ["违法", "裁员", "辞退", "解雇", "开除", "非法"]
    if any(k in reason for k in illegal_keywords):
        multiplier = 2
        legal_type = "违法解除赔偿金 (2N)"
    else:
        multiplier = 1
        legal_type = "经济补偿金 (N)"

    # 计算总金额
    total_money = n_value * multiplier * salary_val

    return {
        "total_money": f"{total_money:.2f}",
        "n_value": str(n_value),
        "work_period": f"{years}年{display_months}个月",
        "legal_type": legal_type,
        "multiplier": multiplier,
        "years_raw": years,
        "months_raw": int(remained_months),
        "days_total": total_days,
        "error": False
    }


@router.post("/estimate")
def estimate(body: CalcRequest):
    """仲裁金额估算主接口"""
    result = 0.0
    note = ""
    detail_result = None
    
    # 工龄计算模式（使用日期）
    if body.mode == "severance":
        if body.entry_date and body.last_working_day and body.salary:
            # 使用精确日期计算
            detail_result = calculate_severance(
                entry_date=body.entry_date,
                last_working_day=body.last_working_day,
                salary=body.salary,
                termination_reason=body.termination_reason or "",
                modify_result=[item.model_dump() for item in body.modify_result] if body.modify_result else None
            )
            result = float(detail_result["total_money"])
            note = f"{detail_result['legal_type']} | 工龄{detail_result['work_period']} | N={detail_result['n_value']}"
        elif body.base_amount and body.months:
            # 兼容旧版简单计算
            result = round(body.base_amount * body.months, 2)
            note = "经济补偿常用算法：月工资 × 工作年限（≤6个月按0.5年计等细则请结合实际）"
        else:
            note = "请输入：入职日期、离职日期、月薪（精确计算）或 月工资和年限（简易计算）"
    
    elif body.mode == "overtime" and body.hours and body.hourly_rate:
        result = round(body.hours * body.hourly_rate * 1.5, 2)
        note = "延时加班示例系数1.5，具体以制度与证据为准"
    
    elif body.mode == "unpaid_wage" and body.base_amount:
        result = round(body.base_amount, 2)
        note = "未发工资以应发金额合计为准"
    
    elif body.mode == "fine_dispute" and body.fine_amount:
        result = round(body.fine_amount, 2)
        note = "争议罚款金额核对：结合规则公示与扣款凭证"
    
    else:
        note = "参数不足，请补齐输入项"

    response = {
        "estimated_amount": result,
        "note": note,
        "laborer_type": body.laborer_type,
        "ui_meta": {"result_animation": "count-up", "duration_ms": 280},
    }
    
    # 如果有详细计算结果，附加到响应中
    if detail_result:
        response["detail"] = detail_result
    
    return response
