"""
Schemas nghiệp vụ cho Hệ thống tính điểm KPI trong Công an nhân dân
(Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026).

Các schema riêng của KPI nằm ở models/kpi_schemas.py.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

# ================= ENUMS =================

class RoleEnum(str, Enum):
    """Phân cấp thẩm quyền: ADMIN > DIRECTOR > LEADER > STAFF"""
    ADMIN = "admin"        # Quản trị hệ thống
    DIRECTOR = "director"  # Lãnh đạo đơn vị (người đứng đầu)
    LEADER = "leader"      # Lãnh đạo, chỉ huy cấp Phòng/Đội
    STAFF = "staff"        # Cán bộ, chiến sĩ không giữ chức vụ lãnh đạo


class TaskStatusEnum(str, Enum):
    """Trạng thái thực hiện nhiệm vụ công tác"""
    ASSIGNED = "assigned"        # Đã giao, chưa thực hiện
    IN_PROGRESS = "in_progress"  # Đang thực hiện
    REVIEW = "review"            # Đã trình, đang xem xét/hoàn thiện
    DONE = "done"                # Đã hoàn thành


class TaskProductEnum(str, Enum):
    """Sản phẩm công việc theo Danh mục nhiệm vụ công tác"""
    CONG_VAN = "cong_van"      # Công văn
    BAO_CAO = "bao_cao"        # Báo cáo
    TO_TRINH = "to_trinh"      # Tờ trình
    THONG_TU = "thong_tu"      # Thông tư
    QUY_DINH = "quy_dinh"      # Quy định
    KE_HOACH = "ke_hoach"      # Kế hoạch
    DE_AN = "de_an"            # Đề án
    KHAC = "khac"              # Sản phẩm khác


class NotificationType(str, Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    TASK_REMINDED = "task_reminded"          # Nhắc nhở về tiến độ (ảnh hưởng điểm C)
    TASK_REVISION = "task_revision"          # Yêu cầu hoàn thiện, chỉnh sửa (ảnh hưởng điểm B)
    DEADLINE_WARNING = "deadline_warning"
    TASK_OVERDUE = "task_overdue"
    TASK_COMPLETED = "task_completed"
    KPI_SELF_EVAL_REQUIRED = "kpi_self_eval_required"  # Bước 1
    KPI_REVIEW_REQUIRED = "kpi_review_required"        # Bước 2
    KPI_APPROVED = "kpi_approved"                      # Bước 3
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


# ================= ĐƠN VỊ =================

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    # Hệ lực lượng (theo tài liệu: xây dựng Danh mục nhiệm vụ theo hệ lực lượng)
    force_system: Optional[str] = None
    parent_id: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    force_system: Optional[str] = None
    parent_id: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


# ================= CÁN BỘ =================

class UserBase(BaseModel):
    username: str
    name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.STAFF
    department_id: Optional[str] = None
    # Chức vụ cụ thể (VD: Trưởng phòng, Phó Trưởng phòng, Chuyên viên)
    position: Optional[str] = None
    # Cấp bậc hàm (VD: Thiếu tá, Đại úy)
    rank: Optional[str] = None
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
    position: Optional[str] = None
    rank: Optional[str] = None
    bio: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: str
    email: EmailStr
    position: Optional[str] = None
    rank: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    is_admin: bool = False
    # Là lãnh đạo, chỉ huy → KPI tính theo 04 tiêu chí (có thêm điểm D)
    is_commander: bool = False

    class Config:
        populate_by_name = True


class UserInDB(UserResponse):
    hashed_password: str


# ================= NHIỆM VỤ CÔNG TÁC =================

class TaskBase(BaseModel):
    """
    Một nhiệm vụ công tác được giao, gắn với một mục trong
    Danh mục nhiệm vụ công tác theo KPI.
    """
    title: str
    description: Optional[str] = None
    # Liên kết tới mục trong Danh mục nhiệm vụ (để lấy điểm và nhóm độ phức tạp)
    catalog_item_id: Optional[str] = None
    # Sản phẩm công việc đầu ra
    product: TaskProductEnum = TaskProductEnum.KHAC
    # Điểm của công việc được giao theo Danh mục (thang 100)
    kpi_point: int = Field(default=0, ge=0, le=100)
    # Số lượng sản phẩm được giao / đã hoàn thành
    quantity_assigned: int = Field(default=1, ge=0)
    quantity_completed: int = Field(default=0, ge=0)

    assigned_to: Optional[str] = None
    department_id: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.ASSIGNED
    deadline: datetime

    # Số lần phải hoàn thiện, chỉnh sửa → quyết định mức điểm chất lượng (B)
    revision_count: int = Field(default=0, ge=0)
    # Số lần bị nhắc nhở về tiến độ → quyết định mức điểm tiến độ (C)
    reminder_count: int = Field(default=0, ge=0)

    # Kỳ đánh giá mà nhiệm vụ này thuộc về
    period_month: Optional[int] = Field(default=None, ge=1, le=12)
    period_year: Optional[int] = None

    attachments: List[str] = []


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    catalog_item_id: Optional[str] = None
    product: Optional[TaskProductEnum] = None
    kpi_point: Optional[int] = Field(default=None, ge=0, le=100)
    quantity_assigned: Optional[int] = Field(default=None, ge=0)
    quantity_completed: Optional[int] = Field(default=None, ge=0)
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    deadline: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    revision_count: Optional[int] = Field(default=None, ge=0)
    reminder_count: Optional[int] = Field(default=None, ge=0)
    period_month: Optional[int] = Field(default=None, ge=1, le=12)
    period_year: Optional[int] = None
    attachments: Optional[List[str]] = None


class TaskResponse(TaskBase):
    id: str = Field(alias="_id")
    actual_end: Optional[datetime] = None
    # Trường bổ sung qua join
    assignee_name: Optional[str] = None
    department_name: Optional[str] = None

    class Config:
        populate_by_name = True


# ================= Ý KIẾN TRAO ĐỔI =================

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


# ================= THÔNG BÁO =================

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


# ================= NHẬT KÝ =================

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
