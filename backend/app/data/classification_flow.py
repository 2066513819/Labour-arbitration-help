"""其他/不确定：引导式判定（最多 5 步）"""

from typing import Dict, Tuple

FLOW_STEPS = [
    {
        "id": "q1",
        "question": "是否签订书面劳动合同？",
        "options": [
            {"value": "yes_contract", "label": "已签订"},
            {"value": "no_contract", "label": "未签订"},
            {"value": "unclear_contract", "label": "不清楚/部分签订"},
        ],
    },
    {
        "id": "q2",
        "question": "用人单位是否为您缴纳社保？",
        "options": [
            {"value": "si_yes", "label": "有缴纳"},
            {"value": "si_no", "label": "未缴纳"},
            {"value": "si_partial", "label": "部分缴纳/委托第三方"},
        ],
    },
    {
        "id": "q3",
        "question": "您的主要工作模式是？",
        "options": [
            {"value": "mode_site", "label": "固定坐班/工厂产线"},
            {"value": "mode_platform", "label": "平台接单（外卖/快递/网约车等）"},
            {"value": "mode_intern", "label": "实习/见习"},
            {"value": "mode_dispatch", "label": "劳务派遣至用工单位"},
        ],
    },
    {
        "id": "q4",
        "question": "纠纷是否涉及实习协议或学校实习？",
        "options": [
            {"value": "intern_yes", "label": "是"},
            {"value": "intern_no", "label": "否"},
        ],
    },
    {
        "id": "q5",
        "question": "您是否主要由劳务派遣公司管理并发放工资？",
        "options": [
            {"value": "disp_yes", "label": "是"},
            {"value": "disp_no", "label": "否"},
        ],
    },
]


def infer_laborer_type(answers: Dict[str, str]) -> Tuple[str, str]:
    """根据答案推断劳动者类型与理由说明。"""
    mode = answers.get("q3", "")
    if answers.get("q4") == "intern_yes":
        return "intern", "您选择了实习相关情形，优先匹配实习生场景。"
    if mode == "mode_platform":
        return "platform", "工作模式为平台接单，匹配新就业形态从业者场景。"
    if mode == "mode_dispatch" or answers.get("q5") == "disp_yes":
        return "dispatch", "存在劳务派遣或派遣管理特征，匹配劳务派遣场景。"
    if mode == "mode_intern":
        return "intern", "工作模式为实习/见习，匹配实习生场景。"
    if mode == "mode_site":
        return "regular", "工作模式为固定坐班/工厂产线，匹配正式员工场景。"
    return "regular", "综合判断更接近正式员工常见形态，可按正式员工场景处理（可再调整）。"
