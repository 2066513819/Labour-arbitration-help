from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.data.classification_flow import FLOW_STEPS, infer_laborer_type
from app.data.scenario_catalog import GUIDE_TEMPLATE, SCENARIOS, get_scenarios, faq_for
from app.deps import get_current_user
from app.models.user import User
from app.schemas.labor import LaborerType

router = APIRouter(prefix="/labor", tags=["labor"])


@router.get("/types")
def list_types():
    items = [
        {"value": LaborerType.REGULAR.value, "label": "正式员工", "accent": "blue"},
        {"value": LaborerType.DISPATCH.value, "label": "劳务派遣员工", "accent": "sky"},
        {"value": LaborerType.INTERN.value, "label": "在校实习生", "accent": "emerald"},
        {"value": LaborerType.PLATFORM.value, "label": "外卖/快递/网约车", "accent": "amber"},
        {"value": LaborerType.OTHER_UNCERTAIN.value, "label": "其他/不确定", "accent": "slate"},
    ]
    return {"items": items, "ui_meta": {"card_radius": 16}}


@router.get("/scenarios")
def scenarios(
    laborer_type: str = Query(..., description="劳动者类型 value"),
    user: User = Depends(get_current_user),
):
    if user.laborer_type and user.laborer_type != laborer_type:
        pass  # 允许查看非当前类型用于管理
    data = get_scenarios(laborer_type)
    return {"laborer_type": laborer_type, "scenarios": data}


@router.get("/classification-flow")
def classification_flow():
    return {"steps": FLOW_STEPS, "max_steps": 5}


@router.post("/classification-result")
def classification_result(answers: Dict[str, str] = Body(...)):
    lt, reason = infer_laborer_type(answers)
    return {
        "laborer_type": lt,
        "reason": reason,
        "recommended_scenarios": get_scenarios(lt),
        "ui_meta": {"transition": "slide-up", "duration_ms": 300},
    }


@router.get("/faq")
def faq(laborer_type: str = Query(...)):
    return {"items": faq_for(laborer_type)}


@router.get("/guide")
def guide(laborer_type: str = Query(...)):
    g = GUIDE_TEMPLATE.get(laborer_type)
    if not g:
        raise HTTPException(404, "未知类型")
    return {"laborer_type": laborer_type, **g}


@router.get("/evidence-checklist")
def evidence_checklist(laborer_type: str = Query(...), scenario_id: Optional[str] = None):
    scenarios = SCENARIOS.get(laborer_type, [])
    if scenario_id:
        for s in scenarios:
            if s["id"] == scenario_id:
                return {"required": s.get("evidence_hint", []), "scenario_id": scenario_id}
    return {"generic": [s["evidence_hint"] for s in scenarios[:2]]}
