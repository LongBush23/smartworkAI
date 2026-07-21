from fastapi import APIRouter, Depends
from backend.database import db
from backend.security import get_current_user
from backend.models.schemas import TimeLogCreate, TimeLogResponse
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.get("/", response_model=List[TimeLogResponse], dependencies=[Depends(get_current_user)])
async def get_time_logs(task_id: Optional[str] = None, user_id: Optional[str] = None):
    query = {}
    if task_id:
        query["task_id"] = task_id
    if user_id:
        query["user_id"] = user_id
    cursor = db.time_logs.find(query).sort("log_date", -1)
    logs = await cursor.to_list(length=100)
    return [fix_id(log) for log in logs]

@router.post("/", response_model=TimeLogResponse)
async def create_time_log(log: TimeLogCreate, current_user: dict = Depends(get_current_user)):
    log_dict = log.model_dump(exclude_unset=True, by_alias=True)
    if "_id" in log_dict:
        del log_dict["_id"]
    if "log_date" not in log_dict or not log_dict["log_date"]:
        log_dict["log_date"] = datetime.utcnow()
    log_dict["user_id"] = str(current_user["_id"])
    result = await db.time_logs.insert_one(log_dict)
    log_dict["_id"] = str(result.inserted_id)
    return log_dict

@router.delete("/{log_id}", dependencies=[Depends(get_current_user)])
async def delete_time_log(log_id: str):
    await db.time_logs.delete_one({"_id": ObjectId(log_id)})
    return {"message": "Time log deleted successfully"}
