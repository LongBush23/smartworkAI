import api from './api';

export interface KPICatalogItem {
  id: string;
  task_name: string;
  category: string;
  complexity_group: 1 | 2 | 3;
  kpi_point: number;
  description?: string;
}

export interface KPICatalog {
  id: string;
  department_id: string;
  period_year: number;
  name: string;
  status: 'draft' | 'approved';
  items: KPICatalogItem[];
  approved_by?: string;
  approved_at?: string;
}

export interface TaskKPIScore {
  task_id: string;
  catalog_item_id?: string;
  task_name: string;
  kpi_point: number;
  is_completed: boolean;
  quality_tier: string;
  timeline_tier: string;
  note?: string;
}

export interface KPIEvaluation {
  id: string;
  evaluation_type: 'individual' | 'collective';
  target_id: string;
  target_name: string;
  target_role?: string;
  department_id: string;
  period_type: 'monthly' | 'quarterly' | 'yearly';
  period_month?: number;
  period_year: number;
  self_evaluation?: any;
  review?: any;
  approval?: any;
  general_criteria?: any;
  overall_status: 'draft' | 'self_evaluating' | 'reviewing' | 'approved' | 'rejected';
}

export interface KPIRankingItem {
  target_id: string;
  target_name: string;
  department_name?: string;
  role?: string;
  kpi_score: number;
  kpi_group: string;
  score_A: number;
  score_B: number;
  score_C: number;
  score_D?: number;
  total_E?: number;
  total_final_score?: number;
}

export interface CriteriaSubItem {
  id: string;
  name: string;
  max_score: number;
}

export interface CriteriaItem {
  id: string;
  name: string;
  max_score: number;
  sub_criteria?: CriteriaSubItem[];
}

export interface CriteriaTemplate {
  id: string;
  type: 'collective' | 'leader' | 'staff';
  name: string;
  total_max_score: number;
  criteria: CriteriaItem[];
}

// Nhóm xếp loại KPI theo văn bản
export const KPI_GROUP_LABELS: Record<string, string> = {
  group_1: 'Đáp ứng tốt yêu cầu nhiệm vụ',
  group_2: 'Đáp ứng yêu cầu nhiệm vụ',
  group_3: 'Chưa đáp ứng yêu cầu nhiệm vụ',
};

export const KPI_GROUP_COLORS: Record<string, string> = {
  group_1: 'text-green-700 bg-green-100 border-green-200',
  group_2: 'text-blue-700 bg-blue-100 border-blue-200',
  group_3: 'text-red-700 bg-red-100 border-red-200',
};

// Nhãn tiếng Việt cho thẩm quyền của cán bộ
export const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị hệ thống',
  director: 'Lãnh đạo đơn vị',
  leader: 'Lãnh đạo, chỉ huy',
  staff: 'Cán bộ, chiến sĩ',
};

// Nhóm độ phức tạp công việc theo thang 100 điểm
export const COMPLEXITY_GROUP_LABELS: Record<number, string> = {
  1: 'Nhóm 1 (0 – dưới 50 điểm)',
  2: 'Nhóm 2 (50 – dưới 70 điểm)',
  3: 'Nhóm 3 (70 – 100 điểm)',
};

// ===== Mức điểm chất lượng (B) và tiến độ (C) =====

export type QualityTier = 'excellent' | 'good' | 'fair_1' | 'fair_2_4' | 'poor_5_6' | 'fail_7';
export type TimelineTier = 'ahead' | 'on_time' | 'late_1' | 'late_2' | 'late_3' | 'fail_4';

export const QUALITY_PERCENT: Record<QualityTier, number> = {
  excellent: 1.20, good: 1.00, fair_1: 0.75, fair_2_4: 0.50, poor_5_6: 0.25, fail_7: 0,
};

export const TIMELINE_PERCENT: Record<TimelineTier, number> = {
  ahead: 1.20, on_time: 1.00, late_1: 0.75, late_2: 0.50, late_3: 0.25, fail_4: 0,
};

/**
 * Suy ra mức điểm chất lượng từ số lần phải hoàn thiện, chỉnh sửa.
 * 0 lần → đảm bảo (100%); 1 lần → ≤75%; 2-4 lần → ≤50%;
 * 5-6 lần → ≤25%; từ 7 lần → không tính điểm.
 */
export function qualityTierFromRevisions(revisionCount: number): QualityTier {
  if (revisionCount <= 0) return 'good';
  if (revisionCount === 1) return 'fair_1';
  if (revisionCount <= 4) return 'fair_2_4';
  if (revisionCount <= 6) return 'poor_5_6';
  return 'fail_7';
}

/**
 * Suy ra mức điểm tiến độ từ số lần bị nhắc nhở.
 * 0 lần → đúng tiến độ (100%); 1 lần → ≤75%;
 * 2 lần → ≤50%; 3 lần → ≤25%; từ 4 lần → không tính điểm.
 */
export function timelineTierFromReminders(reminderCount: number): TimelineTier {
  if (reminderCount <= 0) return 'on_time';
  if (reminderCount === 1) return 'late_1';
  if (reminderCount === 2) return 'late_2';
  if (reminderCount === 3) return 'late_3';
  return 'fail_4';
}

export const kpiApi = {
  // Catalog endpoints
  getCatalogs: async (params?: { department_id?: string; period_year?: number }) => {
    const res = await api.get<KPICatalog[]>('/kpi/catalog', { params });
    return res.data;
  },
  
  createCatalog: async (data: any) => {
    const res = await api.post<KPICatalog>('/kpi/catalog', data);
    return res.data;
  },
  
  approveCatalog: async (id: string) => {
    const res = await api.put(`/kpi/catalog/${id}/approve`);
    return res.data;
  },

  // Evaluation endpoints
  createEvaluation: async (data: any) => {
    const res = await api.post<KPIEvaluation>('/kpi/evaluations', data);
    return res.data;
  },
  
  getEvaluations: async (params?: { target_id?: string; department_id?: string; period_type?: string; period_month?: number; period_year?: number }) => {
    const res = await api.get<KPIEvaluation[]>('/kpi/evaluations', { params });
    return res.data;
  },
  
  getEvaluation: async (id: string) => {
    const res = await api.get<KPIEvaluation>(`/kpi/evaluations/${id}`);
    return res.data;
  },
  
  submitSelfEvaluation: async (id: string, data: any) => {
    const res = await api.put(`/kpi/evaluations/${id}/self-evaluate`, data);
    return res.data;
  },
  
  submitReview: async (id: string, data: any) => {
    const res = await api.put(`/kpi/evaluations/${id}/review`, data);
    return res.data;
  },
  
  approveEvaluation: async (id: string) => {
    const res = await api.put(`/kpi/evaluations/${id}/approve`);
    return res.data;
  },
  
  submitGeneralCriteria: async (id: string, data: any) => {
    const res = await api.put(`/kpi/evaluations/${id}/general-criteria`, data);
    return res.data;
  },

  // Ranking endpoints
  getRanking: async (params?: { department_id?: string; period_month?: number; period_year?: number }) => {
    const res = await api.get<KPIRankingItem[]>('/kpi/scores/ranking', { params });
    return res.data;
  },

  // Criteria templates (Phụ lục tiêu chí chung)
  getCriteriaTemplate: async (type: 'collective' | 'leader' | 'staff') => {
    const res = await api.get<CriteriaTemplate>(`/kpi/criteria-templates?criteria_type=${type}`);
    return res.data;
  },

  getAllCriteriaTemplates: async () => {
    const res = await api.get<CriteriaTemplate[]>('/kpi/criteria-templates');
    return res.data;
  },
};
