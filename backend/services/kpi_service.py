from backend.database import db
from backend.models.kpi_schemas import (
    QualityTier, TimelineTier, KPIGroup, 
    TaskKPIScore, KPIScoreResult
)
from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any

# ================= 1. QUALITY/TIMELINE MAPPING =================

def get_quality_percent(tier: str) -> float:
    """Map QualityTier to percentage multiplier"""
    mapping = {
        QualityTier.EXCELLENT.value: 1.20,
        QualityTier.GOOD.value: 1.00,
        QualityTier.FAIR_1.value: 0.75,
        QualityTier.FAIR_2_4.value: 0.50,
        QualityTier.POOR_5_6.value: 0.25,
        QualityTier.FAIL_7.value: 0.00,
    }
    return mapping.get(tier, 0.0)

def get_timeline_percent(tier: str) -> float:
    """Map TimelineTier to percentage multiplier"""
    mapping = {
        TimelineTier.AHEAD.value: 1.20,
        TimelineTier.ON_TIME.value: 1.00,
        TimelineTier.LATE_1.value: 0.75,
        TimelineTier.LATE_2.value: 0.50,
        TimelineTier.LATE_3.value: 0.25,
        TimelineTier.FAIL_4.value: 0.00,
    }
    return mapping.get(tier, 0.0)

# ================= 2. SCORE CALCULATION (A, B, C) =================

def calculate_score_A(task_scores: List[dict], total_assigned_points: int) -> float:
    """Điểm số lượng = Σ(điểm CV đã hoàn thành) / Σ(điểm CV được giao)"""
    if total_assigned_points == 0:
        return 0.0
    completed_points = sum(task.get("kpi_point", 0) for task in task_scores if task.get("is_completed", False))
    return completed_points / total_assigned_points

def get_task_quality_score(task: dict) -> float:
    """Tính điểm chất lượng của 1 công việc từ quality_tier"""
    if task.get("quality_score") is not None:
        return float(task["quality_score"])
    pct = get_quality_percent(task.get("quality_tier", QualityTier.FAIL_7.value))
    return task.get("kpi_point", 0) * pct

def get_task_timeline_score(task: dict) -> float:
    """Tính điểm tiến độ của 1 công việc từ timeline_tier"""
    if task.get("timeline_score") is not None:
        return float(task["timeline_score"])
    pct = get_timeline_percent(task.get("timeline_tier", TimelineTier.FAIL_4.value))
    return task.get("kpi_point", 0) * pct

def calculate_score_B(task_scores: List[dict], total_assigned_points: int) -> float:
    """Điểm chất lượng = Σ(kpi_point × quality_percent) / Σ(điểm CV được giao)"""
    if total_assigned_points == 0:
        return 0.0
    quality_points = sum(get_task_quality_score(task) for task in task_scores if task.get("is_completed", False))
    return quality_points / total_assigned_points

def calculate_score_C(task_scores: List[dict], total_assigned_points: int) -> float:
    """Điểm tiến độ = Σ(kpi_point × timeline_percent) / Σ(điểm CV được giao)"""
    if total_assigned_points == 0:
        return 0.0
    timeline_points = sum(get_task_timeline_score(task) for task in task_scores if task.get("is_completed", False))
    return timeline_points / total_assigned_points

# ================= 3. SCORE D (LEADERSHIP) =================

async def calculate_score_D(leader_id: str, period_month: Optional[int], period_year: int) -> float:
    """Điểm lãnh đạo = Số thuộc quyền quản lý hoàn thành NV (nhóm 1, 2) / Tổng số được đánh giá"""
    # Find the leader's department
    leader = await db.users.find_one({"_id": ObjectId(leader_id)})
    if not leader or not leader.get("department_id"):
        return 0.0
    
    dept_id = leader["department_id"]
    
    # Query evaluations for this period and department (excluding the leader themselves)
    query = {
        "department_id": dept_id,
        "target_id": {"$ne": leader_id},
        "period_year": period_year,
        "overall_status": "approved"
    }
    if period_month:
        query["period_month"] = period_month
        
    evaluations = await db.kpi_evaluations.find(query).to_list(length=None)
    
    if not evaluations:
        return 0.0
        
    total_evaluated = len(evaluations)
    completed_count = sum(1 for e in evaluations 
                          if e.get("approval", {}).get("kpi_group") in [KPIGroup.GROUP_1.value, KPIGroup.GROUP_2.value])
                          
    return completed_count / total_evaluated

# ================= 4. KPI AGGREGATION & GROUPS =================

def calculate_kpi(score_A: float, score_B: float, score_C: float, score_D: Optional[float] = None, is_leader: bool = False) -> float:
    """Calculate final KPI score."""
    if is_leader and score_D is not None:
        return ((score_A + score_B + score_C + score_D) / 4) * 100
    else:
        return ((score_A + score_B + score_C) / 3) * 100

def determine_kpi_group(kpi_score: float) -> str:
    """Classify into groups"""
    if kpi_score >= 70:
        return KPIGroup.GROUP_1.value
    elif kpi_score >= 50:
        return KPIGroup.GROUP_2.value
    else:
        return KPIGroup.GROUP_3.value

# ================= 5. TOTAL SCORE =================

def calculate_total_score(total_E: float, kpi_score: float) -> float:
    """F/G/H = E + KPI × 0.7"""
    return total_E + (kpi_score * 0.7)

# ================= 6. EVALUATION PROCESSING =================

async def process_evaluation_approval(evaluation_id: str, approved_by: str) -> Dict[str, Any]:
    """Process full KPI calculation when an evaluation is approved"""
    eval_doc = await db.kpi_evaluations.find_one({"_id": ObjectId(evaluation_id)})
    if not eval_doc:
        raise ValueError("Evaluation not found")
        
    # Get tasks from review if exists, else from self_evaluation
    review_data = eval_doc.get("review", {})
    self_eval = eval_doc.get("self_evaluation", {})
    
    if review_data and "task_scores" in review_data:
        task_scores = review_data["task_scores"]
    elif self_eval and "task_scores" in self_eval:
        task_scores = self_eval["task_scores"]
    else:
        task_scores = []
        
    # Calculate points
    total_assigned_points = sum(task.get("kpi_point", 0) for task in task_scores)
    
    score_A = calculate_score_A(task_scores, total_assigned_points)
    score_B = calculate_score_B(task_scores, total_assigned_points)
    score_C = calculate_score_C(task_scores, total_assigned_points)
    
    # Check if leader
    is_leader = eval_doc.get("target_role") in ["leader", "director"]
    score_D = None
    
    if is_leader:
        score_D = await calculate_score_D(
            eval_doc["target_id"], 
            eval_doc.get("period_month"), 
            eval_doc.get("period_year")
        )
        
    kpi_score = calculate_kpi(score_A, score_B, score_C, score_D, is_leader)
    kpi_group = determine_kpi_group(kpi_score)
    
    # Ensure leader KPI <= collective KPI
    if is_leader and eval_doc.get("evaluation_type") == "individual":
        # Check collective KPI for the same period
        coll_query = {
            "department_id": eval_doc.get("department_id"),
            "evaluation_type": "collective",
            "period_year": eval_doc.get("period_year"),
            "period_type": eval_doc.get("period_type"),
            "overall_status": "approved"
        }
        if eval_doc.get("period_month"):
            coll_query["period_month"] = eval_doc.get("period_month")
            
        coll_eval = await db.kpi_evaluations.find_one(coll_query)
        if coll_eval and coll_eval.get("approval", {}).get("kpi_score") is not None:
            coll_kpi = coll_eval["approval"]["kpi_score"]
            if kpi_score > coll_kpi:
                kpi_score = coll_kpi
                kpi_group = determine_kpi_group(kpi_score)
    
    approval_data = {
        "approved_by": approved_by,
        "approved_at": datetime.utcnow(),
        "status": "approved",
        "total_assigned_points": total_assigned_points,
        "score_A": score_A,
        "score_B": score_B,
        "score_C": score_C,
        "score_D": score_D,
        "kpi_score": kpi_score,
        "kpi_group": kpi_group
    }
    
    await db.kpi_evaluations.update_one(
        {"_id": ObjectId(evaluation_id)},
        {
            "$set": {
                "approval": approval_data,
                "overall_status": "approved",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return approval_data

# ================= 7. PERIOD AGGREGATION =================

async def get_quarterly_kpi(user_id: str, year: int, quarter: int) -> float:
    """KPI quý = bình quân KPI các tháng trong quý"""
    months = []
    if quarter == 1: months = [1, 2, 3]
    elif quarter == 2: months = [4, 5, 6]
    elif quarter == 3: months = [7, 8, 9]
    elif quarter == 4: months = [10, 11, 12]
    
    evaluations = await db.kpi_evaluations.find({
        "target_id": user_id,
        "evaluation_type": "individual",
        "period_type": "monthly",
        "period_year": year,
        "period_month": {"$in": months},
        "overall_status": "approved"
    }).to_list(length=None)
    
    if not evaluations:
        return 0.0
        
    total_kpi = sum(e.get("approval", {}).get("kpi_score", 0.0) for e in evaluations)
    return total_kpi / len(evaluations)

async def get_yearly_kpi(user_id: str, year: int) -> float:
    """KPI năm = bình quân KPI các tháng trong năm"""
    evaluations = await db.kpi_evaluations.find({
        "target_id": user_id,
        "evaluation_type": "individual",
        "period_type": "monthly",
        "period_year": year,
        "overall_status": "approved"
    }).to_list(length=None)
    
    if not evaluations:
        return 0.0
        
    total_kpi = sum(e.get("approval", {}).get("kpi_score", 0.0) for e in evaluations)
    return total_kpi / len(evaluations)

# ================= 8. RANKING =================

async def get_kpi_ranking(department_id: Optional[str] = None, period_month: Optional[int] = None, period_year: Optional[int] = None) -> List[dict]:
    """Get ranked list of all evaluated individuals"""
    query = {
        "evaluation_type": "individual",
        "overall_status": "approved"
    }
    if department_id:
        query["department_id"] = department_id
    if period_year:
        query["period_year"] = period_year
    if period_month:
        query["period_month"] = period_month
        
    evaluations = await db.kpi_evaluations.find(query).to_list(length=None)
    
    results = []
    for eval_doc in evaluations:
        approval = eval_doc.get("approval", {})
        general_criteria = eval_doc.get("general_criteria", {})
        
        item = {
            "target_id": eval_doc["target_id"],
            "target_name": eval_doc.get("target_name", ""),
            "department_id": eval_doc.get("department_id"),
            "role": eval_doc.get("target_role", ""),
            "kpi_score": approval.get("kpi_score", 0.0),
            "kpi_group": approval.get("kpi_group", ""),
            "score_A": approval.get("score_A", 0.0),
            "score_B": approval.get("score_B", 0.0),
            "score_C": approval.get("score_C", 0.0),
            "score_D": approval.get("score_D"),
            "total_E": general_criteria.get("total_E"),
            "total_final_score": general_criteria.get("total_final_score")
        }
        results.append(item)
        
    # Sort by kpi_score descending
    results.sort(key=lambda x: x["kpi_score"], reverse=True)
    return results
