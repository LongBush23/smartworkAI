import { useEffect, useState } from 'react';

/**
 * Chế độ "Xem dấu vết AI".
 *
 * VÌ SAO CÓ CHẾ ĐỘ NÀY
 * --------------------
 * Năm mô hình của hệ thống đều nằm chìm trong quy trình nghiệp vụ: khối cảnh
 * báo trên Trang chủ, danh sách dấu hiệu ở trang rà soát, gợi ý cán bộ trong
 * hộp nhiệm vụ. Người dùng thấy kết quả nhưng không biết đó là mô hình tính ra,
 * nên công sức làm mô hình không toát ra được.
 *
 * Bật chế độ này thì mọi khối do mô hình sinh ra được viền lại và gắn số hiệu,
 * bấm vào nhãn là sang đúng thẻ mô hình đó ở trang Mô hình hỗ trợ ra quyết định.
 * Tắt đi thì giao diện trở lại y nguyên — đây là lớp phủ để xem và để chụp ảnh
 * minh hoạ, không phải giao diện làm việc hằng ngày.
 */

const KHOA = 'dau_vet_ai';

// Đổi trạng thái ở một chỗ (nút trên thanh tiêu đề) nhưng phải làm mọi khung mô
// hình ở khắp cây React vẽ lại. Dùng sự kiện của window thay vì React context:
// khung mô hình nằm rải ở nhiều trang nạp theo nhu cầu, bọc context quanh tất cả
// chỉ để truyền một giá trị boolean là quá nặng tay.
const SU_KIEN = 'dauVetAIThayDoi';

/**
 * Mã mô hình đã gắn vào giao diện → số hiệu và tên gọi để in trên nhãn.
 *
 * Chỉ giữ đúng hai thứ cần cho cái nhãn. Mô tả đầy đủ, thuật toán, tham số và
 * chất lượng đều lấy từ sổ đăng ký ở backend (GET /api/ai/models) để không có
 * hai bản mô tả lệch nhau. Có test đối chiếu số hiệu và tên với sổ đăng ký.
 */
export const MO_HINH_DA_GAN: Record<string, { so: number; ten: string }> = {
  nguy_co_nhom_3: { so: 1, ten: 'Nguy cơ rơi Nhóm 3' },
  nguy_co_tre_han: { so: 2, ten: 'Nguy cơ nhiệm vụ trễ hạn' },
  cham_hinh_thuc: { so: 3, ten: 'Phát hiện chấm điểm hình thức' },
  goi_y_phan_cong: { so: 4, ten: 'Gợi ý phân công' },
  tra_cuu_huong_dan: { so: 5, ten: 'Tra cứu Hướng dẫn 20-HD/ĐUCA' },
  tro_ly_hoi_thoai: { so: 6, ten: 'Trợ lý hội thoại' },
};

export const dangXemDauVet = () => localStorage.getItem(KHOA) === 'true';

export const datXemDauVet = (bat: boolean) => {
  localStorage.setItem(KHOA, String(bat));
  window.dispatchEvent(new Event(SU_KIEN));
};

/** Theo dõi trạng thái chế độ xem dấu vết. */
export const useDauVetAI = () => {
  const [bat, setBat] = useState(dangXemDauVet);

  useEffect(() => {
    const doi = () => setBat(dangXemDauVet());
    window.addEventListener(SU_KIEN, doi);
    // 'storage' để hai thẻ trình duyệt cùng mở không hiển thị khác nhau
    window.addEventListener('storage', doi);
    return () => {
      window.removeEventListener(SU_KIEN, doi);
      window.removeEventListener('storage', doi);
    };
  }, []);

  return bat;
};
