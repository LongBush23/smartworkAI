# HƯỚNG DẪN SỬ DỤNG
## Hệ thống Tính điểm KPI trong Công an nhân dân

Hệ thống được xây dựng theo **Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026** của Ban Thường vụ
Đảng ủy Công an Trung ương về phương pháp tính điểm và sử dụng chỉ số đo lường (KPI)
trong đánh giá, xếp loại chất lượng đối với tập thể, cá nhân trong Công an nhân dân.

---

## 1. Tài khoản mẫu

| Thẩm quyền | Tài khoản | Mật khẩu | Phạm vi |
|---|---|---|---|
| Quản trị hệ thống | `admin` | `admin123` | Toàn bộ dữ liệu, quản lý đơn vị, nhật ký |
| Lãnh đạo đơn vị (người đứng đầu) | `director_vp`, `director_tccb`, `director_pc`, `director_csdt`, `director_anctnb` | `123456` | Danh mục nhiệm vụ, xác định điểm KPI (Bước 3) |
| Lãnh đạo, chỉ huy | `leader1` … `leader10` | `123456` | Giao nhiệm vụ, thẩm định (Bước 2) |
| Cán bộ, chiến sĩ | `canbo0` … `canbo29` | `123456` | Nhiệm vụ của mình, tự đánh giá (Bước 1) |

> Lãnh đạo, chỉ huy được tính KPI theo **04 tiêu chí** (có thêm điểm D);
> tập thể và cán bộ không giữ chức vụ tính theo **03 tiêu chí**.

---

## 2. Phương pháp tính điểm

### 2.1. Điểm của từng công việc

Mỗi công việc trong **Danh mục nhiệm vụ công tác** được xác định điểm trên thang **100 điểm**,
chia thành 03 nhóm theo tính chất, mức độ phức tạp:

| Nhóm | Dải điểm |
|---|---|
| Nhóm 1 | 0 đến dưới 50 điểm |
| Nhóm 2 | 50 đến dưới 70 điểm |
| Nhóm 3 | 70 đến 100 điểm |

### 2.2. Bốn tiêu chí thành phần

**A — Điểm về số lượng kết quả thực hiện nhiệm vụ**

```
A = Điểm số lượng công việc đã hoàn thành / Điểm công việc được giao theo Danh mục
```

**B — Điểm về chất lượng kết quả thực hiện nhiệm vụ**

```
B = Điểm về chất lượng của công việc đã hoàn thành / Điểm công việc được giao
```

Mức điểm chất lượng theo số lần phải hoàn thiện, chỉnh sửa:

| Đánh giá | Số lần sửa | Mức điểm |
|---|---|---|
| Vượt mức yêu cầu | — | không quá **120%** |
| Đảm bảo chất lượng | 0 | **100%** |
| Cơ bản đảm bảo | 01 lần | không quá **75%** |
| Còn thiếu sót | 02 – 04 lần | không quá **50%** |
| Thiếu sót | 05 – 06 lần | không quá **25%** |
| Không đạt | từ 07 lần | **không tính điểm** |

**C — Điểm về tiến độ thực hiện nhiệm vụ**

```
C = Điểm về tiến độ của công việc hoàn thành / Điểm công việc được giao
```

Mức điểm tiến độ theo số lần bị nhắc nhở:

| Đánh giá | Số lần nhắc nhở | Mức điểm |
|---|---|---|
| Vượt tiến độ và đảm bảo chất lượng | — | không quá **120%** |
| Đảm bảo tiến độ và chất lượng | 0 | **100%** |
| Chưa đảm bảo tiến độ | 01 lần | không quá **75%** |
| Chưa đảm bảo tiến độ | 02 lần | không quá **50%** |
| Chưa đảm bảo tiến độ | 03 lần | không quá **25%** |
| Chưa đảm bảo tiến độ | từ 04 lần | **không tính điểm** |

**D — Điểm về kết quả lãnh đạo, chỉ đạo** *(chỉ với cán bộ là lãnh đạo, chỉ huy)*

```
      Số tập thể, cá nhân thuộc quyền quản lý được đánh giá hoàn thành nhiệm vụ trở lên
D = ─────────────────────────────────────────────────────────────────────────────────  (0 – 01)
                        Số tập thể, cá nhân được đánh giá
```

### 2.3. Điểm KPI

```
KPI tập thể                        = (A + B + C) / 3 × 100
KPI cá nhân không giữ chức vụ      = (A + B + C) / 3 × 100
KPI cá nhân là lãnh đạo, chỉ huy   = (A + B + C + D) / 4 × 100
```

> **KPI của người đứng đầu không cao hơn KPI của tập thể, đơn vị do mình đứng đầu.**
> Hệ thống tự động áp mức trần này khi xác định điểm.

Điểm A, B, C được ghi ở 03 chữ số thập phân và điểm KPI ở 02 chữ số thập phân,
đúng như cách ghi tại Phụ lục.

### 2.4. Tổng điểm dùng trong đánh giá, xếp loại

| Thành phần | Tối đa |
|---|---|
| **E** — Điểm theo nhóm tiêu chí chung | 30 điểm |
| Điểm theo nhóm tiêu chí về kết quả thực hiện nhiệm vụ = KPI × 0,7 | 70 điểm |

```
F (tập thể)                      = E + KPI tập thể × 0,7
G (cá nhân không là lãnh đạo)    = E + KPI cá nhân × 0,7
H (cá nhân là lãnh đạo, chỉ huy) = E + KPI lãnh đạo × 0,7
```

### 2.5. Phân nhóm cán bộ

| Nhóm | Điểm KPI | Ý nghĩa |
|---|---|---|
| Nhóm 1 | 70 – 100 | Đáp ứng tốt yêu cầu nhiệm vụ trở lên |
| Nhóm 2 | 50 – dưới 70 | Đáp ứng yêu cầu nhiệm vụ |
| Nhóm 3 | dưới 50 | Chưa đáp ứng yêu cầu nhiệm vụ |

### 2.6. KPI quý, năm

Điểm KPI hằng quý, hằng năm được xác định bằng **bình quân điểm KPI hằng tháng**.

---

## 3. Quy trình 03 bước

```
Bước 1                     Bước 2                        Bước 3
Tự đánh giá và        →    Cơ quan có liên quan     →    Cấp có thẩm quyền
đề xuất mức xếp loại       thẩm định, đề xuất            xác định điểm KPI
(cán bộ / tập thể)         (lãnh đạo, chỉ huy)           (người đứng đầu)
```

**Bước 1 — Tự đánh giá.** Cán bộ báo cáo kết quả thực hiện nhiệm vụ, tự chấm điểm theo KPI,
làm rõ số lượng công việc hoàn thành; mức độ đạt được về chất lượng và tiến độ so với kế hoạch;
nguyên nhân chưa đảm bảo (nếu có), rồi đề xuất mức xếp loại.

**Bước 2 — Thẩm định.** Cơ quan tổ chức cán bộ phối hợp cơ quan tham mưu đối chiếu Danh mục
nhiệm vụ công tác và kết quả thực tế để đánh giá, đề xuất.

**Bước 3 — Xác định điểm KPI.** Cấp có thẩm quyền xác định điểm KPI; sau đó thông báo kết quả
bằng hình thức phù hợp.

Trạng thái trên hệ thống: `Chưa tự đánh giá` → `Chờ thẩm định` → `Chờ xác định điểm KPI` →
`Đã xác định điểm KPI`. Trường hợp số liệu chưa khớp hồ sơ, hồ sơ được trả lại.

---

## 4. Các chức năng chính

### 4.1. Trang chủ
Nhiệm vụ trong tháng, số quá hạn, KPI kỳ gần nhất, KPI bình quân năm, diễn biến KPI theo tháng,
và nhắc việc bước tiếp theo của kỳ đánh giá hiện tại.

### 4.2. Danh mục nhiệm vụ *(Lãnh đạo đơn vị trở lên)*
Xây dựng và phê duyệt Khung Danh mục nhiệm vụ công tác theo KPI cho từng năm: tên nhiệm vụ,
sản phẩm đầu ra, nhóm độ phức tạp và số điểm. Danh mục có 2 trạng thái: **Bản nháp** và **Đã duyệt**.

Nhiệm vụ phát sinh chưa có trong Khung Danh mục do lãnh đạo trực tiếp giao xác định nhóm và số điểm;
đến kỳ rà soát gần nhất sẽ đề xuất bổ sung vào Khung.

### 4.3. Nhiệm vụ được giao
- Cán bộ chỉ thấy nhiệm vụ của mình; lãnh đạo, chỉ huy thấy toàn đơn vị.
- Bảng tổng hợp hiển thị ngay **tổng điểm được giao** và **A / B / C dự kiến** của kỳ.
- Lãnh đạo, chỉ huy có 2 thao tác trực tiếp ảnh hưởng điểm KPI:
  - 🔔 **Nhắc nhở tiến độ** → tăng số lần nhắc nhở, giảm mức điểm **C**
  - 📝 **Yêu cầu hoàn thiện, chỉnh sửa** → tăng số lần sửa, giảm mức điểm **B**

### 4.4. Quy trình đánh giá
Thực hiện 3 bước nêu trên. Mức chất lượng và tiến độ của từng công việc được chọn theo đúng
các mức quy định, kèm tỷ lệ phần trăm tương ứng.

### 4.5. Tiêu chí chung (E) *(Lãnh đạo, chỉ huy trở lên)*
Chấm 30 điểm tiêu chí chung theo đúng Phụ lục, tự động chọn bộ tiêu chí phù hợp:

| Đối tượng | Bố cục thang điểm |
|---|---|
| Tập thể | 6 tiêu chí × 5 điểm = 30 |
| Cá nhân là lãnh đạo, chỉ huy | 18 + 04 + 08 = 30 |
| Cá nhân không là lãnh đạo, chỉ huy | 20 + 08 + 02 = 30 |

Mỗi tiêu chí chấm theo 2 mức: **Đảm bảo** (đạt tối đa điểm) hoặc **Không đảm bảo** (0 điểm).
Trang hiển thị luôn tổng điểm xếp loại = E + KPI × 0,7.

### 4.6. Kết quả xếp loại
Bảng điểm chi tiết A, B, C, D, KPI, E và tổng điểm; xếp nhóm theo ngưỡng 70 / 50.

### 4.7. Cán bộ / Đơn vị *(Lãnh đạo đơn vị trở lên)*
Quản lý cán bộ theo cấp bậc hàm, chức vụ, đơn vị và thẩm quyền. Đổi vai trò sang
lãnh đạo, chỉ huy sẽ tự chuyển sang cách tính KPI 04 tiêu chí.

---

## 5. Cài đặt và chạy

### 5.1. Backend

```bash
pip install -r backend/requirements.txt
```

Cấu hình biến môi trường:

```bash
export MONGO_URI="mongodb://localhost:27017"
export DB_NAME="smartwork"
```

Chạy máy chủ:

```bash
uvicorn backend.main:app --reload
```

Tài liệu API: `http://localhost:8000/docs`

### 5.2. Sinh dữ liệu mẫu

> ⚠️ **Lệnh này xoá toàn bộ dữ liệu hiện có** trong cơ sở dữ liệu đang trỏ tới
> (`users`, `departments`, `tasks`, `comments`, `notifications`, `audit_logs`,
> `kpi_task_catalog`, `kpi_evaluations`). Hãy kiểm tra `MONGO_URI` và `DB_NAME`
> trước khi chạy.

```bash
python -m backend.services.seeder
```

Dữ liệu mẫu phủ đủ: 3 nhóm độ phức tạp, 6 mức chất lượng, 6 mức tiến độ, 3 nhóm xếp loại KPI,
5 trạng thái quy trình, cả tập thể và cá nhân, 7 tháng liên tiếp để tính KPI quý/năm.

### 5.3. Frontend

```bash
cd frontend && npm install && npm run dev
```

### 5.4. Kiểm thử

```bash
pip install -r backend/requirements-dev.txt
pytest -v
```

47 test kiểm chứng công thức tính điểm, trong đó có test tái tạo đúng **ví dụ mẫu tại
Phụ lục** (đồng chí A tháng 6/2026: KPI = 97,97; tổng điểm xếp loại = 98,579).
