# KỊCH BẢN DEMO THỦ CÔNG
## Hệ thống tính điểm KPI trong Công an nhân dân (KPI-CAND)

Làm theo đúng thứ tự dưới đây, mỗi kịch bản 3–5 phút. Mỗi bước đều ghi rõ
**đăng nhập bằng gì · làm gì · phải thấy gì**.

---

## Chuẩn bị

Mở 2 cửa sổ dòng lệnh:

```bash
backend/venv/bin/uvicorn backend.main:app --reload --port 8000
```

> ⚠️ Không cần cờ `ALLOW_DEMO_ACCOUNTS` nữa: mật khẩu `123456789a` cố ý nằm ngoài
> danh sách mật khẩu mặc định bị chặn. Đổi lại, các tài khoản mẫu **không được cơ chế
> chặn bảo vệ** — chỉ chấp nhận được vì toàn bộ là dữ liệu giả.

```bash
cd frontend && npm run dev
```

Mở trình duyệt vào địa chỉ frontend in ra (mặc định `http://localhost:5173`).

**Đổi tài khoản:** bấm **Đăng xuất** ở đáy thanh trái, rồi đăng nhập lại.
Bạn sẽ đổi tài khoản khá nhiều, nên nhớ vị trí nút này.

Mật khẩu: **mọi tài khoản đều dùng `123456789a`**, kể cả `admin`.

> Toàn bộ dữ liệu mẫu phủ **7 tháng** (6 tháng trước + tháng hiện tại).
> Nếu trang nào trống, kiểm tra lại bộ chọn Tháng/Năm ở góc phải.

---

## Kịch bản 1 — Nhìn toàn cảnh tổ chức
**Đăng nhập: `admin` / `123456789a`**

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Ở thanh trái, nhóm **Tổng quan** → bấm **Cơ cấu tổ chức** | Cây 12 đơn vị 3 cấp: Bộ Công an → 4 Cục / Công an tỉnh → 7 Phòng. Dưới mỗi tên là cấp đơn vị và số cán bộ (gồm cả cấp dưới) |
| 2 | Bấm **Bộ Công an** (dòng trên cùng) | 63 cán bộ (gồm đơn vị cấp dưới) · 4 đơn vị trực thuộc · chưa có cán bộ trực tiếp |
| 3 | Bấm **Phòng Tham mưu tổng hợp** | 9 cán bộ trực thuộc · KPI tập thể (nếu đã phê duyệt) · thanh phân bố xếp loại Nhóm 1/2/3 · bảng cán bộ bên dưới. Góc phải ghi **Mã đơn vị** `VPB-P1` |
| 4 | Xem cột **Tải việc** trong bảng cán bộ | Thanh màu + phần trăm + nhãn: Sẵn sàng (xanh lá) · Đang thực hiện (xanh dương) · Gần đầy (vàng) · Quá tải (đỏ). Công thức: tổng điểm nhiệm vụ chưa hoàn thành / định mức điểm |
| 5 | Xem cột **Tiếp cận** | Có khiên vàng ở người được tiếp cận tài liệu mật. Bên cạnh: biểu tượng ổ khoá + số nhiệm vụ mật đang giữ (nếu có) |
| 6 | Bấm vào **tên một cán bộ** | Mở hồ sơ chi tiết: số hiệu CAND, cấp bậc, đơn vị, tải việc (thanh + phần trăm), 6 ô chỉ số chính: nhiệm vụ giao/hoàn thành/đang thực hiện/quá hạn/lần phải sửa (→ điểm B)/lần bị nhắc nhở (→ điểm C), biểu đồ diễn biến KPI các tháng đã phê duyệt, tổng hợp KPI gần nhất + bình quân năm |

**Điểm cần chú ý:** con số "Lần phải sửa" và "Lần bị nhắc nhở" chính là dữ liệu
đầu vào của điểm B và điểm C — không phải cán bộ tự khai.

---

## Kịch bản 2 — Nhiệm vụ có độ mật ⭐
Đây là phần quan trọng nhất. Ta xem **cùng một nhiệm vụ** bằng 3 tài khoản khác cấp độ.

Nhiệm vụ dùng để thử: tìm một nhiệm vụ **TUYỆT MẬT** thuộc **Phòng Chính sách cán bộ** (ghi lại mã hiệu dạng `NV-2026-xx-xxxx`).

### 2a. Người đủ cấp độ tiếp cận
**Đăng nhập: `director_cscb` / `123456789a`** *(Trưởng phòng Phòng Chính sách cán bộ, tiếp cận Tuyệt mật)*

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Thanh trái → nhóm **Nhiệm vụ công tác** → bấm **Nhiệm vụ được giao** | Dòng đầu ghi tổng số nhiệm vụ và *"… có độ mật"* |
| 2 | Bộ lọc **Mọi độ mật** → chọn **TUYỆT MẬT** | Chỉ còn nhiệm vụ Tuyệt mật. Mỗi dòng có: ổ khoá + huy hiệu **TUYỆT MẬT** |
| 3 | Đọc một dòng Tuyệt mật | Tên thật (tên gọi quy ước) hiện đầy đủ · huy hiệu đỏ **TUYỆT MẬT** · số hồ sơ gốc dạng `Số xxx/HS-X01` |
| 4 | Bấm **Chi tiết** | Hộp chi tiết mở ra. Ô "Số hiệu hồ sơ gốc" và "Nơi lưu hồ sơ" **có dữ liệu**. Có dòng chữ đỏ: *hệ thống không lưu nội dung của nhiệm vụ có độ mật* |

### 2b. Người **thiếu** cấp độ tiếp cận
**Đăng nhập: `leader5` / `123456789a`** *(Phó Trưởng phòng cùng phòng Phòng Chính sách cán bộ, chỉ tiếp cận Tối mật)*

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Vào **Nhiệm vụ được giao** → lọc **TUYỆT MẬT** | Vẫn thấy dòng nhiệm vụ, nhưng tên đã đổi thành **mã hiệu** (VD: `NV-2026-08-xxxx`) thay cho tên gọi quy ước |
| 2 | Nhìn dưới huy hiệu | Nhãn đỏ **"chưa đủ cấp độ tiếp cận"** · **không có** số hồ sơ gốc |
| 3 | Vẫn thấy được | Điểm · nhóm · số lượng · hạn · số lần nhắc · trạng thái — để chấm KPI vẫn minh bạch |
| 4 | Bấm **Chi tiết** | Băng đỏ sọc chéo: *"Thông tin đã được che theo cấp độ tiếp cận… Lượt truy cập này đã được ghi nhật ký"*. Ô hồ sơ gốc **trống** |

> **Đây không phải ẩn bằng giao diện.** Bấm `F12` → tab **Network** → mở lại nhiệm vụ →
> xem phản hồi của `GET /api/tasks/...`: các trường `file_reference`, `file_location`,
> `description` **không tồn tại** trong dữ liệu trả về. Máy chủ đã loại bỏ trước khi gửi
> (xem `security_policy.redact()`).

### 2c. Cán bộ không được tiếp cận tài liệu mật
**Đăng nhập: `canbo12` / `123456789a`** *(cán bộ Phòng Chính sách cán bộ, chỉ tài liệu thường — clearance_level 0)*

| Bước | Làm gì | Phải thấy gì |
|---|---|---|
| 1 | Vào **Nhiệm vụ được giao** → lọc **TUYỆT MẬT** | **Không có dòng nào** |
| 2 | Bỏ lọc | Chỉ thấy nhiệm vụ thường của chính mình (cán bộ không giữ chức vụ chỉ thấy nhiệm vụ của mình) |

### 2d. Nhật ký đã ghi lại
**Đăng nhập: `admin` / `123456789a`**

Thanh trái → nhóm **Quản lý** → bấm **Nhật ký hệ thống**. Lọc theo `classified`:

| Bản ghi | Ý nghĩa |
|---|---|
| `task.classified_access` | Lượt xem **thành công** (của `director_cscb`) |
| `task.classified_denied` | Lượt **bị từ chối** (của `leader5`) — vẫn ghi lại |

---

## Kịch bản 3 — Giao nhiệm vụ và tác động lên điểm KPI
**Đăng nhập: `director_tmth` / `123456789a`** *(Trưởng phòng Tham mưu tổng hợp)*

### 3a. Giao nhiệm vụ mới
1. Thanh trái → **Nhiệm vụ được giao** → bấm nút **Giao nhiệm vụ** (góc phải)
2. Ở mục *Chọn từ Danh mục nhiệm vụ công tác*, chọn một mục → **điểm và nhóm tự điền** theo Danh mục đã duyệt
3. Điền *Căn cứ giao*, chọn cán bộ, đặt hạn → **Giao nhiệm vụ**
4. Quan sát khối 4 số tổng hợp phía trên bảng:

| Ô | Ý nghĩa |
|---|---|
| Tổng điểm được giao | Tổng điểm = kpi_point × quantity_assigned của mọi nhiệm vụ |
| Điểm số lượng (A) | Tỷ lệ hoàn thành theo điểm: Σ(điểm đã hoàn thành) / Σ(điểm được giao) |
| Điểm chất lượng (B) | Tỷ lệ chất lượng: tính theo mức % tương ứng số lần sửa |
| Điểm tiến độ (C) | Tỷ lệ tiến độ: tính theo mức % tương ứng số lần nhắc nhở |

### 3b. Nhắc nhở làm giảm điểm tiến độ (C)
1. Chọn một nhiệm vụ **chưa hoàn thành** → bấm 🔔 (chuông)
2. Thông báo *"Đã ghi nhận nhắc nhở lần 1"*, cột **Nhắc** tăng lên 1
3. Bấm **Chi tiết** → kiểm tra: nhắc 1 lần → mức tiến độ (C) **≤75%**
4. Bấm chuông thêm 2 lần nữa → mức C tụt: 2 lần ≤**50%**, 3 lần ≤**25%**, từ 4 lần **0%**

### 3c. Yêu cầu chỉnh sửa làm giảm điểm chất lượng (B)
1. Bấm 📝 (bút) trên một nhiệm vụ → cột **Sửa** tăng
2. Mức tính: 1 lần → **≤75%** · 2–4 lần → **≤50%** · 5–6 lần → **≤25%** · từ 7 lần → **0%**

### 3d. Thử phá cơ chế bảo mật (phải bị chặn)
| Thử gì | Kết quả đúng |
|---|---|
| Tạo nhiệm vụ → chọn độ mật **MẬT** → nhìn ô *Diễn giải* | Khu vực nhập nội dung **biến mất**, thay bằng cảnh báo đỏ *"Hệ thống không lưu nội dung của nhiệm vụ có độ mật"*. Chỉ hiện ô *Số hiệu hồ sơ gốc* và *Nơi lưu hồ sơ*. Nếu cố gửi có description → API báo lỗi từ chối |
| Đăng nhập `leader1` (tiếp cận Tối mật) → giao nhiệm vụ → mở ô **Độ mật** | Dòng **TUYỆT MẬT** bị khoá (disabled), ghi *"vượt cấp độ tiếp cận"* |

---

## Kịch bản 4 — Quy trình 3 bước ⭐
Cả 3 bước diễn ra trong **Phòng Tham mưu tổng hợp**, kỳ **tháng hiện tại**.

### Bước 1 — Tự đánh giá
**Đăng nhập: `canbo4` / `123456789a`**

1. Thanh trái → nhóm **Đánh giá KPI** → bấm **Quy trình đánh giá**
2. Thấy sơ đồ 3 bước (*Tự đánh giá → Cơ quan có liên quan thẩm định → Cấp có thẩm quyền xác định điểm KPI*)
3. Tìm kỳ của mình đang ở trạng thái **"Chưa tự đánh giá"** → bấm **Bước 1 – Tự đánh giá**
4. Tích các nhiệm vụ đã hoàn thành, chọn mức chất lượng (B) và tiến độ (C) cho từng việc
5. Chọn mức xếp loại tự nhận (Nhóm 1/2/3) → **Gửi tự đánh giá (Bước 1)**
6. Trạng thái đổi thành **"Bước 1 – Chờ thẩm định"**

### Bước 2 — Cơ quan liên quan thẩm định
**Đăng nhập: `leader1` / `123456789a`** *(Phó Trưởng phòng Phòng Tham mưu tổng hợp)*

1. Vào **Quy trình đánh giá**
2. Tìm kỳ đang ở trạng thái **"Bước 1 – Chờ thẩm định"** → bấm **Bước 2 – Thẩm định**
3. Đối chiếu lại mức chất lượng, tiến độ cho từng nhiệm vụ
4. Nhập nhận xét → bấm **Hoàn tất thẩm định – chuyển Bước 3**
5. Trạng thái đổi thành **"Bước 2 – Chờ xác định điểm KPI"**

### Bước 3 — Cấp có thẩm quyền xác định điểm
**Đăng nhập: `director_tmth` / `123456789a`** *(Trưởng phòng)*

1. Vào **Quy trình đánh giá**
2. Tìm kỳ đang ở trạng thái **"Bước 2 – Chờ xác định điểm KPI"** → bấm **Bước 3 – Xác định điểm KPI**
3. Hệ thống tự động tính A, B, C (và D nếu là lãnh đạo, chỉ huy), ra điểm KPI và nhóm xếp loại
4. Trạng thái đổi thành **"Bước 3 – Đã xác định điểm KPI"** kèm số điểm

> - Nút **Bước 2** chỉ hiện với lãnh đạo, chỉ huy (`leader` hoặc `director`). `canbo4` sẽ **không** thấy nút này.
> - Nút **Bước 3** chỉ hiện với Trưởng phòng (`director`). `leader1` sẽ **không** thấy nút này —
>   đó là đúng, vì thẩm quyền xác định điểm thuộc cấp có thẩm quyền.
> - Khi đã phê duyệt, hiện nút **Xuất phiếu Excel** để in phiếu đánh giá cá nhân.

---

## Kịch bản 5 — Tiêu chí chung (E) và kết quả xếp loại
**Đăng nhập: `director_tmth` / `123456789a`**

### 5a. Chấm 30 điểm tiêu chí chung
1. Thanh trái → nhóm **Đánh giá KPI** → bấm **Tiêu chí chung (E)**
2. Ở ô *Kỳ đánh giá đã xác định điểm KPI*, chọn một kỳ **đã phê duyệt** (có dấu ✓)
3. Hệ thống **tự chọn đúng bộ tiêu chí** theo đối tượng:

| Đối tượng | Bộ tiêu chí | Thang điểm |
|---|---|---|
| Tập thể | Tiêu chí tập thể | 6 × 5 = 30 |
| Lãnh đạo, chỉ huy | Tiêu chí lãnh đạo | 18 + 4 + 8 = 30 |
| Cán bộ không giữ chức vụ | Tiêu chí cán bộ | 20 + 8 + 2 = 30 |

4. Mặc định mọi tiêu chí đều "đảm bảo" (✓ xanh). Bấm ✕ (đỏ) ở vài tiêu chí để chuyển sang *không đảm bảo* → **điểm E giảm ngay** (tiêu chí đảm bảo = điểm tối đa, không đảm bảo = 0)
5. Xem 4 ô tổng hợp phía trên: **E** · **KPI** · **KPI × 0,7** · **Tổng điểm xếp loại**
6. Bấm **Lưu điểm tiêu chí chung**
7. Thử lại với một **đối tượng khác** (tập thể hoặc cá nhân) → bộ tiêu chí tự đổi

### 5b. Xem bảng điểm tổng hợp
Thanh trái → bấm **Kết quả xếp loại**:

- Cột **A** (Số lượng) / **B** (Chất lượng) / **C** (Tiến độ) theo phần trăm
- Cột **D** (Lãnh đạo) chỉ có số với lãnh đạo, chỉ huy (cán bộ hiện `–`)
- Cột **KPI** (tô nền tím), **E** (Tiêu chí chung), **Tổng điểm** (tô nền vàng), **Xếp loại** (Nhóm 1/2/3)
- Tự nhẩm kiểm tra một dòng: `Tổng điểm = E + KPI × 0,7`
- Bấm **Xuất Excel** để tải bảng tổng hợp xếp loại dạng `.xlsx`

---

## Kịch bản 6 — Đối chiếu với ví dụ trong văn bản
Phụ lục Hướng dẫn 20-HD/ĐUCA có ví dụ chấm điểm đồng chí A: **KPI = 97,97**, tổng điểm **98,579**.

Chạy lệnh sau để xem hệ thống tính ra đúng con số đó:

```bash
pytest backend/test_kpi.py -v -k worked_example
```

Chạy toàn bộ test kiểm chứng công thức:

```bash
pytest -v
```

Các test bao gồm:
- 6 mức phần trăm chất lượng (B) và 6 mức phần trăm tiến độ (C)
- Công thức KPI 3 tiêu chí (cán bộ) và 4 tiêu chí (lãnh đạo)
- Ngưỡng phân nhóm: Nhóm 1 (≥70), Nhóm 2 (50–<70), Nhóm 3 (<50)
- Khung tiêu chí chung: 3 bộ đều tổng đúng 30 điểm
- Tổng điểm xếp loại: E + KPI × 0,7
- KPI người đứng đầu ≤ KPI tập thể

---

## Kịch bản 7 — Kiểm tra phạm vi xem theo chức vụ
Đăng nhập lần lượt, vào **Nhiệm vụ được giao**, đối chiếu:

| Tài khoản | Chức vụ | Phạm vi nhìn thấy | Vì sao |
|---|---|---|---|
| `admin` | Quản trị hệ thống | **Toàn hệ thống** — tất cả đơn vị | Vai trò admin không bị lọc theo đơn vị |
| `director_tmth` | Trưởng phòng | **Chỉ đơn vị mình phụ trách** (Phòng TMTH) | API lọc theo `department_id` của người gọi |
| `leader1` | Phó Trưởng phòng | **Chỉ đơn vị mình phụ trách** (Phòng TMTH) | Lãnh đạo, chỉ huy cũng bị lọc theo đơn vị |
| `canbo0` | Cán bộ | **Chỉ nhiệm vụ của chính mình** | Cán bộ không giữ chức vụ chỉ thấy `assigned_to = mình` |

Tương tự ở **Quy trình đánh giá**: admin thấy tất cả kỳ · `director_tmth` chỉ thấy kỳ đơn vị mình · `canbo0` chỉ 1 kỳ của mình.

---

## Kịch bản 8 — Gợi ý phân công bằng mô hình ⭐
**Đăng nhập: `director_tmth` / `123456789a`**

1. Vào **Nhiệm vụ được giao** → bấm **Giao nhiệm vụ**
2. Chọn một mục từ Danh mục nhiệm vụ, chọn độ mật và nhóm độ phức tạp
3. Bấm nút **Gợi ý phân công** → hệ thống gọi mô hình chấm điểm, trả về danh sách 5 cán bộ phù hợp nhất kèm **điểm phù hợp** (0–100)
4. Bấm chọn một người trong danh sách gợi ý → ô *Cán bộ thực hiện* tự điền
5. Lãnh đạo vẫn có thể chọn người **ngoài** danh sách gợi ý — hệ thống ghi nhận cả hai trường hợp

> Trang **Mô hình hỗ trợ ra quyết định** (thanh trái → nhóm Đánh giá KPI) hiển thị:
> - Danh sách mô hình đang hoạt động (gợi ý phân công, cảnh báo sớm, tra cứu hướng dẫn)
> - Thống kê lượt gợi ý, tỷ lệ lãnh đạo làm theo gợi ý

---

## Tóm tắt tài khoản dùng trong demo

| Tài khoản | Mật khẩu | Vai trò | Cấp độ tiếp cận | Dùng cho kịch bản |
|---|---|---|---|---|
| `admin` | `123456789a` | Quản trị hệ thống | Tuyệt mật (3) | 1 (toàn cảnh) · 2d (nhật ký) · 7 |
| `director_cscb` | `123456789a` | Trưởng phòng CSCB | Tuyệt mật (3) | 2a — xem nhiệm vụ mật đầy đủ |
| `leader5` | `123456789a` | Phó Trưởng phòng CSCB | Tối mật (2) | 2b — nhiệm vụ mật **bị che** |
| `canbo12` | `123456789a` | Cán bộ CSCB | Thường (0) | 2c — không thấy nhiệm vụ mật |
| `director_tmth` | `123456789a` | Trưởng phòng TMTH | Tuyệt mật (3) | 3 (giao việc) · 4 Bước 3 · 5 (tiêu chí E) · 8 |
| `leader1` | `123456789a` | Phó Trưởng phòng TMTH | Tối mật (2) | 3d (chặn giao vượt cấp) · 4 Bước 2 |
| `canbo4` | `123456789a` | Cán bộ TMTH | Mật (1) | 4 Bước 1 — tự đánh giá |
| `canbo0` | `123456789a` | Cán bộ TMTH | Thường (0) | 7 — phạm vi cán bộ |

> **Quy tắc cấp độ tiếp cận từ seeder:**
> - Director (Trưởng phòng): clearance_level = 3 (Tuyệt mật)
> - Leader (Phó Trưởng phòng / Đội trưởng): clearance_level = 2 (Tối mật)
> - Cán bộ: xoay vòng [0, 0, 0, 1, 1, 2] → đa số chỉ tài liệu thường

---

## Thanh điều hướng (bên trái)

Để tiện tìm, đây là cấu trúc thanh trái theo đúng code:

| Nhóm | Mục | Ai thấy |
|---|---|---|
| **Tổng quan** | Trang chủ · Cơ cấu tổ chức | Tất cả |
| **Nhiệm vụ công tác** | Nhiệm vụ được giao · Danh mục nhiệm vụ | Danh mục: Trưởng phòng trở lên |
| **Đánh giá KPI** | Tổng quan KPI · Quy trình đánh giá · Tiêu chí chung (E) · Kết quả xếp loại · Mô hình hỗ trợ ra quyết định | Tiêu chí + Mô hình: Lãnh đạo trở lên |
| **Quản lý** | Cán bộ · Rà soát chất lượng · Nhật ký hệ thống | Cán bộ + Rà soát: Trưởng phòng trở lên · Nhật ký: chỉ Admin |

---

## Nếu gặp trục trặc

| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| Trang trắng, không có dữ liệu | Bộ chọn **Tháng/Năm** đang ở kỳ không có dữ liệu — chọn lại tháng hiện tại |
| *"Không kết nối được máy chủ"* | Hai nguyên nhân: **(1)** backend chưa chạy — mở `http://localhost:8000/health`, phải thấy `{"status":"ok"}`; **(2)** tên miền giao diện chưa được phép gọi API — xem log khởi động backend dòng `CORS cho phép: …`, nếu thiếu thì thêm vào biến `CORS_ORIGINS` |
| *"Sai tài khoản hoặc mật khẩu"* | Máy chủ có trả lời, nên chỉ là gõ sai. Mật khẩu của mọi tài khoản là `123456789a` |
| *"Tài khoản đang dùng mật khẩu mặc định"* | Tài khoản đó còn mật khẩu cũ (`admin123`/`123456`). Chạy `python -m backend.scripts.set_password --tat-ca 123456789a` |
| Không thấy nút Bước 2 / Bước 3 | Đúng quy định — Bước 2 cần lãnh đạo, chỉ huy (`leader`/`director`), Bước 3 cần Trưởng phòng (`director`) |
| Không thấy Danh mục nhiệm vụ / Tiêu chí chung | Đúng phân quyền — Danh mục yêu cầu `director` trở lên, Tiêu chí yêu cầu `leader` trở lên |
| Muốn làm lại từ đầu | Chạy lại `python -m backend.services.seeder` (⚠️ xoá sạch dữ liệu hiện có) |
