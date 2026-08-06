"""
Các mô hình hỗ trợ ra quyết định trong Hệ thống Tính điểm KPI.

════════════════════════════════════════════════════════════════════════════
HAI RÀNG BUỘC BẤT DI BẤT DỊCH — ĐỌC TRƯỚC KHI SỬA BẤT KỲ FILE NÀO Ở ĐÂY
════════════════════════════════════════════════════════════════════════════

1. MÔ HÌNH KHÔNG ĐƯỢC QUYẾT ĐỊNH ĐIỂM KPI.

   Điểm A, B, C, D và cách phân nhóm là công thức trong Hướng dẫn số
   20-HD/ĐUCA — văn bản pháp quy. Nếu mô hình đề xuất điểm thì mất căn cứ
   pháp lý khi có khiếu nại.

   Cụ thể: KHÔNG module nào trong gói này được ghi vào
   `kpi_evaluations.approval`. Chỉ đọc dữ liệu, trả về gợi ý và cảnh báo.
   Người có thẩm quyền là người quyết định.

2. KHÔNG MỘT BYTE DỮ LIỆU NÀO RỜI HỆ THỐNG.

   Toàn bộ tính toán chạy tại chỗ. KHÔNG import `requests`, `httpx`,
   `openai`, `google.generativeai` hay bất kỳ thư viện gọi mạng nào trong
   gói này. Có test tự động kiểm điều này.

   Với nhiệm vụ có độ mật, mô hình chỉ dùng metadata (điểm, nhóm độ phức
   tạp, thời hạn, số lần sửa/nhắc) — không đụng tới nội dung. Xem
   `backend/models/security_policy.py`.

════════════════════════════════════════════════════════════════════════════

HỆ QUẢ VỀ KỸ THUẬT: ưu tiên mô hình GIẢI THÍCH ĐƯỢC. Cơ quan nhà nước không
chấp nhận hộp đen — mọi kết quả phải nêu được lý do. Vì vậy dùng công thức có
trọng số và hồi quy logistic, tránh mô hình phức tạp không diễn giải nổi.
Mọi phản hồi phải có trường mô tả lý do.
"""
