from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum, IntEnum

# ================= ENUMS =================

class ComplexityGroup(IntEnum):
    GROUP_1 = 1 # 0-50 points
    GROUP_2 = 2 # 50-70 points
    GROUP_3 = 3 # 70-100 points

class QualityTier(str, Enum):
    EXCELLENT = "excellent"     # Vượt mức yêu cầu (<=120%)
    GOOD = "good"               # Đảm bảo chất lượng (=100%)
    FAIR_1 = "fair_1"           # Cơ bản đảm bảo, sửa 1 lần (<=75%)
    FAIR_2_4 = "fair_2_4"       # Còn thiếu sót, sửa 2-4 lần (<=50%)
    POOR_5_6 = "poor_5_6"       # Thiếu sót, sửa 5-6 lần (<=25%)
    FAIL_7 = "fail_7"           # Sửa >=7 lần (0%)

class TimelineTier(str, Enum):
    AHEAD = "ahead"             # Vượt tiến độ + đảm bảo CL (<=120%)
    ON_TIME = "on_time"         # Đúng tiến độ + đảm bảo CL (=100%)
    LATE_1 = "late_1"           # Chưa đảm bảo, nhắc nhở 1 lần (<=75%)
    LATE_2 = "late_2"           # Chưa đảm bảo, nhắc nhở 2 lần (<=50%)
    LATE_3 = "late_3"           # Chưa đảm bảo, nhắc nhở 3 lần (<=25%)
    FAIL_4 = "fail_4"           # Nhắc nhở >=4 lần (0%)

class KPIGroup(str, Enum):
    GROUP_1 = "group_1"         # Đáp ứng tốt (>= 70)
    GROUP_2 = "group_2"         # Đáp ứng (50-70)
    GROUP_3 = "group_3"         # Chưa đáp ứng (< 50)

class EvaluationStatus(str, Enum):
    DRAFT = "draft"
    SELF_EVALUATING = "self_evaluating"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"

class PeriodType(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class EvaluationType(str, Enum):
    INDIVIDUAL = "individual"
    COLLECTIVE = "collective"

class CriteriaRating(str, Enum):
    DAM_BAO = "dam_bao"
    KHONG_DAM_BAO = "khong_dam_bao"

# ================= SCHEMAS =================

# --- KPI Task Catalog ---
class KPICatalogItem(BaseModel):
    id: str
    task_name: str
    category: str
    complexity_group: ComplexityGroup
    kpi_point: int = Field(ge=0, le=100)
    description: Optional[str] = None

class KPICatalogCreate(BaseModel):
    department_id: str
    period_year: int
    name: str
    items: List[KPICatalogItem]

class KPICatalogUpdate(BaseModel):
    name: Optional[str] = None
    items: Optional[List[KPICatalogItem]] = None

class KPICatalogResponse(BaseModel):
    id: str
    department_id: str
    period_year: int
    name: str
    status: str
    items: List[KPICatalogItem]
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

# --- Task KPI Score (used within evaluations) ---
class TaskKPIScoreBase(BaseModel):
    task_id: str
    catalog_item_id: Optional[str] = None
    task_name: str
    kpi_point: int
    is_completed: bool

class TaskKPIScoreSubmit(TaskKPIScoreBase):
    quality_tier: QualityTier
    timeline_tier: TimelineTier
    note: Optional[str] = None

class TaskKPIScore(TaskKPIScoreSubmit):
    quality_percent: float
    quality_score: float
    timeline_percent: float
    timeline_score: float

class SelfEvaluationSubmit(BaseModel):
    task_scores: List[TaskKPIScoreSubmit]
    proposed_rating: KPIGroup

class ReviewSubmit(BaseModel):
    task_scores: List[TaskKPIScoreSubmit]
    review_note: Optional[str] = None

# --- General Criteria ---
class GeneralCriteriaScoreItem(BaseModel):
    criteria_id: str
    criteria_name: str
    max_score: int
    rating: CriteriaRating
    actual_score: float
    note: Optional[str] = None

class GeneralCriteriaSubmit(BaseModel):
    criteria_type: str
    scores: List[GeneralCriteriaScoreItem]

# --- KPI Evaluation ---
class KPIEvaluationCreate(BaseModel):
    evaluation_type: EvaluationType
    target_id: str
    period_type: PeriodType
    period_month: Optional[int] = None
    period_year: int
    task_ids: List[str]

# Using a simplified response model that dumps all dictionary keys
class KPIEvaluationResponse(BaseModel):
    id: str
    evaluation_type: str
    target_id: str
    target_name: str
    target_role: Optional[str] = None
    department_id: str
    period_type: str
    period_month: Optional[int] = None
    period_year: int
    self_evaluation: Optional[Dict[str, Any]] = None
    review: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    general_criteria: Optional[Dict[str, Any]] = None
    overall_status: str
    created_at: datetime
    updated_at: datetime

# --- KPI Score Results ---
class KPIScoreResult(BaseModel):
    score_A: float
    score_B: float
    score_C: float
    score_D: Optional[float] = None
    kpi_score: float
    kpi_group: str
    total_assigned_points: int

class KPIRankingItem(BaseModel):
    target_id: str
    target_name: str
    department_name: Optional[str] = None
    role: Optional[str] = None
    kpi_score: float
    kpi_group: str
    score_A: float
    score_B: float
    score_C: float
    score_D: Optional[float] = None
    total_E: Optional[float] = None
    total_final_score: Optional[float] = None

# --- General Criteria Template ---
class CriteriaTemplateItem(BaseModel):
    id: str
    name: str
    max_score: int
    sub_criteria: Optional[list] = None

class CriteriaTemplate(BaseModel):
    id: str
    type: str
    name: str
    total_max_score: int
    criteria: List[CriteriaTemplateItem]
