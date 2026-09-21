from enum import Enum
from typing import Optional

from pydantic import BaseModel


class LaborerType(str, Enum):
    REGULAR = "regular"
    DISPATCH = "dispatch"
    INTERN = "intern"
    PLATFORM = "platform"
    COURIER = "courier"
    OTHER_UNCERTAIN = "other_uncertain"


class UIInteractionMeta(BaseModel):
    animation: Optional[str] = None
    duration_ms: Optional[int] = None
    state: Optional[str] = None
