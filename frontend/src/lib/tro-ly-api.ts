import api from './api';

/**
 * Client cho trợ lý hội thoại.
 *
 * Tách khỏi ai-api.ts đúng như backend tách services/tro_ly khỏi services/ai:
 * 04 mô hình ra quyết định chạy tại chỗ, còn trợ lý hội thoại có gọi ra ngoài.
 */

export interface DieuKhoan {
  id: string;
  title: string;
  source: string;
  text: string;
}

export interface TraLoiTroLy {
  tra_loi: string;
  dieu_khoan: DieuKhoan[];
  cong_cu_da_dung: string[];
  /** 'llm' = có mô hình ngôn ngữ · 'tai_cho' = máy tra cứu tại chỗ */
  che_do: 'llm' | 'tai_cho';
  ghi_chu: string | null;
}

export interface LuotTruoc {
  vai: 'user' | 'model';
  text: string;
}

/** Nhãn tiếng Việt cho công cụ, để hiện cho người dùng biết dữ liệu lấy từ đâu */
export const NHAN_CONG_CU: Record<string, string> = {
  tra_cuu_huong_dan: 'Hướng dẫn 20-HD/ĐUCA',
  nhiem_vu: 'Nhiệm vụ công tác',
  ket_qua_kpi: 'Kết quả KPI',
  tong_quan_don_vi: 'Tổng quan đơn vị',
  can_bo_can_luu_y: 'Danh sách cán bộ',
};

export const troLyApi = {
  hoi: async (cau_hoi: string, lich_su: LuotTruoc[] = []) => {
    const res = await api.post<TraLoiTroLy>('/tro-ly/hoi', { cau_hoi, lich_su });
    return res.data;
  },

  trangThai: async () => {
    const res = await api.get<{ che_do: 'llm' | 'tai_cho'; mo_ta: string }>('/tro-ly/trang-thai');
    return res.data;
  },
};
