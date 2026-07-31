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


class DepartmentLevelEnum(str, Enum):
    """Cấp đơn vị theo đối tượng áp dụng của Hướng dẫn 20-HD/ĐUCA"""
    BO = "bo"          # Cơ quan Bộ
    CUC = "cuc"        # Cục, Công an tỉnh/thành phố và tương đương
    PHONG = "phong"    # Phòng, Trung đoàn và tương đương
    DOI = "doi"        # Đội, Tiểu đoàn, Công an xã/phường/đặc khu


class TaskStatusEnum(str, Enum):
    """Trạng thái thực hiện nhiệm vụ công tác"""
    ASSIGNED = "assigned"        # Đã giao, chưa thực hiện
    IN_PROGRESS = "in_progress"  # Đang thực hiện
    REVIEW = "review"            # Đã trình, đang xem xét/hoàn thiện
    DONE = "done"                # Đã hoàn thành


class TaskTypeEnum(str, Enum):
    """Loại nhiệm vụ công tác — độc lập với độ mật"""
    THUONG_XUYEN = "thuong_xuyen"  # Nhiệm vụ thường xuyên theo chức năng
    DOT_XUAT = "dot_xuat"          # Nhiệm vụ đột xuất, phát sinh
    CHUYEN_DE = "chuyen_de"        # Nhiệm vụ theo chuyên đề, kế hoạch riêng
    PHOI_HOP = "phoi_hop"          # Nhiệm vụ phối hợp giữa các đơn vị


class ClassificationEnum(str, Enum):
    """
    Độ mật của nhiệm vụ, theo Luật Bảo vệ bí mật nhà nước 2018.

    QUAN TRỌNG: Hệ thống này KHÔNG lưu nội dung thuộc phạm vi bí mật nhà nước.
    Với nhiệm vụ có độ mật, hệ thống chỉ lưu mã hiệu, tên gọi quy ước, điểm,
    thời hạn và số hiệu hồ sơ gốc; nội dung thật được quản lý theo chế độ mật
    tại đơn vị. Xem thêm ghi chú ở models/security_policy.py.
    """
    THUONG = "thuong"        # Không thuộc danh mục bí mật nhà nước
    MAT = "mat"              # Mật
    TOI_MAT = "toi_mat"      # Tối mật
    TUYET_MAT = "tuyet_mat"  # Tuyệt mật


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
    short_name: Optional[str] = None
    description: Optional[str] = None
    # Hệ lực lượng (theo tài liệu: xây dựng Danh mục nhiệm vụ theo hệ lực lượng)
    force_system: Optional[str] = None
    level: DepartmentLevelEnum = DepartmentLevelEnum.PHONG
    parent_id: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    force_system: Optional[str] = None
    level: Optional[DepartmentLevelEnum] = None
    parent_id: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class DepartmentGroupStats(BaseModel):
    """Phân bố cán bộ theo nhóm xếp loại KPI"""
    group_1: int = 0
    group_2: int = 0
    group_3: int = 0


class DepartmentNode(DepartmentResponse):
    """Một nút trong cây cơ cấu tổ chức, kèm số liệu tổng hợp"""
    children: List["DepartmentNode"] = []
    # Số cán bộ trực thuộc trực tiếp / gồm cả đơn vị cấp dưới
    member_count: int = 0
    total_member_count: int = 0
    # KPI tập thể của kỳ gần nhất đã xác định
    collective_kpi: Optional[float] = None
    collective_kpi_group: Optional[str] = None
    group_stats: DepartmentGroupStats = Field(default_factory=DepartmentGroupStats)


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
    # Số hiệu Công an nhân dân
    service_number: Optional[str] = None
    # Cấp độ tiếp cận tài liệu: 0 Thường · 1 Mật · 2 Tối mật · 3 Tuyệt mật
    clearance_level: int = Field(default=0, ge=0, le=3)
    # Định mức tổng điểm nhiệm vụ có thể đảm nhận trong một kỳ,
    # dùng để tính tình trạng sẵn sàng nhận nhiệm vụ
    capacity_points: int = Field(default=300, ge=1)
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
    service_number: Optional[str] = None
    clearance_level: Optional[int] = Field(default=None, ge=0, le=3)
    capacity_points: Optional[int] = Field(default=None, ge=1)
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

    Với nhiệm vụ có độ mật, chỉ lưu thông tin quản lý phục vụ tính điểm;
    nội dung nghiệp vụ nằm ở hồ sơ gốc (xem models/security_policy.py).
    """
    # Mã hiệu nhiệm vụ, VD: NV-2026-07-0042 (máy chủ tự sinh nếu bỏ trống)
    code: Optional[str] = None
    title: str
    description: Optional[str] = None

    # Phân loại — hai trục độc lập
    task_type: TaskTypeEnum = TaskTypeEnum.THUONG_XUYEN
    classification: ClassificationEnum = ClassificationEnum.THUONG

    # Với nhiệm vụ có độ mật: số hiệu và nơi lưu hồ sơ gốc ngoài hệ thống
    file_reference: Optional[str] = None
    file_location: Optional[str] = None

    # Liên kết tới mục trong Danh mục nhiệm vụ (để lấy điểm và nhóm độ phức tạp)
    catalog_item_id: Optional[str] = None
    complexity_group: Optional[int] = Field(default=None, ge=1, le=3)
    # Sản phẩm công việc đầu ra
    product: TaskProductEnum = TaskProductEnum.KHAC
    # Điểm của công việc được giao theo Danh mục (thang 100)
    kpi_point: int = Field(default=0, ge=0, le=100)
    # Số lượng sản phẩm được giao / đã hoàn thành
    quantity_assigned: int = Field(default=1, ge=0)
    quantity_completed: int = Field(default=0, ge=0)

    # Giao việc
    assigned_to: Optional[str] = None
    co_assignees: List[str] = []          # Cán bộ phối hợp thực hiện
    assigned_by: Optional[str] = None     # Người giao nhiệm vụ
    assigned_at: Optional[datetime] = None
    assigned_basis: Optional[str] = None  # Căn cứ giao (VD: Kế hoạch số 12/KH-BCA)

    # Đơn vị chủ trì và phối hợp
    department_id: Optional[str] = None
    support_department_ids: List[str] = []

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
    task_type: Optional[TaskTypeEnum] = None
    classification: Optional[ClassificationEnum] = None
    file_reference: Optional[str] = None
    file_location: Optional[str] = None
    catalog_item_id: Optional[str] = None
    complexity_group: Optional[int] = Field(default=None, ge=1, le=3)
    product: Optional[TaskProductEnum] = None
    kpi_point: Optional[int] = Field(default=None, ge=0, le=100)
    quantity_assigned: Optional[int] = Field(default=None, ge=0)
    quantity_completed: Optional[int] = Field(default=None, ge=0)
    assigned_to: Optional[str] = None
    co_assignees: Optional[List[str]] = None
    assigned_basis: Optional[str] = None
    department_id: Optional[str] = None
    support_department_ids: Optional[List[str]] = None
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
    assigned_by_name: Optional[str] = None
    # True khi máy chủ đã loại bỏ trường nhạy cảm do thiếu cấp độ tiếp cận
    is_redacted: bool = False

    class Config:
        populate_by_name = True


# ================= TÌNH TRẠNG CÔNG TÁC CỦA CÁN BỘ =================

class WorkloadStatusEnum(str, Enum):
    """Tình trạng sẵn sàng nhận nhiệm vụ, tính theo điểm đang đảm nhận / định mức"""
    SAN_SANG = "san_sang"      # < 50% định mức
    DANG_LAM = "dang_lam"      # 50% – dưới 85%
    GAN_DAY = "gan_day"        # 85% – 100%
    QUA_TAI = "qua_tai"        # > 100%


class EmployeeProfile(BaseModel):
    """Hồ sơ công tác của một cán bộ trong một kỳ đánh giá"""
    id: str
    name: str
    username: str
    email: Optional[str] = None
    role: RoleEnum
    position: Optional[str] = None
    rank: Optional[str] = None
    service_number: Optional[str] = None
    clearance_level: int = 0
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    is_commander: bool = False

    period_month: int
    period_year: int

    # Tải việc
    capacity_points: int
    open_points: int = 0            # Điểm của nhiệm vụ chưa hoàn thành
    workload_percent: float = 0.0
    workload_status: WorkloadStatusEnum = WorkloadStatusEnum.SAN_SANG

    # Thống kê nhiệm vụ trong kỳ
    tasks_assigned: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0
    tasks_overdue: int = 0
    points_assigned: int = 0
    points_completed: int = 0
    classified_tasks: int = 0

    # Chất lượng, tiến độ
    total_revisions: int = 0
    total_reminders: int = 0

    # KPI
    latest_kpi: Optional[float] = None
    latest_kpi_group: Optional[str] = None
    yearly_avg_kpi: Optional[float] = None
    kpi_history: List[dict] = []


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


# DepartmentNode tự tham chiếu (children) nên cần dựng lại sau khi định nghĩa xong
DepartmentNode.model_rebuild()
