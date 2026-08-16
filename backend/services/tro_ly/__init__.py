"""
Trợ lý hội thoại — gói DUY NHẤT trong hệ thống được phép gọi dịch vụ AI bên ngoài.

════════════════════════════════════════════════════════════════════════════
VÌ SAO TÁCH RIÊNG KHỎI services/ai
════════════════════════════════════════════════════════════════════════════

`services/ai` chứa 04 mô hình ảnh hưởng tới cách lãnh đạo nhìn nhận cán bộ
(cảnh báo nguy cơ, phát hiện chấm hình thức, gợi ý phân công, tra cứu văn bản).
Nhóm đó giữ nguyên hai ràng buộc cứng: chạy hoàn toàn tại chỗ và không quyết
định điểm KPI. Có test quét mã khoá lại — KHÔNG được thêm thư viện mạng vào đó.

Trợ lý hội thoại là chuyện khác: nó không tính điểm, không xếp hạng ai, chỉ
diễn đạt lại dữ liệu người dùng vốn đã có quyền xem. Nên đặt ở gói riêng này,
với rào chắn riêng ghi ngay dưới đây.

════════════════════════════════════════════════════════════════════════════
BỐN RÀO CHẮN CỦA TRỢ LÝ — ĐỌC TRƯỚC KHI SỬA BẤT KỲ FILE NÀO Ở ĐÂY
════════════════════════════════════════════════════════════════════════════

1. CHỈ ĐỌC. Không công cụ nào được ghi vào cơ sở dữ liệu. Trợ lý không giao
   việc, không nhắc nhở, không chấm điểm, không đổi trạng thái hồ sơ.

2. KHÔNG QUYẾT ĐỊNH ĐIỂM KPI. Mọi con số về cách tính điểm phải lấy từ
   `services/ai/guideline` — tức từ chính hằng số của bộ máy chấm điểm — chứ
   không để mô hình ngôn ngữ tự suy ra. Mô hình chỉ diễn đạt lại.

3. KHÔNG BAO GIỜ GỬI NỘI DUNG NHIỆM VỤ CÓ ĐỘ MẬT RA NGOÀI. Hệ thống vốn đã
   không lưu nội dung mật, nhưng ngay cả tên gọi quy ước và mã hiệu cũng không
   được đưa vào lời nhắc. Nhiệm vụ có độ mật chỉ được đếm, không được kể tên.
   Xem `loc_mat()` trong cong_cu.py — mọi công cụ trả về nhiệm vụ đều phải đi
   qua hàm này.

4. PHẠM VI DỮ LIỆU ĐÚNG BẰNG PHÂN QUYỀN NGƯỜI HỎI. Cán bộ không giữ chức vụ
   chỉ đọc được dữ liệu của chính mình; lãnh đạo, chỉ huy đọc trong đơn vị mình
   phụ trách; quản trị hệ thống đọc toàn bộ. Quy tắc này lặp đúng theo
   `routers/tasks.py`. Công cụ nhận `nguoi_hoi` và tự áp phạm vi — không tin
   vào tham số do mô hình sinh ra.

════════════════════════════════════════════════════════════════════════════

Thiếu GEMINI_API_KEY thì trợ lý tự lui về máy tra cứu tại chỗ, không báo lỗi.
"""
