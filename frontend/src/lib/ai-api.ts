import api from './api';

/**
 * Client cho các mô hình hỗ trợ ra quyết định.
 *
 * Tất cả chạy tại chỗ trong backend, không gọi dịch vụ bên ngoài.
 * Mô hình chỉ gợi ý và cảnh báo — không quyết định điểm KPI.
 */

// ===== Mô hình 1: Gợi ý phân công =====

export interface AssigneeSuggestion {
  id: string;
  name: string;
  rank_position: string;
  clearance_level: number;
  score: number;
  workload_percent: number;
  open_points: number;
  capacity_points: number;
  avg_revision: number;
  avg_reminder: number;
  tasks_overdue: number;
  recent_kpi?: number;
  reasons: string[];
  score_breakdown: Record<string, number>;
}

/**
 * Nhãn 5 thành phần của công thức gợi ý phân công.
 *
 * Khoá phải trùng với TRONG_SO trong backend/services/ai/assignment.py — có test
 * khoá lại, vì lệch khoá thì thanh thành phần lặng lẽ mất một cột chứ không báo lỗi.
 */
export const NHAN_THANH_PHAN: Record<string, string> = {
  du_dia_tai_viec: 'Dư địa tải việc',
  chat_luong_lich_su: 'Chất lượng lịch sử',
  tien_do_lich_su: 'Tiến độ lịch sử',
  khong_qua_han: 'Không tồn việc quá hạn',
  kpi_gan_nhat: 'KPI gần nhất',
};

export interface ExcludedOfficer {
  id: string;
  name: string;
  rank_position: string;
  reason_code: 'thieu_cap_do_tiep_can' | 'qua_tai';
  reason: string;
}

export interface AssignmentResult {
  suggested: AssigneeSuggestion[];
  excluded: ExcludedOfficer[];
  total_considered: number;
  required_clearance: number;
  weights: Record<string, number>;
  explanation: string;
}

// ===== Mô hình 2: Cảnh báo sớm =====

export interface OfficerRisk {
  officer_id: string;
  name: string;
  rank_position: string;
  department_id?: string;
  probability: number;
  tasks_total: number;
  tasks_done: number;
  tasks_overdue: number;
  recent_kpi?: number;
  reasons: string[];
}

export interface TaskRisk {
  task_id: string;
  code?: string;
  title: string;
  classification: string;
  assignee_name?: string;
  deadline?: string;
  days_left?: number;
  reminder_count: number;
  revision_count: number;
  probability: number;
  reasons: string[];
}

export interface RiskResult<T> {
  usable: boolean;
  reason?: string;
  auc?: number;
  threshold?: number;
  items: T[];
  explanation?: string;
}

// ===== Mô hình 3: Phát hiện chấm hình thức =====

export interface AnomalyFlag {
  severity: 'cao' | 'trung_binh' | 'thap';
  code: string;
  title: string;
  target: string;
  evidence: string;
  suggestion: string;
  department_id?: string;
}

export interface AnomalyResult {
  period_month: number;
  period_year: number;
  total_evaluations: number;
  departments_reviewed: number;
  flags: AnomalyFlag[];
  summary: { cao: number; trung_binh: number; thap: number };
  explanation: string;
}

export const SEVERITY_LABELS: Record<string, string> = {
  cao: 'Cần rà soát ngay',
  trung_binh: 'Nên xem lại',
  thap: 'Ghi nhận',
};

export const SEVERITY_COLORS: Record<string, string> = {
  cao: 'bg-crimson-100 text-crimson-800 border-crimson-300',
  trung_binh: 'bg-gold-100 text-gold-700 border-gold-300',
  thap: 'bg-navy-100 text-navy-700 border-navy-300',
};

// ===== Mô hình 4: Tra cứu Hướng dẫn =====

export interface GuidelineClause {
  id: string;
  title: string;
  source: string;
  text: string;
  match_score?: number;
}

export interface GuidelineAnswer {
  question: string;
  rule_answer: {
    question_understood: string;
    answer: string;
    value_percent: number | null;
    detail: string;
    clause_id: string;
  } | null;
  clauses: GuidelineClause[];
  explanation: string;
  source_document: string;
  precision_note: string;
}

// ===== Sổ đăng ký mô hình =====

export interface DacTrungMoHinh {
  ten: string;
  he_so: number;
  khi_cao: string;
  khi_thap: string;
}

export interface ChatLuongMoHinh {
  usable: boolean | null;
  reason: string | null;
  auc: number | null;
  n_samples: number | null;
  n_positive: number | null;
  confusion: { tn: number; fp: number; fn: number; tp: number } | null;
  coefficients: Record<string, number>;
  dac_trung: DacTrungMoHinh[];
  trained_at: string | null;
}

export interface MoHinh {
  ma: string;
  so: number;
  ten: string;
  muc_dich: string;
  thuat_toan: string;
  vi_sao: string;
  noi_chay: 'tai_cho' | 'goi_ra_ngoai';
  ma_nguon: string;
  dung_o: { nhan: string; duong_dan: string }[];
  tham_so: { nhan: string; gia_tri: string }[];
  chat_luong: ChatLuongMoHinh | null;
}

export interface SoDangKyMoHinh {
  mo_hinh: MoHinh[];
  auc_threshold: number;
  so_mau_toi_thieu: number;
  ranh_gioi: { tieu_de: string; noi_dung: string }[];
  ghi_chu_du_lieu_mau: string;
}

export interface TheHoTroAI {
  ma: string;
  nhan: string;
  /** Chuỗi chứ không phải số: có thẻ nêu trạng thái ("Sẵn sàng") chứ không đếm. */
  so: string;
  phu: string;
  duong_dan: string | null;
}

export const aiApi = {
  suggestAssignee: async (params: {
    classification?: string;
    complexity_group?: number;
    product?: string;
    department_id?: string;
    limit?: number;
  }) => {
    const res = await api.get<AssignmentResult>('/ai/suggest-assignee', { params });
    return res.data;
  },

  officerRisk: async (params?: {
    department_id?: string; period_month?: number; period_year?: number; threshold?: number;
  }) => {
    const res = await api.get<RiskResult<OfficerRisk>>('/ai/risk/officers', { params });
    return res.data;
  },

  taskRisk: async (params?: {
    department_id?: string; period_month?: number; period_year?: number; threshold?: number;
  }) => {
    const res = await api.get<RiskResult<TaskRisk>>('/ai/risk/tasks', { params });
    return res.data;
  },

  anomalies: async (params: {
    period_month: number; period_year: number; department_id?: string;
  }) => {
    const res = await api.get<AnomalyResult>('/ai/anomalies', { params });
    return res.data;
  },

  searchGuideline: async (q: string) => {
    const res = await api.get<GuidelineAnswer>('/ai/guideline/search', { params: { q } });
    return res.data;
  },

  allClauses: async () => {
    const res = await api.get<GuidelineClause[]>('/ai/guideline/clauses');
    return res.data;
  },

  moHinh: async () => {
    const res = await api.get<SoDangKyMoHinh>('/ai/models');
    return res.data;
  },

  tomTat: async () => {
    const res = await api.get<{ the: TheHoTroAI[] }>('/ai/tom-tat');
    return res.data.the;
  },

  retrain: async () => {
    const res = await api.post('/ai/retrain');
    return res.data;
  },
};
