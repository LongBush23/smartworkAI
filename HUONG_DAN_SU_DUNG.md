# TÀI LIỆU HƯỚNG DẪN SỬ DỤNG SMARTWORK AI

Chào mừng bạn đến với **SmartWork AI** - Hệ thống Quản lý Công việc & Dự án thông minh được tích hợp Trợ lý Trí tuệ Nhân tạo (Gemini 2.5). Tài liệu này sẽ giúp bạn làm quen và khai thác tối đa sức mạnh của hệ thống.

---

## 1. Đăng nhập hệ thống

- Truy cập vào đường link trang web của công ty (Ví dụ: `https://smartwork-ai-3u7e.vercel.app`).
- Nhập **Tên đăng nhập** và **Mật khẩu** do Ban Quản trị cấp.
- *Lưu ý:* Hệ thống không có nút "Đăng ký" tự do. Mọi tài khoản đều phải được cấp phát nội bộ bởi tài khoản có quyền Quản trị viên (Admin) hoặc Trưởng phòng (Director).

### Danh sách các tài khoản Demo có sẵn để thử nghiệm:

**1. Cấp Quản trị tối cao (Admin)**
*Quyền cao nhất, xem được mọi thứ và quản lý nhân sự*
- **Tài khoản:** `admin` | **Mật khẩu:** `admin123`

**2. Cấp Trưởng phòng (Director)**
*Quản lý phòng ban, tạo dự án lớn, cấp tài khoản*
- **Tài khoản:** `director_tech`, `director_mkt`, `director_hr`, `director_finance` | **Mật khẩu:** `123456`

**3. Cấp Trưởng nhóm (Leader)**
*Chuyên tạo dự án con, giao việc cho nhân viên*
- **Tài khoản:** `leader1`, `leader2`, `leader3`, `leader4` | **Mật khẩu:** `123456`

**4. Cấp Nhân viên (Staff)**
*Chỉ xem được dự án mình tham gia, cập nhật tiến độ task*
- **Tài khoản:** `user0` đến `user19` (ví dụ: `user1`, `user15`) | **Mật khẩu:** `123456`

---

## 2. Giao diện Tổng quan (Dashboard)

Ngay sau khi đăng nhập, bạn sẽ được đưa đến trang Dashboard. Tại đây cung cấp bức tranh toàn cảnh về tiến độ công việc:
- **Thẻ Thống kê (Phía trên cùng):** Hiển thị nhanh số lượng Dự án đang chạy, Tổng số Nhân sự, và Tổng số Công việc (Tasks) chưa hoàn thành.
- **Biểu đồ Cột (Khối lượng công việc):** Cho biết nhân viên nào đang ôm nhiều việc nhất, giúp Trưởng nhóm cân bằng lại task.
- **Dự báo AI (Màu sắc):** Trí tuệ nhân tạo sẽ tự động đánh giá tiến độ của cả tổ chức dựa trên dữ liệu lịch sử và gán nhãn: **Đúng tiến độ (Màu Xanh)**, **Có nguy cơ trễ (Màu Vàng)**, hoặc **Trễ hạn (Màu Đỏ)**.
- **Phân loại Năng lực Nhân sự:** AI tự động phân tích và xếp loại nhân sự thành các nhóm Giỏi, Khá, Kém dựa vào tỷ lệ hoàn thành công việc và thời gian xử lý.

---

## 3. Quản lý Dự án (Projects)

Chỉ có vai trò **Leader (Nhóm trưởng)** trở lên mới có quyền tạo Dự án mới.
- **Xem Dự án:** Chọn mục `Dự án` bên menu trái. Tại đây liệt kê các dự án dưới dạng thẻ.
- **Thêm Dự án mới:** Bấm nút `+ Thêm Dự án`, điền Tên dự án, Mô tả, Ngày bắt đầu và Hạn chót. Sau đó chọn những nhân sự được phép tham gia vào dự án này.
- **AI Phân tích Dự án:** Bạn có thể bấm vào biểu tượng "Tia sét màu tím" (Phân tích AI) trên mỗi thẻ dự án. Trợ lý ảo sẽ lập tức đọc dữ liệu và đưa ra lời khuyên: *Liệu dự án có kịp deadline không? Khâu nào đang chậm?*

---

## 4. Bảng Công việc (Kanban Tasks)

Đây là nơi bạn thao tác nhiều nhất hàng ngày.
- **Giao diện Kanban:** Các công việc được chia thành 4 cột: `TODO` (Cần làm), `IN PROGRESS` (Đang làm), `REVIEW` (Chờ duyệt), `DONE` (Hoàn thành).
- **Kéo Thả (Drag & Drop):** Để chuyển trạng thái công việc, bạn chỉ cần dùng chuột (hoặc ngón tay trên điện thoại) nhấn giữ thẻ công việc và kéo sang cột tương ứng.
- **Chấm công (Log Time):** Bấm vào biểu tượng Đồng hồ trên mỗi thẻ công việc để khai báo số giờ bạn đã bỏ ra cho task đó.

> [!TIP]
> **Tính năng Đặc biệt: AI Phân công Nhiệm vụ**
> Khi bạn bấm tạo mới một Công việc, thay vì phải vắt óc suy nghĩ xem nên giao cho ai, hãy bấm nút **"Gợi ý Phân công bằng AI"**. Trí tuệ nhân tạo sẽ quét toàn bộ kỹ năng của nhân viên, kiểm tra xem ai đang rảnh rỗi và đề xuất 3 ứng cử viên phù hợp nhất cho công việc đó!

---

## 5. Trợ lý Ảo AI (Chatbox 24/7)

Góc dưới cùng bên phải màn hình luôn có một **Nút bong bóng màu xanh**. 
- Hãy bấm vào đó để mở cửa sổ trò chuyện với Trợ lý SmartWork AI (Sử dụng công nghệ Gemini 2.5 Flash mạnh mẽ).
- **Bạn có thể hỏi gì?**
  - *"Tóm tắt cho tôi tình hình dự án Website Bán hàng."*
  - *"Code Python của tôi bị lỗi SSL, giải thích nguyên nhân giúp tôi."*
  - *"Tôi là nhân viên mới, làm sao để tạo task?"*
- AI đã được lập trình để hiểu rõ cấu trúc công ty, nó sẽ gọi bạn bằng Tên và trả lời chuyên nghiệp, từ chối các câu hỏi ngoài lề không liên quan đến công việc.

---

## 6. Phân quyền và Quản lý Nhân sự (Dành cho Cấp Quản lý)

Hệ thống có 4 cấp bậc với quyền hạn tăng dần:
1. **Chuyên viên (Staff):** Chỉ thấy dự án mình tham gia, chỉ kéo thả được công việc của mình.
2. **Nhóm trưởng (Leader):** Được tạo Dự án, tạo Task, xem Yêu cầu tham gia.
3. **Trưởng phòng (Director):** Có thêm quyền truy cập menu `Nhân sự` để thêm, sửa, xóa nhân viên, đổi mật khẩu cho nhân viên.
4. **Quản trị viên (Admin):** Nắm toàn quyền, có thêm menu `Nhật ký kiểm toán (Audit Logs)` để theo dõi lịch sử ai đã thêm/xóa/sửa cái gì vào giờ nào, chống gian lận dữ liệu.

> [!IMPORTANT]
> - Nếu bạn sử dụng điện thoại di động, thanh menu bên trái sẽ được thu gọn vào biểu tượng **3 dấu gạch ngang (☰)** ở góc trên bên trái màn hình.
> - Hãy luôn tuân thủ việc Cập nhật trạng thái Task (Kéo thẻ sang DONE) để AI có dữ liệu chính xác đánh giá năng suất làm việc của bạn vào cuối tháng.
