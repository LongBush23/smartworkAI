import api from './api';

export type TaskStatus = 'assigned' | 'in_progress' | 'review' | 'done';

export type TaskProduct =
  | 'cong_van' | 'bao_cao' | 'to_trinh' | 'thong_tu'
  | 'quy_dinh' | 'ke_hoach' | 'de_an' | 'khac';

export type TaskType = 'thuong_xuyen' | 'dot_xuat' | 'chuyen_de' | 'phoi_hop';
export type Classification = 'thuong' | 'mat' | 'toi_mat' | 'tuyet_mat';

export interface Task {
  _id: string;
  code?: string;
  title: string;
  description?: string;
  task_type: TaskType;
  classification: Classification;
  file_reference?: string;
  file_location?: string;
  catalog_item_id?: string;
  complexity_group?: 1 | 2 | 3;
  product: TaskProduct;
  kpi_point: number;
  quantity_assigned: number;
  quantity_completed: number;
  assigned_to?: string;
  co_assignees: string[];
  assigned_by?: string;
  assigned_at?: string;
  assigned_basis?: string;
  department_id?: string;
  support_department_ids: string[];
  status: TaskStatus;
  deadline: string;
  actual_end?: string;
  revision_count: number;
  reminder_count: number;
  period_month?: number;
  period_year?: number;
  attachments: string[];
  assignee_name?: string;
  department_name?: string;
  assigned_by_name?: string;
  /** Máy chủ đã loại bỏ trường nhạy cảm do người xem thiếu cấp độ tiếp cận */
  is_redacted: boolean;
}

export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  thuong_xuyen: 'Thường xuyên',
  dot_xuat: 'Đột xuất',
  chuyen_de: 'Chuyên đề',
  phoi_hop: 'Phối hợp',
};

export const TASK_TYPE_COLORS: Record<TaskType, string> = {
  thuong_xuyen: 'bg-navy-50 text-navy-700 border-navy-200',
  dot_xuat: 'bg-crimson-50 text-crimson-700 border-crimson-200',
  chuyen_de: 'bg-gold-50 text-gold-700 border-gold-200',
  phoi_hop: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

/** Độ mật theo Luật Bảo vệ bí mật nhà nước 2018 */
export const CLASSIFICATION_LABELS: Record<Classification, string> = {
  thuong: 'Thường',
  mat: 'MẬT',
  toi_mat: 'TỐI MẬT',
  tuyet_mat: 'TUYỆT MẬT',
};

export const CLASSIFICATION_RANK: Record<Classification, number> = {
  thuong: 0, mat: 1, toi_mat: 2, tuyet_mat: 3,
};

export const CLASSIFICATION_COLORS: Record<Classification, string> = {
  thuong: 'bg-gray-100 text-gray-600 border-gray-200',
  mat: 'bg-gold-100 text-gold-700 border-gold-300',
  toi_mat: 'bg-orange-100 text-orange-800 border-orange-300',
  tuyet_mat: 'bg-crimson-100 text-crimson-800 border-crimson-300',
};

export const CLEARANCE_LABELS: Record<number, string> = {
  0: 'Tài liệu thường',
  1: 'Đến độ Mật',
  2: 'Đến độ Tối mật',
  3: 'Đến độ Tuyệt mật',
};

export type WorkloadStatus = 'san_sang' | 'dang_lam' | 'gan_day' | 'qua_tai';

export const WORKLOAD_LABELS: Record<WorkloadStatus, string> = {
  san_sang: 'Sẵn sàng nhận nhiệm vụ',
  dang_lam: 'Đang thực hiện',
  gan_day: 'Gần đầy định mức',
  qua_tai: 'Quá tải',
};

export const WORKLOAD_COLORS: Record<WorkloadStatus, string> = {
  san_sang: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  dang_lam: 'bg-navy-100 text-navy-700 border-navy-300',
  gan_day: 'bg-gold-100 text-gold-700 border-gold-300',
  qua_tai: 'bg-crimson-100 text-crimson-800 border-crimson-300',
};

export const WORKLOAD_BAR: Record<WorkloadStatus, string> = {
  san_sang: 'bg-emerald-500',
  dang_lam: 'bg-navy-500',
  gan_day: 'bg-gold-500',
  qua_tai: 'bg-crimson-600',
};

export interface EmployeeProfile {
  id: string;
  name: string;
  username: string;
  email?: string;
  role: string;
  position?: string;
  rank?: string;
  service_number?: string;
  clearance_level: number;
  department_id?: string;
  department_name?: string;
  is_commander: boolean;
  period_month: number;
  period_year: number;
  capacity_points: number;
  open_points: number;
  workload_percent: number;
  workload_status: WorkloadStatus;
  tasks_assigned: number;
  tasks_completed: number;
  tasks_in_progress: number;
  tasks_overdue: number;
  points_assigned: number;
  points_completed: number;
  classified_tasks: number;
  total_revisions: number;
  total_reminders: number;
  latest_kpi?: number;
  latest_kpi_group?: string;
  yearly_avg_kpi?: number;
  kpi_history: { period_month: number; kpi_score: number; kpi_group: string }[];
}

/** Tóm tắt một cán bộ trong danh sách đơn vị */
export interface DepartmentMember {
  id: string;
  name: string;
  role: string;
  position?: string;
  rank?: string;
  clearance_level: number;
  capacity_points: number;
  open_points: number;
  workload_percent: number;
  workload_status: WorkloadStatus;
  tasks_assigned: number;
  tasks_completed: number;
  tasks_overdue: number;
  classified_tasks: number;
  total_revisions: number;
  total_reminders: number;
  latest_kpi?: number;
  latest_kpi_group?: string;
  yearly_avg_kpi?: number;
}

export interface DepartmentNode {
  _id: string;
  name: string;
  short_name?: string;
  description?: string;
  force_system?: string;
  level: 'bo' | 'cuc' | 'phong' | 'doi';
  parent_id?: string;
  children: DepartmentNode[];
  member_count: number;
  total_member_count: number;
  collective_kpi?: number;
  collective_kpi_group?: string;
  group_stats: { group_1: number; group_2: number; group_3: number };
}

export const DEPT_LEVEL_LABELS: Record<string, string> = {
  bo: 'Cơ quan Bộ',
  cuc: 'Cục / Công an tỉnh',
  phong: 'Phòng / Trung đoàn',
  doi: 'Đội / Tiểu đoàn',
};

export const PRODUCT_LABELS: Record<TaskProduct, string> = {
  cong_van: 'Công văn',
  bao_cao: 'Báo cáo',
  to_trinh: 'Tờ trình',
  thong_tu: 'Thông tư',
  quy_dinh: 'Quy định',
  ke_hoach: 'Kế hoạch',
  de_an: 'Đề án',
  khac: 'Sản phẩm khác',
};

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  assigned: 'Đã giao',
  in_progress: 'Đang thực hiện',
  review: 'Đang hoàn thiện',
  done: 'Đã hoàn thành',
};

export const TASK_STATUS_COLORS: Record<TaskStatus, string> = {
  assigned: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  review: 'bg-amber-100 text-amber-700',
  done: 'bg-green-100 text-green-700',
};

export const taskApi = {
  list: async (params?: {
    assignee_id?: string; department_id?: string; status?: string;
    task_type?: string; classification?: string;
    period_month?: number; period_year?: number;
  }) => {
    const res = await api.get<Task[]>('/tasks/', { params });
    return res.data;
  },

  get: async (id: string) => {
    const res = await api.get<Task>(`/tasks/${id}`);
    return res.data;
  },

  /** Hồ sơ công tác của cán bộ trong kỳ */
  employeeProfile: async (id: string, params?: { period_month?: number; period_year?: number }) => {
    const res = await api.get<EmployeeProfile>(`/employees/${id}/profile`, { params });
    return res.data;
  },

  /** Cây cơ cấu tổ chức kèm số liệu tổng hợp */
  departmentTree: async (params?: { period_month?: number; period_year?: number }) => {
    const res = await api.get<DepartmentNode[]>('/departments/tree', { params });
    return res.data;
  },

  /** Cán bộ của một đơn vị kèm tải việc và KPI — một lượt truy vấn duy nhất */
  departmentMembers: async (id: string, params?: { period_month?: number; period_year?: number }) => {
    const res = await api.get<DepartmentMember[]>(`/departments/${id}/members`, { params });
    return res.data;
  },

  create: async (data: Partial<Task>) => {
    const res = await api.post<Task>('/tasks/', data);
    return res.data;
  },

  update: async (id: string, data: Partial<Task>) => {
    const res = await api.put(`/tasks/${id}`, data);
    return res.data;
  },

  remove: async (id: string) => {
    const res = await api.delete(`/tasks/${id}`);
    return res.data;
  },

  /** Nhắc nhở tiến độ — làm giảm mức điểm tiến độ (C) */
  remind: async (id: string) => {
    const res = await api.post<{ reminder_count: number }>(`/tasks/${id}/remind`);
    return res.data;
  },

  /** Yêu cầu hoàn thiện, chỉnh sửa — làm giảm mức điểm chất lượng (B) */
  requestRevision: async (id: string) => {
    const res = await api.post<{ revision_count: number }>(`/tasks/${id}/request-revision`);
    return res.data;
  },
};
