from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from backend.database import db
from backend.security import get_current_user
from backend.dependencies import (
    require_leader_or_above,
    require_director_or_above,
    require_admin
)
from backend.models.kpi_schemas import (
    KPICatalogCreate, KPICatalogUpdate, KPICatalogResponse,
    KPIEvaluationCreate, KPIEvaluationResponse,
    SelfEvaluationSubmit, ReviewSubmit, GeneralCriteriaSubmit
)
from backend.services.kpi_service import (
    process_evaluation_approval, get_kpi_ranking,
    get_quarterly_kpi, get_yearly_kpi
)

from backend.models.kpi_criteria import CRITERIA_TEMPLATES as _CRITERIA_TEMPLATES

router = APIRouter(prefix="/api/kpi", tags=["KPI"])

# ================= 1. DANH MỤC NHIỆM VỤ CÔNG TÁC =================

@router.get("/catalog", response_model=List[KPICatalogResponse])
async def get_kpi_catalogs(
    department_id: Optional[str] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if department_id:
        query["department_id"] = department_id
    if period_year:
        query["period_year"] = period_year
        
    cursor = db.kpi_task_catalog.find(query)
    catalogs = await cursor.to_list(length=None)
    for c in catalogs:
        c["id"] = str(c.pop("_id"))
    return catalogs

@router.post("/catalog", response_model=KPICatalogResponse)
async def create_kpi_catalog(
    catalog_in: KPICatalogCreate,
    current_user: dict = Depends(require_director_or_above)
):
    doc = catalog_in.model_dump()
    doc["status"] = "draft"
    doc["created_by"] = str(current_user["_id"])
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    
    # Ensure IDs are string
    for item in doc["items"]:
        item["id"] = str(item.get("id", ObjectId()))
    
    result = await db.kpi_task_catalog.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc

@router.put("/catalog/{catalog_id}/approve")
async def approve_kpi_catalog(
    catalog_id: str,
    current_user: dict = Depends(require_director_or_above)
):
    result = await db.kpi_task_catalog.update_one(
        {"_id": ObjectId(catalog_id)},
        {
            "$set": {
                "status": "approved",
                "approved_by": str(current_user["_id"]),
                "approved_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy Danh mục nhiệm vụ")
    return {"message": "Catalog approved"}

# ================= 2. QUẢN LÝ KỲ ĐÁNH GIÁ =================

@router.post("/evaluations", response_model=KPIEvaluationResponse)
async def create_evaluation(
    eval_in: KPIEvaluationCreate,
    current_user: dict = Depends(require_leader_or_above)
):
    # Determine target details
    if eval_in.evaluation_type.value == "individual":
        target = await db.users.find_one({"_id": ObjectId(eval_in.target_id)})
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy cán bộ")
        target_name = target.get("name", target.get("username"))
        target_role = target.get("role")
        department_id = target.get("department_id")
    else:
        target = await db.departments.find_one({"_id": ObjectId(eval_in.target_id)})
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")
        target_name = target.get("name")
        target_role = None
        department_id = str(target["_id"])
        
    doc = {
        "evaluation_type": eval_in.evaluation_type.value,
        "target_id": eval_in.target_id,
        "target_name": target_name,
        "target_role": target_role,
        "department_id": department_id,
        "period_type": eval_in.period_type.value,
        "period_month": eval_in.period_month,
        "period_year": eval_in.period_year,
        "overall_status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.kpi_evaluations.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc

@router.get("/evaluations", response_model=List[KPIEvaluationResponse])
async def list_evaluations(
    target_id: Optional[str] = None,
    department_id: Optional[str] = None,
    period_type: Optional[str] = None,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    role = current_user.get("role", "staff")

    if target_id:
        query["target_id"] = target_id
    elif role == "staff":
        # Cán bộ không giữ chức vụ chỉ thấy kỳ đánh giá của mình
        query["target_id"] = str(current_user["_id"])

    if department_id:
        query["department_id"] = department_id
    elif not target_id and role in ("leader", "director") and current_user.get("department_id"):
        # Lãnh đạo, chỉ huy chỉ thẩm định trong phạm vi đơn vị mình phụ trách
        query["department_id"] = current_user["department_id"]

    if period_month:
        query["period_month"] = period_month
    if period_type:
        query["period_type"] = period_type
    if period_year:
        query["period_year"] = period_year
        
    cursor = db.kpi_evaluations.find(query)
    evaluations = await cursor.to_list(length=None)
    for e in evaluations:
        e["id"] = str(e.pop("_id"))
    return evaluations

@router.get("/evaluations/{eval_id}", response_model=KPIEvaluationResponse)
async def get_evaluation(
    eval_id: str,
    current_user: dict = Depends(get_current_user)
):
    doc = await db.kpi_evaluations.find_one({"_id": ObjectId(eval_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ đánh giá")
    doc["id"] = str(doc.pop("_id"))
    return doc

# ================= 3. QUY TRÌNH ĐÁNH GIÁ 3 BƯỚC =================

@router.put("/evaluations/{eval_id}/self-evaluate")
async def submit_self_evaluation(
    eval_id: str,
    eval_in: SelfEvaluationSubmit,
    current_user: dict = Depends(get_current_user)
):
    # Basic check - ensure user owns this evaluation if they are staff
    eval_doc = await db.kpi_evaluations.find_one({"_id": ObjectId(eval_id)})
    if not eval_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ đánh giá")
        
    if current_user["role"] == "staff" and eval_doc["target_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Bạn không có quyền đánh giá đối tượng này")
    
    self_eval_data = {
        "status": "submitted",
        "submitted_at": datetime.utcnow(),
        "task_scores": [t.model_dump() for t in eval_in.task_scores],
        "proposed_rating": eval_in.proposed_rating.value
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(eval_id)},
        {
            "$set": {
                "self_evaluation": self_eval_data,
                "overall_status": "self_evaluating",
                "updated_at": datetime.utcnow()
            }
        }
    )
    return {"message": "Self evaluation submitted"}

@router.put("/evaluations/{eval_id}/review")
async def submit_review(
    eval_id: str,
    review_in: ReviewSubmit,
    current_user: dict = Depends(require_leader_or_above)
):
    review_data = {
        "status": "reviewed",
        "reviewed_by": str(current_user["_id"]),
        "reviewed_at": datetime.utcnow(),
        "task_scores": [t.model_dump() for t in review_in.task_scores],
        "review_note": review_in.review_note
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(eval_id)},
        {
            "$set": {
                "review": review_data,
                "overall_status": "reviewing",
                "updated_at": datetime.utcnow()
            }
        }
    )
    return {"message": "Review submitted"}

@router.put("/evaluations/{eval_id}/approve")
async def approve_evaluation(
    eval_id: str,
    current_user: dict = Depends(require_director_or_above)
):
    try:
        result = await process_evaluation_approval(eval_id, str(current_user["_id"]))
        return {"message": "Evaluation approved", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/evaluations/{eval_id}/general-criteria")
async def submit_general_criteria(
    eval_id: str,
    criteria_in: GeneralCriteriaSubmit,
    current_user: dict = Depends(require_director_or_above)
):
    # First get the evaluation to check kpi score
    eval_doc = await db.kpi_evaluations.find_one({"_id": ObjectId(eval_id)})
    if not eval_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ đánh giá")
        
    kpi_score = eval_doc.get("approval", {}).get("kpi_score", 0)
    total_E = sum(score.actual_score for score in criteria_in.scores)
    total_final_score = total_E + (kpi_score * 0.7)
    
    criteria_data = {
        "criteria_type": criteria_in.criteria_type,
        "scores": [s.model_dump() for s in criteria_in.scores],
        "total_E": total_E,
        "total_kpi_weighted": kpi_score * 0.7,
        "total_final_score": total_final_score,
        "scored_by": str(current_user["_id"]),
        "scored_at": datetime.utcnow()
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(eval_id)},
        {
            "$set": {
                "general_criteria": criteria_data,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return {"message": "General criteria scored", "total_final_score": total_final_score}

# ================= 4. KẾT QUẢ KPI & XẾP HẠNG =================

@router.get("/scores/ranking")
async def get_ranking(
    department_id: Optional[str] = None,
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
    current_user: dict = Depends(require_leader_or_above)
):
    # Directors can only see their department
    if current_user["role"] in ["director", "leader"] and not department_id:
        department_id = current_user.get("department_id")
        
    ranking = await get_kpi_ranking(department_id, period_month, period_year)
    return ranking

# ================= 5. TEMPLATES TIÊU CHÍ CHUNG (PHỤ LỤC) =================

@router.get("/criteria-templates")
async def get_criteria_templates(
    criteria_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Trả về templates tiêu chí chung theo Phụ lục Hướng dẫn số 20-HD/ĐUCA.
    criteria_type: 'collective' | 'leader' | 'staff'
    """
    if criteria_type:
        template = _CRITERIA_TEMPLATES.get(criteria_type)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{criteria_type}' not found")
        return template
    return list(_CRITERIA_TEMPLATES.values())
