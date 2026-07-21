from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

# ================= ENUMS =================
class RoleEnum(str, Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    LEADER = "leader"
    STAFF = "staff"

class ProjectStatusEnum(str, Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"

class TaskStatusEnum(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class TaskPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class RequestStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

class NotificationType(str, Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    REQUEST_SUBMITTED = "request_submitted"
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_AUTO_APPROVED = "request_auto_approved"
    DEADLINE_WARNING = "deadline_warning"
    TASK_OVERDUE = "task_overdue"
    WORKLOAD_ALERT = "workload_alert"
    TASK_COMPLETED = "task_completed"
    GENERAL = "general"

# ================= AUTH & TOKEN =================
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# ================= DEPARTMENT =================
class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: str = Field(alias="_id")

# ================= USER / EMPLOYEE (AI ENHANCED) =================
class Skill(BaseModel):
    skill_name: str
    self_rating: int = Field(default=3, ge=1, le=5)
    verified_rating: Optional[float] = None
    last_used: Optional[datetime] = None

class WorkPreferences(BaseModel):
    interests: List[str] = []
    preferred_task_types: List[str] = []
    max_concurrent_tasks: int = 3

class AIMetrics(BaseModel):
    historical_quality_score: float = 50.0
    on_time_rate: float = 1.0
    capacity_hours_per_week: int = 40
    current_workload_hours: int = 0

class UserBase(BaseModel):
    username: str
    name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.STAFF
    department_id: Optional[str] = None
    skills: List[Skill] = []
    preferences: WorkPreferences = Field(default_factory=WorkPreferences)
    bio: Optional[str] = None
    avatar: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    role: Optional[RoleEnum] = None
    department_id: Optional[str] = None
    skills: Optional[List[Skill]] = None
    preferences: Optional[WorkPreferences] = None
    bio: Optional[str] = None
    availability: Optional[float] = None
    quality_score: Optional[float] = None
    current_workload: Optional[int] = None
    ai_metrics: Optional[AIMetrics] = None

class ProfileUpdate(BaseModel):
    name: str
    email: EmailStr
    skills: List[Skill]
    preferences: Optional[WorkPreferences] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None

class UserResponse(UserBase):
    id: str = Field(alias="_id")
    ai_metrics: AIMetrics = Field(default_factory=AIMetrics)
    
    # Legacy fields
    availability: float = 100.0
    quality_score: float = 50.0
    current_workload: int = 0
    is_admin: bool = False
    
    class Config:
        populate_by_name = True

class UserInDB(UserResponse):
    hashed_password: str

# ================= PROJECT =================
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatusEnum = ProjectStatusEnum.PLANNING
    start_date: datetime
    end_date: datetime
    progress: float = Field(default=0, ge=0, le=100)
    department_id: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatusEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    department_id: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str = Field(alias="_id")
    historical_score: Optional[float] = None

    class Config:
        populate_by_name = True

# ================= SUBTASK & COMMENT =================
class SubTask(BaseModel):
    id: str
    title: str
    is_completed: bool = False

class CommentBase(BaseModel):
    task_id: str
    content: str

class CommentCreate(BaseModel):
    content: str

class CommentResponse(CommentBase):
    id: str = Field(alias="_id")
    user_id: str
    user_name: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True

# ================= TASK =================
class TaskBase(BaseModel):
    project_id: str
    title: str
    description: str
    assigned_to: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.TODO
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    progress: float = Field(default=0, ge=0, le=100)
    deadline: datetime
    effort_required: int = 1
    required_skills: List[str] = []
    max_assignees: int = 1
    subtasks: List[SubTask] = []
    attachments: List[str] = []

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    deadline: Optional[datetime] = None
    effort_required: Optional[int] = None
    actual_end: Optional[datetime] = None
    required_skills: Optional[List[str]] = None
    max_assignees: Optional[int] = None
    subtasks: Optional[List[SubTask]] = None
    attachments: Optional[List[str]] = None

class TaskResponse(TaskBase):
    id: str = Field(alias="_id")
    actual_end: Optional[datetime] = None
    quality_score: Optional[float] = None

    # Aggregated fields (Populated via joins)
    project_name: Optional[str] = None
    assignee_name: Optional[str] = None

    class Config:
        populate_by_name = True

# ================= TASK REQUEST (JOIN REQUEST) =================
class TaskRequestCreate(BaseModel):
    message: Optional[str] = None

class TaskRequestResponse(BaseModel):
    id: str = Field(alias="_id")
    task_id: str
    task_title: Optional[str] = None
    employee_id: str
    employee_name: Optional[str] = None
    status: RequestStatusEnum = RequestStatusEnum.PENDING
    ai_match_score: Optional[float] = None
    message: Optional[str] = None
    created_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reject_reason: Optional[str] = None

    class Config:
        populate_by_name = True

class TaskRequestReview(BaseModel):
    reject_reason: Optional[str] = None

# ================= NOTIFICATION =================
class NotificationResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    type: NotificationType
    title: str
    message: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    is_read: bool = False
    created_at: datetime

    class Config:
        populate_by_name = True

# ================= AUDIT LOG =================
class AuditLogResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    user_name: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True

# ================= TIME LOG =================
class TimeLogBase(BaseModel):
    task_id: str
    hours: float

class TimeLogCreate(TimeLogBase):
    log_date: datetime = Field(default_factory=datetime.utcnow)

class TimeLogResponse(TimeLogBase):
    id: str = Field(alias="_id")
    user_id: str
    log_date: datetime
    
    class Config:
        populate_by_name = True
