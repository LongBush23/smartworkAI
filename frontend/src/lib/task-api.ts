import api from './api';

export type TaskStatus = 'assigned' | 'in_progress' | 'review' | 'done';

export type TaskProduct =
  | 'cong_van' | 'bao_cao' | 'to_trinh' | 'thong_tu'
  | 'quy_dinh' | 'ke_hoach' | 'de_an' | 'khac';

export interface Task {
  _id: string;
  title: string;
  description?: string;
  catalog_item_id?: string;
  product: TaskProduct;
  kpi_point: number;
  quantity_assigned: number;
  quantity_completed: number;
  assigned_to?: string;
  department_id?: string;
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
}

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
    period_month?: number; period_year?: number;
  }) => {
    const res = await api.get<Task[]>('/tasks/', { params });
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
