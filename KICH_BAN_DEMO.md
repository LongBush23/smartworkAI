# KỊCH BẢN DEMO THỦ CÔNG
## Hệ thống Tính điểm KPI trong Công an nhân dân

Làm theo đúng thứ tự dưới đây, mỗi kịch bản 3–5 phút. Mỗi bước đều ghi rõ
**đăng nhập bằng gì · làm gì · phải thấy gì**.

---

## Chuẩn bị

Mở 2 cửa sổ dòng lệnh:

```bash
backend/venv/bin/uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Mở trình duyệt vào địa chỉ frontend in ra (mặc định `http://localhost:5173`).

**Đổi tài khoản:** bấm **Đăng xuất** ở đáy thanh trái, rồi đăng nhập lại.
Bạn sẽ đổi tài khoản khá nhiều, nên nhớ vị trí nút này.

Mật khẩu: `admin` dùng `admin123`, tất cả tài khoản còn lại dùng `123456`.

> Toàn bộ dữ liệu mẫu nằm ở **kỳ tháng hiện tại**. Nếu trang nào trống,
> kiểm tra lại bộ chọn Tháng/Năm ở góc phải.

---

## Kịch bản 1 — Nhìn toàn cảnh tổ chức
**Đăng nhập: `admin` / `admin123`**

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Vào **Cơ cấu tổ chức** | Cây 12 đơn vị 3 cấp, ghi **tên đầy đủ**: Bộ Công an → 4 Cục / Công an tỉnh → 7 Phòng. Dưới mỗi tên là cấp đơn vị và số cán bộ (gồm cả cấp dưới) |
| 2 | Bấm **Bộ Công an** (dòng trên cùng) | 63 cán bộ · 4 đơn vị trực thuộc · chưa có cán bộ trực tiếp |
| 3 | Bấm **Phòng Tham mưu tổng hợp** | 10 cán bộ · KPI tập thể · thanh phân bố xếp loại Nhóm 1/2/3 · bảng cán bộ bên dưới. Góc phải ghi **Mã đơn vị** để tra cứu |
| 4 | Xem cột **Tải việc** | Thanh màu + phần trăm + nhãn: Sẵn sàng (xanh) · Đang thực hiện (xanh dương) · Gần đầy (vàng) · Quá tải (đỏ) |
| 5 | Xem cột **Tiếp cận** | Có ổ khoá vàng ở người được tiếp cận tài liệu mật, kèm số nhiệm vụ mật đang giữ |
| 6 | Bấm vào **tên một cán bộ** | Mở hồ sơ: số hiệu CAND, cấp bậc, tải việc, nhiệm vụ giao/hoàn thành/quá hạn, số lần sửa (→ điểm B) và nhắc nhở (→ điểm C), biểu đồ diễn biến KPI 7 tháng |

**Điểm cần chú ý:** con số "Lần phải sửa" và "Lần bị nhắc nhở" chính là dữ liệu
đầu vào của điểm B và điểm C — không phải cán bộ tự khai.

---

## Kịch bản 2 — Nhiệm vụ có độ mật ⭐
Đây là phần quan trọng nhất. Ta xem **cùng một nhiệm vụ** bằng 3 tài khoản khác cấp độ.

Nhiệm vụ dùng để thử: **`NV-2026-08-0014`**, độ **TUYỆT MẬT**, thuộc **Phòng Chính sách cán bộ**.

### 2a. Người đủ cấp độ tiếp cận
**Đăng nhập: `director_cscb` / `123456`** *(Trưởng phòng Phòng Chính sách cán bộ, tiếp cận Tuyệt mật)*

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Vào **Nhiệm vụ được giao** | Dòng đầu ghi tổng số nhiệm vụ và *"… có độ mật"* |
| 2 | Bộ lọc **Mọi độ mật** → chọn **TUYỆT MẬT** | Còn đúng 1 dòng: `NV-2026-08-0014` |
| 3 | Đọc dòng đó | Tên thật **"Nhiệm vụ chuyên đề A2"** · ổ khoá đỏ · huy hiệu **TUYỆT MẬT** · số hồ sơ gốc **Số 148/HS-X01** |
| 4 | Bấm **Chi tiết** | Ô "Số hiệu hồ sơ gốc" và "Nơi lưu hồ sơ" **có dữ liệu**. Có dòng chữ đỏ: *hệ thống không lưu nội dung của nhiệm vụ có độ mật* |

### 2b. Người **thiếu** cấp độ tiếp cận
**Đăng nhập: `leader5` / `123456`** *(Phó Trưởng phòng cùng phòng Phòng Chính sách cán bộ, chỉ tiếp cận Tối mật)*

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Vào **Nhiệm vụ được giao** → lọc **TUYỆT MẬT** | Vẫn thấy 1 dòng, nhưng tên đã đổi thành **`NV-2026-08-0014`** (mã hiệu thay cho tên) |
| 2 | Nhìn dưới huy hiệu | Nhãn đỏ **"chưa đủ cấp độ tiếp cận"** · **không có** số hồ sơ gốc |
| 3 | Vẫn thấy được | Điểm · nhóm · số lượng · hạn · số lần nhắc · trạng thái — để chấm KPI vẫn minh bạch |
| 4 | Bấm **Chi tiết** | Băng đỏ sọc chéo: *"Thông tin đã được che theo cấp độ tiếp cận… Lượt truy cập này đã được ghi nhật ký"*. Ô hồ sơ gốc **trống** |

> **Đây không phải ẩn bằng giao diện.** Bấm `F12` → tab **Network** → mở lại nhiệm vụ →
> xem phản hồi của `GET /api/tasks/...`: các trường `file_reference`, `file_location`,
> `description` **không tồn tại** trong dữ liệu trả về. Máy chủ đã loại bỏ trước khi gửi.

### 2c. Cán bộ không được tiếp cận tài liệu mật
**Đăng nhập: `canbo12` / `123456`** *(cán bộ Phòng Chính sách cán bộ, chỉ tài liệu thường)*

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Vào **Nhiệm vụ được giao** → lọc **TUYỆT MẬT** | **Không có dòng nào** |
| 2 | Bỏ lọc | Chỉ thấy nhiệm vụ thường của chính mình |

### 2d. Nhật ký đã ghi lại
**Đăng nhập: `admin` / `admin123`**

Vào **Nhật ký hệ thống**, lọc theo `classified`:

| Bản ghi | Ý nghĩa |
|---|---|
| `task.classified_access` | Lượt xem **thành công** (của `director_cscb`) |
| `task.classified_denied` | Lượt **bị từ chối** (của `leader5`) — vẫn ghi lại |

---

## Kịch bản 3 — Giao nhiệm vụ và tác động lên điểm KPI
**Đăng nhập: `director_tmth` / `123456`** *(Trưởng phòng Tham mưu tổng hợp)*

### 3a. Giao nhiệm vụ mới
1. Vào **Nhiệm vụ được giao** → **Giao nhiệm vụ**
2. Ở *Chọn từ Danh mục nhiệm vụ công tác*, chọn một mục → **điểm và nhóm tự điền** theo khung đã duyệt
3. Điền *Căn cứ giao*, chọn cán bộ, đặt hạn → **Giao nhiệm vụ**
4. Quan sát khối 3 số giữa form:

| Ô | Ý nghĩa |
|---|---|
| Điểm được giao | điểm/sản phẩm × số lượng |
| **Điểm tối đa đạt được** | × 120% — mức trần khi hoàn thành vượt mức |
| Điểm đã hoàn thành | theo số lượng thực tế |

### 3b. Nhắc nhở làm giảm điểm tiến độ (C)
1. Chọn một nhiệm vụ **chưa hoàn thành** → bấm 🔔 (chuông)
2. Thông báo *"Đã ghi nhận nhắc nhở lần 1"*, cột **Nhắc** tăng lên 1
3. Bấm **Chi tiết** → khối dưới cùng: *"Đã nhắc nhở 1 lần → mức tiến độ (C) **75%**"*
4. Bấm chuông thêm 2 lần nữa → mức C tụt còn **50%** rồi **25%**

### 3c. Yêu cầu chỉnh sửa làm giảm điểm chất lượng (B)
1. Bấm 📝 (bút) trên một nhiệm vụ → cột **Sửa** tăng
2. Vào **Chi tiết**: 1 lần → **75%** · 2–4 lần → **50%** · 5–6 lần → **25%** · từ 7 lần → **0%**

### 3d. Thử phá cơ chế bảo mật (phải bị chặn)
| Thử gì | Kết quả đúng |
|---|---|
| Tạo nhiệm vụ, chọn độ mật **MẬT**, rồi điền ô *Diễn giải* | Ô Diễn giải **biến mất** khi chọn độ mật. Nếu cố gửi → báo lỗi từ chối |
| Đăng nhập `leader1` (Tối mật) → giao nhiệm vụ → mở ô **Độ mật** | Dòng **TUYỆT MẬT** bị khoá, ghi *"vượt cấp độ tiếp cận"* |

---

## Kịch bản 4 — Quy trình 3 bước ⭐
Cả 3 bước diễn ra trong **Phòng Tham mưu tổng hợp**, kỳ **tháng hiện tại**.

### Bước 1 — Tự đánh giá
**Đăng nhập: `canbo4` / `123456`**

1. Vào **Quy trình đánh giá** → thấy sơ đồ 3 bước
2. Kỳ của mình đang ở trạng thái **"Chưa tự đánh giá"** → bấm **Bước 1 – Tự đánh giá**
3. Tích các nhiệm vụ đã hoàn thành, chọn mức chất lượng và tiến độ cho từng việc
4. Chọn mức xếp loại tự nhận → **Gửi tự đánh giá (Bước 1)**
5. Trạng thái đổi thành **"Bước 1 – Chờ thẩm định"**

### Bước 2 — Cơ quan liên quan thẩm định
**Đăng nhập: `leader1` / `123456`**

1. Vào **Quy trình đánh giá**
2. Tìm dòng của **Phan Phương Bình** (`canbo0`) hoặc **Vũ Thu Mai** (`canbo5`) — đang **"Chờ thẩm định"**
3. Bấm **Bước 2 – Thẩm định** → đối chiếu lại mức chất lượng, tiến độ
4. Nhập nhận xét → **Hoàn tất thẩm định**
5. Trạng thái đổi thành **"Bước 2 – Chờ xác định điểm KPI"**

### Bước 3 — Cấp có thẩm quyền xác định điểm
**Đăng nhập: `director_tmth` / `123456`**

1. Vào **Quy trình đánh giá**
2. Tìm dòng của **Đỗ Gia Cường** (`leader1`) hoặc **Huỳnh Phương Hương** (`canbo1`) — đang **"Chờ xác định điểm KPI"**
3. Bấm **Bước 3 – Xác định điểm KPI**
4. Hệ thống tính A, B, C (và D nếu là lãnh đạo, chỉ huy), ra điểm KPI và nhóm xếp loại

> Nút **Bước 3** chỉ hiện với Trưởng phòng. `leader1` sẽ **không** thấy nút này —
> đó là đúng, vì thẩm quyền xác định điểm thuộc cấp có thẩm quyền.

---

## Kịch bản 5 — Tiêu chí chung (E) và kết quả xếp loại
**Đăng nhập: `director_tmth` / `123456`**

### 5a. Chấm 30 điểm tiêu chí chung
1. Vào **Tiêu chí chung (E)**
2. Ở ô *Kỳ đánh giá đã xác định điểm KPI*, chọn **Phòng Tham mưu tổng hợp** (tập thể)
3. Hệ thống **tự chọn đúng bộ tiêu chí**:

| Đối tượng | Bộ tiêu chí | Thang điểm |
|---|---|---|
| Tập thể | Tiêu chí tập thể | 6 × 5 = 30 |
| Lãnh đạo, chỉ huy | Tiêu chí lãnh đạo | 18 + 4 + 8 = 30 |
| Cán bộ không giữ chức vụ | Tiêu chí cán bộ | 20 + 8 + 2 = 30 |

4. Bấm ✕ ở vài tiêu chí để chuyển sang *không đảm bảo* → **điểm E giảm ngay**
5. Xem 4 ô tổng hợp phía trên: **E** · **KPI** · **KPI × 0,7** · **Tổng điểm xếp loại**
6. Thử lại với một **cá nhân** → bộ tiêu chí đổi khác, tự động

### 5b. Xem bảng điểm tổng hợp
Vào **Kết quả xếp loại**:

- Cột **A / B / C** theo phần trăm · cột **D** chỉ có số với lãnh đạo, chỉ huy (cán bộ hiện `–`)
- Cột **KPI**, **E**, **Tổng điểm**, **Xếp loại**
- Tự nhẩm kiểm tra một dòng: `Tổng điểm = E + KPI × 0,7`

---

## Kịch bản 6 — Đối chiếu với ví dụ trong văn bản
Phụ lục Hướng dẫn 20-HD/ĐUCA có ví dụ chấm điểm đồng chí A: **KPI = 97,97**, tổng điểm **98,579**.

Chạy lệnh sau để xem hệ thống tính ra đúng con số đó:

```bash
pytest backend/test_kpi.py -v -k worked_example
```

Chạy toàn bộ 47 test kiểm chứng công thức:

```bash
pytest -v
```

---

## Kịch bản 7 — Kiểm tra phạm vi xem theo chức vụ
Đăng nhập lần lượt, vào **Nhiệm vụ được giao**, đối chiếu số lượng:

| Tài khoản | Chức vụ | Số nhiệm vụ thấy được | Vì sao |
|---|---|---|---|
| `admin` | Quản trị hệ thống | **337** | Toàn hệ thống |
| `director_tmth` | Trưởng phòng | **50** | Chỉ đơn vị mình phụ trách |
| `leader1` | Phó Trưởng phòng | **50** | Chỉ đơn vị mình phụ trách |
| `canbo0` | Cán bộ | **7** | Chỉ nhiệm vụ của chính mình |

Tương tự ở **Quy trình đánh giá**: admin 70 kỳ · `director_tmth` 10 kỳ · `canbo0` 1 kỳ.

---

## Tóm tắt tài khoản dùng trong demo

| Tài khoản | Mật khẩu | Dùng cho kịch bản |
|---|---|---|
| `admin` | `admin123` | 1 (toàn cảnh) · 2d (nhật ký) · 7 |
| `director_cscb` | `123456` | 2a — xem nhiệm vụ mật đầy đủ |
| `leader5` | `123456` | 2b — nhiệm vụ mật **bị che** |
| `canbo12` | `123456` | 2c — không thấy nhiệm vụ mật |
| `director_tmth` | `123456` | 3 (giao việc) · 4 Bước 3 · 5 (tiêu chí E) |
| `leader1` | `123456` | 3d (chặn giao vượt cấp) · 4 Bước 2 |
| `canbo4` | `123456` | 4 Bước 1 — tự đánh giá |
| `canbo0` | `123456` | 7 — phạm vi cán bộ |

---

## Nếu gặp trục trặc

| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| Trang trắng, không có dữ liệu | Bộ chọn **Tháng/Năm** đang ở kỳ không có dữ liệu — chọn lại tháng hiện tại |
| Đăng nhập không được | Backend chưa chạy. Kiểm tra `http://localhost:8000/docs` |
| Không thấy nút Bước 2 / Bước 3 | Đúng quy định — Bước 2 cần lãnh đạo chỉ huy, Bước 3 cần Trưởng phòng |
| Muốn làm lại từ đầu | Chạy lại `python -m backend.services.seeder` (⚠️ xoá sạch dữ liệu hiện có) |
