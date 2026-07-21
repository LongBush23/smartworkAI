from fastapi import APIRouter, Depends
from backend.security import get_current_user
from backend.database import db
from backend.dependencies import require_leader_or_above
from backend.services.ai_core import predict_project_deadline, optimize_resources, analyze_performance, workload_analysis

router = APIRouter()

@router.get("/predict-deadline/{project_id}", dependencies=[Depends(get_current_user)])
async def get_deadline_prediction(project_id: str):
    result = await predict_project_deadline(project_id)
    return result

@router.get("/optimize-resources/{task_id}", dependencies=[Depends(get_current_user)])
async def get_resource_optimization(task_id: str):
    result = await optimize_resources(task_id)
    return result

@router.get("/performance", dependencies=[Depends(get_current_user)])
async def get_performance_analysis():
    result = await analyze_performance()
    return result

@router.get("/recommend-tasks", dependencies=[Depends(get_current_user)])
async def get_recommended_tasks(current_user: dict = Depends(get_current_user)):
    """
    AI gợi ý danh sách Task phù hợp nhất cho nhân viên.
    """
    from backend.services.gemini_service import get_match_score_from_gemini
    
    # Get all unassigned tasks (or tasks with few assignees)
    cursor = db.tasks.find({"status": "todo", "assigned_to": None})
    tasks = await cursor.to_list(length=20)
    
    recommendations = []
    for t in tasks:
        # Calculate score using Gemini
        gemini_result = await get_match_score_from_gemini(current_user, t)
        t["_id"] = str(t["_id"])
        
        # Only recommend if score > 60
        if gemini_result["match_score"] >= 60:
            recommendations.append({
                "task": t,
                "match_score": gemini_result["match_score"],
                "reasoning": gemini_result["reasoning"]
            })
            
    # Sort by highest score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations[:5]  # Top 5

@router.get("/workload-analysis", dependencies=[Depends(require_leader_or_above)])
async def get_workload_analysis():
    """
    Phân tích tình trạng làm việc, dự báo nhân viên nào đang bị Overload.
    Chỉ dành cho Quản lý.
    """
    result = await workload_analysis()
    return result
