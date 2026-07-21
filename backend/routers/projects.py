from fastapi import APIRouter, Depends, HTTPException
from backend.database import db
from backend.security import get_current_user
from backend.dependencies import require_leader_or_above, require_admin
from backend.models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.services.audit_service import log_action
from bson import ObjectId
from typing import List

router = APIRouter()

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(current_user: dict = Depends(get_current_user)):
    """All authenticated users can see projects. Directors see only their department."""
    query = {}
    role = current_user.get("role", "staff")
    
    # Director only sees their own department's projects
    if role == "director" and current_user.get("department_id"):
        query["$or"] = [
            {"department_id": current_user["department_id"]},
            {"department_id": None},
            {"department_id": {"$exists": False}},
        ]
    
    cursor = db.projects.find(query)
    projects = await cursor.to_list(length=100)
    return [fix_id(p) for p in projects]

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: dict = Depends(require_leader_or_above)):
    """Only Leader+ can create projects."""
    project_dict = project.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in project_dict:
        del project_dict["_id"]
    
    # Auto-assign department from creator if not specified
    if not project_dict.get("department_id") and current_user.get("department_id"):
        project_dict["department_id"] = current_user["department_id"]
    
    result = await db.projects.insert_one(project_dict)
    project_dict["_id"] = str(result.inserted_id)
    
    await log_action(current_user["_id"], current_user.get("name", ""), "project.created", "project", str(result.inserted_id), f"Name: {project.name}")
    return project_dict

@router.put("/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate, current_user: dict = Depends(require_leader_or_above)):
    """Only Leader+ can update projects."""
    update_data = project.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in update_data:
        del update_data["_id"]
    await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": update_data})
    
    await log_action(current_user["_id"], current_user.get("name", ""), "project.updated", "project", project_id, f"Fields: {list(update_data.keys())}")
    return {"message": "Project updated successfully"}

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(require_admin)):
    """Only Admin can delete projects."""
    await db.projects.delete_one({"_id": ObjectId(project_id)})
    await db.tasks.delete_many({"project_id": project_id})
    
    await log_action(current_user["_id"], current_user.get("name", ""), "project.deleted", "project", project_id)
    return {"message": "Project deleted successfully"}
