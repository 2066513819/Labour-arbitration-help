"""按劳动者类型拆分的高频仲裁场景（务实、非泛化）"""

from typing import Any, Dict, List

from app.schemas.labor import LaborerType

SCENARIOS: Dict[str, List[Dict[str, Any]]] = {
    LaborerType.REGULAR.value: [
        {
            "id": "regular_no_contract",
            "title": "未签劳动合同双倍工资",
            "evidence_hint": ["工资流水/银行记录", "考勤记录", "工作证/工牌", "同事证言", "工作群聊天记录"],
            "law_refs": ["《劳动合同法》第十条、第八十二条"],
        },
        {
            "id": "regular_illegal_dismissal",
            "title": "违法解除劳动合同",
            "evidence_hint": ["解除通知书（如有）", "劳动合同", "工资流水", "工作年限证明"],
            "law_refs": ["《劳动合同法》第四十七条、第四十八条、第八十七条"],
        },
        {
            "id": "regular_wage_arrears",
            "title": "拖欠工资/加班费",
            "evidence_hint": ["工资条/银行流水", "考勤记录", "加班申请/审批记录", "与公司的沟通记录"],
            "law_refs": ["《劳动合同法》第三十条、第八十五条", "《工资支付暂行规定》"],
        },
        {
            "id": "regular_social_insurance",
            "title": "未缴社保/公积金",
            "evidence_hint": ["劳动合同", "工资流水", "社保查询记录", "公积金账户截图"],
            "law_refs": ["《社会保险法》", "《住房公积金管理条例》"],
        },
        {
            "id": "regular_severance",
            "title": "经济补偿金/赔偿金",
            "evidence_hint": ["解除/终止劳动关系证明", "工资流水（12个月）", "离职前12个月考勤"],
            "law_refs": ["《劳动合同法》第四十六条、第四十七条"],
        },
        {
            "id": "regular_overtime",
            "title": "加班费计算争议",
            "evidence_hint": ["考勤记录/钉钉打卡", "加班审批记录", "工资条", "企业加班制度文件"],
            "law_refs": ["《劳动法》第四十四条", "《劳动合同法》第三十一条"],
        },
        {
            "id": "regular_annual_leave",
            "title": "年休假未休补偿",
            "evidence_hint": ["考勤记录", "请假系统截图", "工资发放记录"],
            "law_refs": ["《职工带薪年休假条例》", "《企业职工带薪年休假实施办法》"],
        },
        {
            "id": "regular_contract_change",
            "title": "劳动合同变更/调岗争议",
            "evidence_hint": ["原劳动合同", "调岗/变更通知", "异议记录", "新岗位说明"],
            "law_refs": ["《劳动合同法》第三十五条"],
        },
    ],
    LaborerType.DISPATCH.value: [
        {
            "id": "dispatch_equal_pay",
            "title": "同工同酬争议",
            "evidence_hint": ["劳务派遣合同", "工资条/银行流水", "同岗位正式员工待遇对比材料"],
            "law_refs": ["《劳动合同法》第六十三条", "《劳务派遣暂行规定》"],
        },
        {
            "id": "dispatch_social_insurance",
            "title": "社保缴纳与责任划分",
            "evidence_hint": ["派遣协议", "社保缴费记录", "与用工单位/派遣公司沟通记录"],
            "law_refs": ["《劳务派遣暂行规定》第八条、第十八条"],
        },
        {
            "id": "dispatch_contract_dispute",
            "title": "劳务派遣合同纠纷",
            "evidence_hint": ["派遣合同", "岗位说明", "变更通知"],
            "law_refs": ["《劳动合同法》第五章第二节"],
        },
        {
            "id": "dispatch_severance",
            "title": "离职补偿/违法解除",
            "evidence_hint": ["解除通知", "考勤", "工资流水"],
            "law_refs": ["《劳动合同法》第四十六条、第四十七条、第八十七条"],
        },
        {
            "id": "dispatch_position_change",
            "title": "岗位调整纠纷",
            "evidence_hint": ["原岗位约定", "调岗书面材料", "异议记录"],
            "law_refs": ["《劳动合同法》第三十五条"],
        },
    ],
    LaborerType.INTERN.value: [
        {
            "id": "intern_pay_arrears",
            "title": "实习报酬拖欠",
            "evidence_hint": ["实习协议", "考勤/打卡", "约定报酬的沟通记录"],
            "law_refs": ["《民法典》合同编相关条款", "实习协议约定"],
        },
        {
            "id": "intern_agreement_breach",
            "title": "实习协议违约",
            "evidence_hint": ["实习协议全文", "违约事实材料"],
            "law_refs": ["《民法典》第五百七十七条"],
        },
        {
            "id": "intern_injury",
            "title": "实习期间人身伤害赔偿",
            "evidence_hint": ["事故说明", "医疗票据", "现场证明人/监控说明"],
            "law_refs": ["《民法典》侵权责任编"],
        },
        {
            "id": "intern_certificate",
            "title": "实习证明出具纠纷",
            "evidence_hint": ["要求出具证明的记录", "学校要求说明"],
            "law_refs": ["诚实信用原则与协议约定"],
        },
    ],
    LaborerType.PLATFORM.value: [
        {
            "id": "platform_overtime",
            "title": "加班工资/在线时长争议",
            "evidence_hint": ["平台订单截图", "在线时长记录", "站长/客服沟通记录"],
            "law_refs": ["劳动关系认定相关裁判规则", "工时制度规定"],
        },
        {
            "id": "platform_fine",
            "title": "订单罚款/扣款纠纷",
            "evidence_hint": ["罚款规则截图", "扣款流水", "申诉记录"],
            "law_refs": ["《新就业形态劳动者权益保障办法》及平台规则合法性审查"],
        },
        {
            "id": "platform_relation",
            "title": "劳动关系/劳务关系判定",
            "evidence_hint": ["接单记录", "管理规则", "工服工牌", "考勤"],
            "law_refs": ["原劳动和社会保障部相关确认劳动关系规定"],
        },
        {
            "id": "platform_injury",
            "title": "工伤认定协助",
            "evidence_hint": ["事故经过说明", "接单记录", "医疗材料"],
            "law_refs": ["《工伤保险条例》"],
        },
        {
            "id": "platform_no_contract",
            "title": "未签书面合同补偿",
            "evidence_hint": ["工资发放记录", "管理证据", "入职时间证明"],
            "law_refs": ["《劳动合同法》第十条、第八十二条"],
        },
    ],
    LaborerType.COURIER.value: [
        {
            "id": "courier_overtime",
            "title": "配送时长与报酬",
            "evidence_hint": ["配送订单截图", "站点排班", "工资条"],
            "law_refs": ["劳动关系认定", "最低工资与加班规则"],
        },
        {
            "id": "courier_fine",
            "title": "违规罚款争议",
            "evidence_hint": ["平台处罚通知", "申诉记录"],
            "law_refs": ["平台规则合法性", "扣款合理性"],
        },
        {
            "id": "courier_injury",
            "title": "配送途中事故",
            "evidence_hint": ["事故认定", "医疗票据", "订单时间线"],
            "law_refs": ["工伤/侵权责任"],
        },
    ],
    LaborerType.OTHER_UNCERTAIN.value: [
        {
            "id": "other_help_me",
            "title": "综合：帮我梳理维权路径",
            "evidence_hint": ["任何现有材料：合同、聊天、考勤、工资记录"],
            "law_refs": ["依最终判定类型匹配"],
        },
    ],
}


def get_scenarios(laborer_type: str) -> List[Dict[str, Any]]:
    return SCENARIOS.get(laborer_type, SCENARIOS[LaborerType.OTHER_UNCERTAIN.value])


FAQ_BY_TYPE: Dict[str, List[Dict[str, str]]] = {
    LaborerType.REGULAR.value: [
        {"q": "公司不签合同怎么办？", "a": "收集工资流水、考勤、工作证等证明劳动关系，可主张双倍工资差额。"},
        {"q": "被辞退能拿多少钱？", "a": "合法解除最少N（每满一年一个月工资），违法解除为2N，具体需计算工龄和平均工资。"},
        {"q": "社保未缴怎么维权？", "a": "先向社保部门投诉要求补缴，无法补缴时可主张赔偿损失，保留工资流水等证据。"},
        {"q": "加班费如何计算？", "a": "工作日1.5倍、休息日2倍、法定假日3倍基数工资，需保留考勤和加班审批记录。"},
    ],
    LaborerType.DISPATCH.value: [
        {"q": "如何证明与用工单位存在实际用工关系？", "a": "保留工牌、门禁、排班、工作邮件、与现场主管的沟通记录等。"},
        {"q": "社保应由谁缴纳？", "a": "依法一般由劳务派遣单位参保；具体可结合协议与地方细则。"},
    ],
    LaborerType.INTERN.value: [
        {"q": "实习生没有报酬可以维权吗？", "a": "若协议明确约定报酬，可依协议主张；需保存协议与履行证据。"},
        {"q": "实习是否一定不构成劳动关系？", "a": "需结合从属性、报酬、期限等综合判断，个案差异大。"},
    ],
    LaborerType.PLATFORM.value: [
        {"q": "平台未缴社保怎么办？", "a": "先确认法律关系，再决定社保稽核、仲裁或诉讼路径。"},
        {"q": "罚款过高如何主张？", "a": "保存规则公示证据、扣款明细与申诉记录，审查规则公平性。"},
    ],
    LaborerType.COURIER.value: [
        {"q": "站点罚款是否有效？", "a": "审查是否公示、是否过苛、有无申诉渠道，保存证据。"},
    ],
    LaborerType.OTHER_UNCERTAIN.value: [
        {"q": "我不确定属于哪一类？", "a": "使用系统「类型判定」引导问答，再匹配场景与清单。"},
    ],
}


def faq_for(laborer_type: str) -> List[Dict[str, str]]:
    return FAQ_BY_TYPE.get(laborer_type, FAQ_BY_TYPE[LaborerType.OTHER_UNCERTAIN.value])


GUIDE_TEMPLATE: Dict[str, Dict[str, Any]] = {
    LaborerType.REGULAR.value: {
        "steps": [
            "收集劳动合同、工资流水、考勤记录等基础材料",
            "明确诉求：双倍工资/赔偿金/加班费/补缴社保等",
            "向劳动履行地或公司注册地仲裁委提交申请书",
        ],
        "materials": ["仲裁申请书", "身份证复印件", "劳动合同", "工资银行流水", "考勤记录（截图/打印）"],
        "commission_hint": "优先向劳动合同履行地劳动人事争议仲裁委员会申请",
    },
    LaborerType.DISPATCH.value: {
        "steps": [
            "准备身份证、派遣合同、工资流水",
            "向劳动合同履行地或用人单位所在地仲裁委申请",
            "提交申请书与证据清单，按指引补充材料",
        ],
        "materials": ["仲裁申请书", "身份证明", "劳务派遣合同", "证据复印件（分类编号）"],
        "commission_hint": "可通过地图搜索「区/市劳动人事争议仲裁委员会」",
    },
    LaborerType.INTERN.value: {
        "steps": [
            "整理实习协议、考勤、报酬约定记录",
            "明确诉求：报酬/违约/伤害赔偿等",
            "按仲裁或法院指引提交（部分争议走民事诉讼）",
        ],
        "materials": ["仲裁/诉讼文书", "实习协议", "证据目录"],
        "commission_hint": "实习争议路径因个案不同，建议先完成智能咨询确认",
    },
    LaborerType.PLATFORM.value: {
        "steps": [
            "导出订单、罚款、聊天等关键截图",
            "初步整理时间线与金额",
            "申请仲裁并提交劳动关系相关证据",
        ],
        "materials": ["申请书", "身份证明", "平台证据打包", "录音文字稿（如有）"],
        "commission_hint": "优先劳动合同履行地仲裁委",
    },
    LaborerType.COURIER.value: {
        "steps": ["导出跑单与罚款记录", "准备工资与考勤", "提交仲裁申请"],
        "materials": ["申请书", "身份证明", "跑单与扣款证据"],
        "commission_hint": "与平台/站点所在地仲裁委咨询管辖",
    },
    LaborerType.OTHER_UNCERTAIN.value: {
        "steps": ["完成类型判定", "按匹配类型准备材料", "生成文书并现场提交"],
        "materials": ["依判定类型自动生成清单"],
        "commission_hint": "完成判定后展示对应仲裁委检索建议",
    },
}
