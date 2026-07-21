# TÀI LIỆU DỰ ÁN

# SMARTWORK AI – PHẦN MỀM THEO DÕI TIẾN ĐỘ CÔNG VIỆC VÀ TỐI ƯU HÓA PHÂN BỔ NGUỒN LỰC ỨNG DỤNG TRÍ TUỆ NHÂN TẠO

---

> **Cuộc thi**: Ứng dụng Trí tuệ nhân tạo tỉnh Đắk Lắk 2026  
> **Lĩnh vực**: AI trong cải cách hành chính và chính quyền số  
> **Phiên bản**: 1.0.0  
> **Ngày lập**: 24/06/2026

---

## MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Vấn đề thực tiễn và giải pháp](#2-vấn-đề-thực-tiễn-và-giải-pháp)
3. [Kiến trúc hệ thống](#3-kiến-trúc-hệ-thống)
4. [Công nghệ sử dụng](#4-công-nghệ-sử-dụng)
5. [Cấu trúc mã nguồn](#5-cấu-trúc-mã-nguồn)
6. [Cơ sở dữ liệu](#6-cơ-sở-dữ-liệu)
7. [Các mô hình AI chi tiết](#7-các-mô-hình-ai-chi-tiết)
8. [Chức năng hệ thống](#8-chức-năng-hệ-thống)
9. [API Endpoints](#9-api-endpoints)
10. [Giao diện người dùng](#10-giao-diện-người-dùng)
11. [Hướng dẫn cài đặt và chạy](#11-hướng-dẫn-cài-đặt-và-chạy)
12. [Mã nguồn chi tiết](#12-mã-nguồn-chi-tiết)
13. [Tính khả thi và khả năng mở rộng](#13-tính-khả-thi-và-khả-năng-mở-rộng)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Tên sản phẩm

**SmartWork AI** – Phần mềm theo dõi tiến độ công việc và tối ưu hóa phân bổ nguồn lực ứng dụng Trí tuệ nhân tạo.

### 1.2 Mục tiêu

Xây dựng một hệ thống web quản lý dự án nội bộ dành cho các cơ quan nhà nước, tích hợp **3 mô hình AI** để:

- **Dự báo** khả năng hoàn thành đúng hạn của từng dự án.
- **Tối ưu hóa** việc phân bổ nhân lực dựa trên kỹ năng, workload và hiệu suất lịch sử.
- **Phân tích** hiệu suất làm việc của từng nhân viên một cách khách quan, dựa trên dữ liệu.

### 1.3 Đối tượng sử dụng

- Lãnh đạo cơ quan, đơn vị (theo dõi tổng quan, ra quyết định).
- Trưởng phòng (quản lý dự án, phân công công việc).
- Nhân viên (cập nhật tiến độ, xem công việc được giao).

### 1.4 Phạm vi ứng dụng

Hệ thống được thiết kế phù hợp với **bối cảnh cơ quan nhà nước tỉnh Đắk Lắk**, với dữ liệu mẫu mô phỏng hoạt động của các phòng ban trực thuộc.

---

## 2. VẤN ĐỀ THỰC TIỄN VÀ GIẢI PHÁP

### 2.1 Thực trạng

| Vấn đề                 | Mô tả                                                            |
| ---------------------- | ---------------------------------------------------------------- |
| Quản lý thủ công       | Theo dõi công việc qua Excel, giấy tờ → khó tổng hợp, dễ sai sót |
| Phân công cảm tính     | Giao việc dựa trên kinh nghiệm cá nhân → không tối ưu nguồn lực  |
| Không có dự báo        | Chỉ phát hiện trễ deadline khi đã quá muộn                       |
| Đánh giá chủ quan      | Đánh giá nhân viên thiếu cơ sở dữ liệu khách quan                |
| Thiếu hệ thống báo cáo | Khó theo dõi tiến độ tổng thể nhiều dự án cùng lúc               |

### 2.2 Giải pháp SmartWork AI

| Giải pháp                          | Công nghệ AI                                           |
| ---------------------------------- | ------------------------------------------------------ |
| Dashboard tổng quan thời gian thực | Tổng hợp dữ liệu tự động                               |
| AI dự báo deadline                 | Weighted Multi-Factor Scoring (mô phỏng Random Forest) |
| AI phân công thông minh            | Multi-Criteria Decision Making (MCDM)                  |
| AI đánh giá hiệu suất              | Composite Scoring + Clustering                         |
| Cảnh báo rủi ro tự động            | Rule-based alerting kết hợp AI scoring                 |

### 2.3 Tính mới và sáng tạo

- **Không sử dụng đơn thuần API có sẵn**: Tất cả 3 mô hình AI đều được xây dựng từ đầu bằng thuật toán tự thiết kế.
- **Kết hợp đa mô hình**: 3 AI models hoạt động liên kết, bổ trợ lẫn nhau.
- **Dữ liệu bối cảnh địa phương**: Mô phỏng đúng cơ cấu tổ chức cơ quan nhà nước Đắk Lắk.
- **Giải thích được (Explainable AI)**: Mỗi kết quả AI đều kèm lý do, trọng số các yếu tố → người dùng hiểu được tại sao AI đề xuất như vậy.

---

## 3. KIẾN TRÚC HỆ THỐNG

```
┌─────────────────────────────────────────────────────────────┐
│                     TRÌNH DUYỆT WEB                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ HTML5    │  │ CSS3     │  │ JS       │  │ Chart.js   │  │
│  │ Dashboard│  │ Dark     │  │ App      │  │ Biểu đồ   │  │
│  │ Layout   │  │ Glassmor │  │ Logic    │  │ Trực quan  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │  HTTP REST API (JSON)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              main.py – REST API Server                 │ │
│  │  /api/dashboard  /api/projects  /api/tasks             │ │
│  │  /api/employees  /api/ai/*      /api/departments       │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                 │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │              AI ENGINE (ai_engine.py)                   │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │ │
│  │  │ Deadline     │ │ Resource     │ │ Performance    │  │ │
│  │  │ Predictor    │ │ Optimizer    │ │ Analyzer       │  │ │
│  │  │ (Dự báo)     │ │ (Phân bổ)    │ │ (Hiệu suất)   │  │ │
│  │  └──────────────┘ └──────────────┘ └────────────────┘  │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                 │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │           DATABASE (SQLite – database.py)               │ │
│  │  departments │ employees │ projects │ tasks │ perf_logs  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Đặc điểm kiến trúc:**

- **Monolithic (All-in-one)**: Backend phục vụ luôn Frontend → chỉ cần 1 lệnh để chạy toàn bộ hệ thống.
- **Stateless API**: Frontend giao tiếp với Backend qua REST API chuẩn JSON.
- **Embedded Database**: SQLite lưu trữ dữ liệu trong 1 file duy nhất → dễ di chuyển, deploy.

---

## 4. CÔNG NGHỆ SỬ DỤNG

### 4.1 Backend

| Công nghệ    | Phiên bản      | Vai trò                   |
| ------------ | -------------- | ------------------------- |
| **Python**   | 3.12           | Ngôn ngữ lập trình chính  |
| **FastAPI**  | 0.138.0        | Web framework (REST API)  |
| **Uvicorn**  | 0.49.0         | ASGI Server chạy ứng dụng |
| **SQLite**   | 3.x (built-in) | Cơ sở dữ liệu nhúng       |
| **Pydantic** | 2.13.4         | Xác thực dữ liệu đầu vào  |

### 4.2 Frontend

| Công nghệ                         | Phiên bản | Vai trò                                       |
| --------------------------------- | --------- | --------------------------------------------- |
| **HTML5**                         | —         | Cấu trúc giao diện                            |
| **CSS3**                          | —         | Thiết kế giao diện (Dark Glassmorphism)       |
| **JavaScript** (ES6+)             | —         | Logic tương tác, gọi API                      |
| **Chart.js**                      | 4.4.2     | Biểu đồ trực quan (Doughnut, Bar, Polar Area) |
| **Be Vietnam Pro** (Google Fonts) | —         | Font tiếng Việt chuyên nghiệp                 |

### 4.3 AI/ML

| Thuật toán                         | Mô hình             | Ứng dụng                            |
| ---------------------------------- | ------------------- | ----------------------------------- |
| **Weighted Multi-Factor Scoring**  | DeadlinePredictor   | Dự báo xác suất hoàn thành đúng hạn |
| **Multi-Criteria Decision Making** | ResourceOptimizer   | Đề xuất nhân viên phù hợp nhất      |
| **Composite Scoring + Clustering** | PerformanceAnalyzer | Phân tích và xếp hạng hiệu suất     |

---

## 5. CẤU TRÚC MÃ NGUỒN

```
smartwork-ai/
│
├── backend/                          # Mã nguồn Backend
│   ├── main.py                       # FastAPI app – REST API endpoints (314 dòng)
│   ├── requirements.txt              # Danh sách thư viện Python
│   ├── smartwork.db                  # Database SQLite (tự sinh khi chạy)
│   ├── venv/                         # Môi trường ảo Python
│   └── models/
│       ├── __init__.py               # Package marker
│       ├── database.py               # Schema + dữ liệu mẫu Đắk Lắk (243 dòng)
│       └── ai_engine.py              # 3 mô hình AI (374 dòng)
│
├── frontend/                         # Mã nguồn Frontend
│   ├── index.html                    # Giao diện chính – Dashboard (~ 350 dòng)
│   ├── css/
│   │   └── style.css                 # Thiết kế Dark Glassmorphism (~ 650 dòng)
│   └── js/
│       ├── app.js                    # Logic ứng dụng chính (~ 500 dòng)
│       └── charts.js                 # Biểu đồ Chart.js (~ 200 dòng)
│
└── TÀI_LIỆU_DỰ_ÁN_SMARTWORK_AI.md  # Tài liệu này
```

**Tổng quy mô mã nguồn**: ~2.300 dòng code (không tính thư viện bên ngoài).

---

## 6. CƠ SỞ DỮ LIỆU

### 6.1 Sơ đồ quan hệ (ERD)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ departments  │     │  employees   │     │   projects   │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)      │◄────│ dept_id (FK) │     │ id (PK)      │
│ name         │     │ id (PK)      │     │ name         │
│ code         │     │ name         │     │ dept_id (FK) │──►┐
└──────────────┘     │ position     │     │ priority     │   │
                     │ skills (JSON)│     │ status       │   │
                     │ experience   │     │ start_date   │   │
                     └──────┬───────┘     │ end_date     │   │
                            │             │ progress     │   │
                            │             │ description  │   │
                            │             └──────┬───────┘   │
                            │                    │           │
                     ┌──────▼────────────────────▼───────┐   │
                     │            tasks                   │   │
                     ├────────────────────────────────────┤   │
                     │ id (PK)                            │   │
                     │ project_id (FK) ───────────────────┘   │
                     │ assignee_id (FK) ──────────────────────┘
                     │ name                               │
                     │ status                             │
                     │ priority                           │
                     │ start_date / due_date              │
                     │ completed_date                     │
                     │ progress (0-100)                   │
                     │ estimated_hours / actual_hours     │
                     │ skills_required (JSON)             │
                     └────────────────┬───────────────────┘
                                      │
                     ┌────────────────▼───────────────────┐
                     │       performance_logs             │
                     ├────────────────────────────────────┤
                     │ id (PK)                            │
                     │ employee_id (FK)                   │
                     │ task_id (FK)                       │
                     │ on_time (0/1)                      │
                     │ quality_score (1.0 – 5.0)          │
                     │ effort_score (1.0 – 5.0)           │
                     │ log_date                           │
                     └────────────────────────────────────┘
```

### 6.2 Chi tiết các bảng

#### Bảng `departments` – Phòng ban

| Cột  | Kiểu         | Mô tả                                        |
| ---- | ------------ | -------------------------------------------- |
| id   | INTEGER (PK) | Mã phòng ban                                 |
| name | TEXT         | Tên đầy đủ (VD: "Phòng Công nghệ thông tin") |
| code | TEXT         | Mã viết tắt (VD: "CNTT")                     |

**Dữ liệu mẫu**: 5 phòng ban (HC, CNTT, KHTC, PC, TCNS).

#### Bảng `employees` – Nhân viên

| Cột        | Kiểu         | Mô tả                                            |
| ---------- | ------------ | ------------------------------------------------ |
| id         | INTEGER (PK) | Mã nhân viên                                     |
| name       | TEXT         | Họ tên                                           |
| dept_id    | INTEGER (FK) | Thuộc phòng ban nào                              |
| position   | TEXT         | Chức vụ (Trưởng phòng / Chuyên viên / Nhân viên) |
| skills     | TEXT (JSON)  | Danh sách kỹ năng (mảng JSON)                    |
| experience | INTEGER      | Số năm kinh nghiệm                               |

**Dữ liệu mẫu**: 15 nhân viên, phân bố đều 5 phòng ban.

#### Bảng `projects` – Dự án

| Cột         | Kiểu         | Mô tả                                                   |
| ----------- | ------------ | ------------------------------------------------------- |
| id          | INTEGER (PK) | Mã dự án                                                |
| name        | TEXT         | Tên dự án                                               |
| dept_id     | INTEGER (FK) | Phòng ban phụ trách                                     |
| priority    | TEXT         | Mức ưu tiên (Cao / Trung bình / Thấp)                   |
| status      | TEXT         | Trạng thái (Chưa bắt đầu / Đang thực hiện / Hoàn thành) |
| start_date  | TEXT         | Ngày bắt đầu (ISO format)                               |
| end_date    | TEXT         | Ngày deadline (ISO format)                              |
| progress    | INTEGER      | Tiến độ tổng thể (0-100%)                               |
| description | TEXT         | Mô tả chi tiết dự án                                    |

**Dữ liệu mẫu**: 8 dự án theo bối cảnh chuyển đổi số tỉnh Đắk Lắk.

#### Bảng `tasks` – Công việc

| Cột                   | Kiểu         | Mô tả                        |
| --------------------- | ------------ | ---------------------------- |
| id                    | INTEGER (PK) | Mã task                      |
| project_id            | INTEGER (FK) | Thuộc dự án nào              |
| name                  | TEXT         | Tên công việc                |
| assignee_id           | INTEGER (FK) | Người được giao              |
| status                | TEXT         | Trạng thái                   |
| priority              | TEXT         | Mức ưu tiên                  |
| start_date / due_date | TEXT         | Thời gian bắt đầu / deadline |
| completed_date        | TEXT         | Ngày hoàn thành thực tế      |
| progress              | INTEGER      | Tiến độ (0-100%)             |
| estimated_hours       | INTEGER      | Giờ ước tính                 |
| actual_hours          | INTEGER      | Giờ thực tế                  |
| skills_required       | TEXT (JSON)  | Kỹ năng yêu cầu              |

**Dữ liệu mẫu**: 40 tasks phân bổ vào 8 dự án.

#### Bảng `performance_logs` – Nhật ký hiệu suất

| Cột           | Kiểu         | Mô tả                                       |
| ------------- | ------------ | ------------------------------------------- |
| id            | INTEGER (PK) | Mã bản ghi                                  |
| employee_id   | INTEGER (FK) | Mã nhân viên                                |
| task_id       | INTEGER (FK) | Mã task liên quan                           |
| on_time       | INTEGER      | Hoàn thành đúng hạn (0 = trễ, 1 = đúng hạn) |
| quality_score | REAL         | Điểm chất lượng (1.0 – 5.0)                 |
| effort_score  | REAL         | Điểm nỗ lực (1.0 – 5.0)                     |
| log_date      | TEXT         | Ngày ghi nhận                               |

---

## 7. CÁC MÔ HÌNH AI CHI TIẾT

### 7.1 Model 1: DeadlinePredictor – Dự báo khả năng hoàn thành đúng hạn

#### Mục đích

Dự đoán **xác suất (%)** một dự án sẽ hoàn thành đúng deadline, từ đó cảnh báo sớm các dự án có nguy cơ trễ hạn.

#### Thuật toán: Weighted Multi-Factor Scoring

Mô phỏng đầu ra của Random Forest bằng công thức tính điểm có trọng số:

```
Score = 0.35 × Tiến_độ + 0.25 × Thời_gian + 0.20 × Lịch_sử + 0.10 × Workload + 0.10 × Phức_tạp
```

#### Các yếu tố đầu vào (Features)

| Yếu tố                 | Trọng số | Cách tính                             | Ý nghĩa                                    |
| ---------------------- | -------- | ------------------------------------- | ------------------------------------------ |
| **Tiến độ hiện tại**   | 35%      | `progress / 100`                      | Phần trăm công việc đã hoàn thành          |
| **Thời gian còn lại**  | 25%      | `min(1, days_remaining / 90)`         | Chuẩn hóa số ngày còn lại (tối đa 90 ngày) |
| **Lịch sử hoàn thành** | 20%      | `on_time_tasks / total_tasks`         | Tỷ lệ hoàn thành đúng hạn lịch sử          |
| **Workload nhóm**      | 10%      | `1 - (in_progress / remaining)`       | Số task đang thực hiện so với tổng còn lại |
| **Độ phức tạp**        | 10%      | `1 - min(0.3, (avg_hours - 8) / 160)` | Dựa trên giờ ước tính trung bình           |

#### Đầu ra

| Trường        | Mô tả                                                                |
| ------------- | -------------------------------------------------------------------- |
| `probability` | Xác suất hoàn thành đúng hạn (2% – 98%)                              |
| `risk_level`  | Mức rủi ro: **Thấp** (≥75%), **Trung bình** (50-74%), **Cao** (<50%) |
| `advice`      | Lời khuyên cụ thể cho người quản lý                                  |
| `factors`     | Chi tiết từng yếu tố đã dùng để tính                                 |

#### Ví dụ minh họa

```
Dự án: "Hệ thống Cổng Dịch vụ Công tỉnh Đắk Lắk"
├── Tiến độ: 65%        → 0.35 × 0.65 = 0.2275
├── Còn lại: 30 ngày    → 0.25 × 0.33 = 0.0833
├── Lịch sử: 60%        → 0.20 × 0.60 = 0.1200
├── Workload: 1 in-prog → 0.10 × 0.50 = 0.0500
├── Phức tạp: 24h avg   → 0.10 × 0.90 = 0.0900
│
└── TỔNG = 0.5708 → 57.1% → Rủi ro: TRUNG BÌNH
    Lời khuyên: "Cần tăng tốc. Còn 30 ngày – hãy kiểm tra lại phân công nhân lực."
```

#### Code (trích từ `ai_engine.py`)

```python
class DeadlinePredictor:
    def predict(self, project_id: int) -> dict:
        # Lấy dữ liệu dự án
        progress = project["progress"] / 100.0
        days_remaining = (end_date - date.today()).days
        history_rate = self._get_project_history_rate(project_id)

        # Feature engineering
        days_norm = max(0, min(1, days_remaining / 90.0))
        workload_factor = min(1.0, in_progress / max(1, total_tasks - done_tasks))
        complexity_penalty = 1.0 - min(0.3, (avg_hours - 8) / 160.0)

        # Weighted formula
        score = (
            0.35 * progress +
            0.25 * days_norm +
            0.20 * history_rate +
            0.10 * (1.0 - workload_factor) +
            0.10 * complexity_penalty
        )

        probability = round(min(0.98, max(0.02, score)) * 100, 1)

        # Phân loại rủi ro
        if probability >= 75:
            risk = "Thấp"
        elif probability >= 50:
            risk = "Trung bình"
        else:
            risk = "Cao"

        return {
            "probability": probability,
            "risk_level": risk,
            "advice": advice,
            "factors": {...}
        }
```

---

### 7.2 Model 2: ResourceOptimizer – Tối ưu phân bổ nguồn lực

#### Mục đích

Khi có một công việc mới cần phân công, AI sẽ **đề xuất top 3 nhân viên phù hợp nhất** dựa trên phân tích đa tiêu chí.

#### Thuật toán: Multi-Criteria Decision Making (MCDM)

```
Score = 0.40 × Kỹ_năng + 0.30 × Workload + 0.20 × Hiệu_suất + 0.10 × Kinh_nghiệm + Bonus_cùng_phòng
```

#### Các tiêu chí đánh giá

| Tiêu chí              | Trọng số | Cách tính                                        | Ý nghĩa                         |
| --------------------- | -------- | ------------------------------------------------ | ------------------------------- | --- | -------------- | --- | ------------------ |
| **Kỹ năng phù hợp**   | 40%      | `                                                | skills_chung                    | /   | skills_yêu_cầu | `   | Tỷ lệ kỹ năng khớp |
| **Workload hiện tại** | 30%      | `max(0, 1 - tasks_hiện_tại × 0.15)`              | Phạt nếu đang quá tải (>6 task) |
| **Hiệu suất lịch sử** | 20%      | `(quality×0.4 + effort×0.3 + on_time×5×0.3) / 5` | Điểm hiệu suất tổng hợp         |
| **Kinh nghiệm**       | 10%      | `min(1, years / 10)`                             | Chuẩn hóa theo 10 năm           |
| **Bonus cùng phòng**  | +5%      | Cộng thêm nếu cùng phòng ban                     | Ưu tiên phối hợp nội bộ         |

#### Đầu ra

| Trường           | Mô tả                          |
| ---------------- | ------------------------------ |
| `name`           | Tên nhân viên                  |
| `score`          | Điểm phù hợp tổng hợp (0-100%) |
| `skill_match`    | % kỹ năng khớp                 |
| `workload`       | Số task hiện tại               |
| `performance`    | Điểm hiệu suất /5              |
| `matched_skills` | Danh sách kỹ năng khớp         |
| `missing_skills` | Danh sách kỹ năng còn thiếu    |

#### Ví dụ minh họa

```
Yêu cầu: Cần nhân viên có kỹ năng "Lập trình Python" + "Trí tuệ nhân tạo"

Kết quả AI:
🥇 #1 Phạm Thị Dung – 84.0% phù hợp
    ✓ Lập trình Python, ✓ Trí tuệ nhân tạo
    Workload: 2 task | Hiệu suất: 4.2/5

🥈 #2 Nguyễn Văn An – 80.7% phù hợp
    ✓ Lập trình Python, ✓ Trí tuệ nhân tạo
    Workload: 3 task | Hiệu suất: 4.0/5

🥉 #3 Ngô Quốc Hùng – 56.2% phù hợp
    ✗ Thiếu cả 2 kỹ năng, nhưng có hiệu suất cao và ít workload
```

#### Code (trích từ `ai_engine.py`)

```python
class ResourceOptimizer:
    def recommend(self, required_skills, project_dept_id=None, top_k=3):
        for emp in employees:
            emp_skills = set(json.loads(emp["skills"]))
            skill_match = len(required_skills_set & emp_skills) / max(1, len(required_skills_set))

            workload = self._get_employee_workload(emp["id"])
            workload_score = max(0, 1.0 - workload * 0.15)

            perf_score = self._get_employee_performance(emp["id"]) / 5.0
            exp_score = min(1.0, emp["experience"] / 10.0)

            dept_bonus = 0.05 if (project_dept_id and emp["dept_id"] == project_dept_id) else 0

            final_score = (
                0.40 * skill_match +
                0.30 * workload_score +
                0.20 * perf_score +
                0.10 * exp_score +
                dept_bonus
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
```

---

### 7.3 Model 3: PerformanceAnalyzer – Phân tích hiệu suất nhân viên

#### Mục đích

Đánh giá **hiệu suất làm việc** của từng nhân viên một cách khách quan dựa trên dữ liệu, phân nhóm (clustering) để nhận diện nhân viên xuất sắc và cần cải thiện.

#### Thuật toán: Composite Scoring + Rule-based Clustering

```
Performance_Score = On_time × 35 + (Quality / 5) × 35 + (Effort / 5) × 20 + Completion_rate × 10
```

#### Các chỉ số đo lường

| Chỉ số                   | Trọng số | Nguồn dữ liệu                    | Thang đo  |
| ------------------------ | -------- | -------------------------------- | --------- |
| **Tỷ lệ đúng hạn**       | 35%      | `performance_logs.on_time`       | 0.0 – 1.0 |
| **Chất lượng công việc** | 35%      | `performance_logs.quality_score` | 1.0 – 5.0 |
| **Mức độ nỗ lực**        | 20%      | `performance_logs.effort_score`  | 1.0 – 5.0 |
| **Tỷ lệ hoàn thành**     | 10%      | `tasks.done / tasks.total`       | 0.0 – 1.0 |

#### Phân nhóm (Clustering)

| Nhóm                     | Điều kiện       | Biểu tượng | Màu               |
| ------------------------ | --------------- | ---------- | ----------------- |
| **Hiệu suất cao**        | Score ≥ 70      | 🏆         | Xanh lá (#10b981) |
| **Hiệu suất trung bình** | 45 ≤ Score < 70 | 📈         | Vàng (#f59e0b)    |
| **Cần cải thiện**        | Score < 45      | ⚠️         | Đỏ (#ef4444)      |

#### Biểu đồ Radar (5 chiều)

Mỗi nhân viên được đánh giá trên 5 chiều năng lực:

```
         Đúng hạn (0-5)
              ▲
             / \
            /   \
  Hoàn thành     Chất lượng
    (0-5)    \   /    (0-5)
              \ /
     Kinh nghiệm ─── Nỗ lực
        (0-5)         (0-5)
```

#### Ví dụ minh họa

```
Nhân viên: Đinh Thị Lan (Chuyên viên, Phòng KHTC)
├── Đúng hạn: 5.0/5
├── Chất lượng: 4.5/5
├── Nỗ lực: 4.2/5
├── Kinh nghiệm: 2.5/5 (5 năm)
├── Hoàn thành: 5.0/5
│
└── TỔNG ĐIỂM: 95.1 → 🏆 Hiệu suất cao
```

#### Code (trích từ `ai_engine.py`)

```python
class PerformanceAnalyzer:
    def analyze_employee(self, employee_id):
        # Tính điểm tổng hợp
        perf_score = (
            on_time_rate * 35 +
            (q_score / 5.0) * 35 +
            (e_score / 5.0) * 20 +
            completion_rate * 10
        )

        # Phân nhóm (Clustering)
        if perf_score >= 70:
            cluster = "Hiệu suất cao"
        elif perf_score >= 45:
            cluster = "Hiệu suất trung bình"
        else:
            cluster = "Cần cải thiện"

        # Radar 5 chiều
        radar = {
            "Đúng hạn": round(on_time_rate * 5, 1),
            "Chất lượng": round(q_score, 1),
            "Nỗ lực": round(e_score, 1),
            "Kinh nghiệm": round(min(5, experience / 2.0), 1),
            "Hoàn thành": round(completion_rate * 5, 1),
        }

        return {
            "performance_score": perf_score,
            "cluster": cluster,
            "radar": radar,
            ...
        }
```

---

## 8. CHỨC NĂNG HỆ THỐNG

### 8.1 Dashboard Tổng quan

| Chức năng                   | Mô tả                                                                          |
| --------------------------- | ------------------------------------------------------------------------------ |
| Thẻ thống kê tổng quan      | Hiển thị 4 KPI: Tổng dự án, Công việc hoàn thành, Nhân sự, Task đang thực hiện |
| Danh sách dự án             | Hiển thị tiến độ, deadline, phòng ban phụ trách, mức ưu tiên                   |
| Cảnh báo AI                 | Hiển thị các dự án bị AI đánh giá rủi ro CAO (xác suất đúng hạn < 50%)         |
| Biểu đồ tỷ lệ hoàn thành    | Biểu đồ Doughnut: Hoàn thành / Đang thực hiện / Chưa bắt đầu                   |
| Biểu đồ xác suất AI         | Biểu đồ ngang so sánh xác suất đúng hạn của tất cả dự án                       |
| Biểu đồ hiệu suất phòng ban | Biểu đồ Polar Area: điểm hiệu suất TB mỗi phòng ban                            |

### 8.2 Quản lý Dự án

| Chức năng              | Mô tả                                                                   |
| ---------------------- | ----------------------------------------------------------------------- |
| Xem danh sách dự án    | Bảng data table: tên, phòng ban, ưu tiên, trạng thái, tiến độ, deadline |
| Lọc theo trạng thái    | Filter: Tất cả / Đang thực hiện / Hoàn thành / Chưa bắt đầu             |
| Chi tiết dự án (Modal) | Popup hiển thị: 3 thẻ KPI + cảnh báo AI + danh sách task con            |
| AI dự báo kèm theo     | Mỗi dự án tự động kèm xác suất đúng hạn và lời khuyên                   |

### 8.3 Quản lý Công việc

| Chức năng             | Mô tả                                                                     |
| --------------------- | ------------------------------------------------------------------------- |
| Xem danh sách task    | Bảng: tên, dự án, người thực hiện, ưu tiên, trạng thái, deadline, tiến độ |
| Lọc theo trạng thái   | Filter Đang thực hiện / Hoàn thành / Chưa bắt đầu                         |
| Cập nhật trạng thái   | Dropdown trực tiếp trong bảng: chuyển trạng thái → gọi API PATCH          |
| Thêm task mới (Modal) | Form: Tên, Dự án, Ưu tiên, Deadline, Giờ ước tính, Phân công              |

### 8.4 Quản lý Nhân sự

| Chức năng                  | Mô tả                                                                          |
| -------------------------- | ------------------------------------------------------------------------------ |
| Lưới thẻ nhân viên         | Card grid: avatar, tên, chức vụ, phòng ban, điểm AI, biểu đồ radar mini        |
| Lọc theo phòng ban         | Dropdown chọn phòng ban                                                        |
| Chi tiết nhân viên (Modal) | 3 KPI + phân loại AI + radar chi tiết 5 chiều + danh sách kỹ năng + task stats |

### 8.5 AI Dự báo Deadline

| Chức năng          | Mô tả                                                                |
| ------------------ | -------------------------------------------------------------------- |
| Danh sách dự báo   | Card cho mỗi dự án: xác suất %, mức rủi ro, ngày còn lại, lời khuyên |
| Biểu đồ so sánh    | Bar chart kép: Xác suất AI vs Tiến độ hiện tại                       |
| Giải thích mô hình | Panel hiển thị 5 yếu tố và trọng số → Explainable AI                 |

### 8.6 AI Tối ưu Nguồn lực

| Chức năng               | Mô tả                                                                    |
| ----------------------- | ------------------------------------------------------------------------ |
| Chọn kỹ năng yêu cầu    | Checkbox grid 15 kỹ năng                                                 |
| Chọn phòng ban ưu tiên  | Dropdown phòng ban (optional)                                            |
| Nút "Chạy AI Phân tích" | Gọi API → hiển thị kết quả                                               |
| Kết quả Top 3           | Card xếp hạng 🥇🥈🥉: tên, điểm, kỹ năng khớp/thiếu, workload, hiệu suất |
| Workload Heatmap        | Thanh ngang thể hiện mức tải của từng nhân viên                          |

### 8.7 AI Phân tích Hiệu suất

| Chức năng         | Mô tả                                                                  |
| ----------------- | ---------------------------------------------------------------------- |
| Thẻ KPI phòng ban | Điểm TB, số người, số nhân viên xuất sắc cho mỗi phòng ban             |
| Bảng xếp hạng     | Table: thứ hạng, nhân viên, điểm AI, đúng hạn %, chất lượng, phân loại |
| Lọc theo nhóm     | Filter: Tất cả / Hiệu suất cao / Trung bình / Cần cải thiện            |
| Biểu đồ phân bố   | Doughnut chart: Tỷ lệ 3 nhóm hiệu suất                                 |
| Panel chi tiết    | Nhấn vào nhân viên → hiện radar 5 chiều bên phải                       |

---

## 9. API ENDPOINTS

### 9.1 Tổng quan

| Method | Endpoint                                 | Mô tả                                           |
| ------ | ---------------------------------------- | ----------------------------------------------- |
| GET    | `/`                                      | Trả về trang HTML giao diện chính               |
| GET    | `/api/dashboard`                         | Dữ liệu tổng quan dashboard + AI alerts         |
| GET    | `/api/projects`                          | Danh sách tất cả dự án                          |
| GET    | `/api/projects/{id}`                     | Chi tiết dự án + danh sách task + AI prediction |
| GET    | `/api/employees`                         | Danh sách nhân viên + workload                  |
| GET    | `/api/employees/{id}/performance`        | AI phân tích hiệu suất 1 nhân viên              |
| GET    | `/api/departments`                       | Danh sách phòng ban                             |
| GET    | `/api/skills`                            | Danh sách tất cả kỹ năng                        |
| POST   | `/api/tasks`                             | Tạo task mới                                    |
| PATCH  | `/api/tasks/{id}`                        | Cập nhật trạng thái / tiến độ task              |
| GET    | `/api/ai/deadline-prediction`            | AI dự báo tất cả dự án                          |
| GET    | `/api/ai/deadline-prediction/{id}`       | AI dự báo 1 dự án                               |
| POST   | `/api/ai/recommend-resource?skills=...`  | AI đề xuất nhân viên phù hợp                    |
| GET    | `/api/ai/performance`                    | AI xếp hạng hiệu suất toàn bộ nhân viên         |
| GET    | `/api/ai/performance/{id}`               | AI phân tích chi tiết 1 nhân viên               |
| GET    | `/api/ai/performance/department-summary` | AI tổng hợp hiệu suất theo phòng ban            |

### 9.2 Ví dụ Request/Response

#### GET `/api/dashboard`

```json
{
  "stats": {
    "total_projects": 8,
    "completed_projects": 2,
    "active_projects": 6,
    "total_employees": 15,
    "active_tasks": 7,
    "total_tasks": 40,
    "done_tasks": 22,
    "completion_rate": 55.0
  },
  "projects": [...],
  "overdue_tasks": [...],
  "ai_alerts": [
    {
      "project_name": "Chuyển đổi số hồ sơ hành chính",
      "probability": 38.5,
      "risk_level": "Cao",
      "advice": "⚠️ Nguy cơ trễ deadline! Chỉ còn 15 ngày."
    }
  ],
  "predictions": [...]
}
```

#### POST `/api/ai/recommend-resource?skills=Lập trình Python,Trí tuệ nhân tạo&top_k=3`

```json
{
  "required_skills": ["Lập trình Python", "Trí tuệ nhân tạo"],
  "recommendations": [
    {
      "name": "Phạm Thị Dung",
      "score": 84.0,
      "skill_match": 100.0,
      "workload": 2,
      "performance": 4.2,
      "matched_skills": ["Lập trình Python", "Trí tuệ nhân tạo"],
      "missing_skills": []
    }
  ]
}
```

---

## 10. GIAO DIỆN NGƯỜI DÙNG

### 10.1 Phong cách thiết kế

- **Dark Glassmorphism**: Nền tối (#080c18) kết hợp hiệu ứng kính mờ (backdrop-filter: blur).
- **Font**: Be Vietnam Pro (Google Fonts) – font tiếng Việt chuyên nghiệp.
- **Bảng màu**:
  - Primary: #3b82f6 (Xanh dương)
  - Accent: #8b5cf6 (Tím)
  - Success: #10b981 (Xanh lá)
  - Warning: #f59e0b (Vàng cam)
  - Danger: #ef4444 (Đỏ)
- **Hiệu ứng**: Hover animations, glow effects, gradient backgrounds, smooth transitions.

### 10.2 Cấu trúc trang

```
┌──────────┬──────────────────────────────────────────┐
│          │           TOPBAR (AI Status, Actions)     │
│          ├──────────────────────────────────────────┤
│ SIDEBAR  │                                          │
│          │          PAGE CONTENT                     │
│ Logo     │                                          │
│ Nav      │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│ Menu     │  │ Stat │ │ Stat │ │ Stat │ │ Stat │    │
│          │  └──────┘ └──────┘ └──────┘ └──────┘    │
│ ─────    │                                          │
│ Dashboard│  ┌──────────────────┐ ┌────────────┐     │
│ Dự án    │  │ Projects List   │ │ AI Alerts  │     │
│ Công việc│  │                 │ │            │     │
│ Nhân sự  │  └──────────────────┘ └────────────┘     │
│ ─────    │                                          │
│ AI Dự báo│  ┌──────────────────┐ ┌────────────┐     │
│ AI Tối ưu│  │ Chart 1         │ │ Chart 2    │     │
│ AI H.suất│  └──────────────────┘ └────────────┘     │
│          │                                          │
│ ─────    │                                          │
│ User Info│                                          │
└──────────┴──────────────────────────────────────────┘
```

### 10.3 Các trang giao diện

| #   | Trang        | Mô tả                                                         |
| --- | ------------ | ------------------------------------------------------------- |
| 1   | Dashboard    | 4 KPI cards + Danh sách dự án + AI Alerts + 3 biểu đồ         |
| 2   | Dự án        | Bảng dữ liệu + filter + chi tiết modal                        |
| 3   | Công việc    | Bảng tasks + filter + cập nhật status + thêm task mới         |
| 4   | Nhân sự      | Card grid + filter phòng ban + chi tiết modal                 |
| 5   | AI Dự báo    | Prediction cards + bar chart kép + giải thích model           |
| 6   | AI Tối ưu    | Skill selector + Top 3 results + Workload heatmap             |
| 7   | AI Hiệu suất | Dept KPIs + ranking table + distribution chart + radar detail |

---

## 11. HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY

### 11.1 Yêu cầu hệ thống

- **Hệ điều hành**: macOS / Windows / Linux
- **Python**: 3.10 trở lên (khuyến nghị 3.12)
- **Trình duyệt**: Chrome / Firefox / Safari / Edge (phiên bản mới)
- **RAM**: Tối thiểu 2GB
- **Dung lượng**: ~50MB (bao gồm cả venv)

### 11.2 Cài đặt

```bash
# 1. Mở Terminal, di chuyển vào thư mục dự án
cd ~/Desktop/smartwork-ai/backend

# 2. Tạo môi trường ảo Python (nếu chưa có)
python3 -m venv venv

# 3. Kích hoạt môi trường ảo
source venv/bin/activate        # macOS/Linux
# hoặc
venv\Scripts\activate           # Windows

# 4. Cài đặt thư viện
pip install fastapi uvicorn python-multipart numpy
```

### 11.3 Khởi chạy

```bash
# Đảm bảo đang ở thư mục backend và đã kích hoạt venv
cd ~/Desktop/smartwork-ai/backend
source venv/bin/activate

# Chạy server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Kết quả mong đợi:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 11.4 Truy cập

Mở trình duyệt web, truy cập: **http://localhost:8000**

### 11.5 Dừng server

Nhấn `Ctrl + C` trong Terminal.

---

## 12. MÃ NGUỒN CHI TIẾT

### 12.1 Backend – `main.py` (REST API Server)

**Chức năng chính:**

- Khởi tạo FastAPI app với CORS middleware.
- Tự động khởi tạo database khi server start (`@app.on_event("startup")`).
- Phục vụ frontend (HTML/CSS/JS) qua StaticFiles.
- 16 REST API endpoints cho CRUD + AI.

**Các endpoint quan trọng:**

| Endpoint                          | Logic                                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------------- |
| `GET /api/dashboard`              | Query 6 thống kê từ DB + gọi `deadline_predictor.predict_all()` + lọc high_risk alerts |
| `GET /api/projects/{id}`          | Query project + tasks + gọi `deadline_predictor.predict(id)`                           |
| `POST /api/ai/recommend-resource` | Parse skills query param → gọi `resource_optimizer.recommend()`                        |
| `GET /api/ai/performance`         | Gọi `performance_analyzer.analyze_all()` → trả về list xếp hạng                        |
| `PATCH /api/tasks/{id}`           | Cập nhật status/progress → nếu "Hoàn thành" thì tự set progress=100                    |

---

### 12.2 Backend – `models/database.py` (Database & Seed Data)

**Chức năng chính:**

- Định nghĩa schema 5 bảng SQLite.
- Chứa dữ liệu mẫu giả lập bối cảnh Đắk Lắk.
- Hàm `init_db()` tự kiểm tra và seed dữ liệu nếu DB trống.

**Dữ liệu mẫu:**

| Bảng             | Số bản ghi | Mô tả                             |
| ---------------- | ---------- | --------------------------------- |
| departments      | 5          | 5 phòng ban cơ quan nhà nước      |
| employees        | 15         | 15 nhân viên với kỹ năng đa dạng  |
| projects         | 8          | 8 dự án chuyển đổi số thực tế     |
| tasks            | 40         | 5 tasks/dự án, đa dạng trạng thái |
| performance_logs | ~22        | Logs cho các task đã hoàn thành   |

**Danh sách 8 dự án mẫu:**

1. Hệ thống Cổng Dịch vụ Công tỉnh Đắk Lắk (65%, Cao)
2. Chuyển đổi số hồ sơ hành chính (45%, Cao)
3. Nâng cấp hạ tầng mạng nội bộ (78%, TB)
4. Phần mềm quản lý tài chính – ngân sách (100%, Hoàn thành)
5. Xây dựng quy trình ISO 9001:2015 (30%, TB)
6. Hệ thống camera giám sát thông minh (20%, Cao)
7. Ứng dụng SmartWork AI nội bộ (15%, Cao)
8. Đào tạo kỹ năng số cho cán bộ (100%, Hoàn thành)

---

### 12.3 Backend – `models/ai_engine.py` (AI Engine)

**3 class chính:**

| Class                 | Dòng code | Thuật toán                     |
| --------------------- | --------- | ------------------------------ |
| `DeadlinePredictor`   | 25-133    | Weighted Multi-Factor Scoring  |
| `ResourceOptimizer`   | 139-223   | Multi-Criteria Decision Making |
| `PerformanceAnalyzer` | 229-367   | Composite Scoring + Clustering |

**3 singleton instances** được khởi tạo cuối file và import vào `main.py`:

```python
deadline_predictor = DeadlinePredictor()
resource_optimizer = ResourceOptimizer()
performance_analyzer = PerformanceAnalyzer()
```

---

### 12.4 Frontend – `index.html`

**Cấu trúc HTML:**

- `<aside class="sidebar">` – Navigation sidebar 7 mục menu
- `<header class="topbar">` – AI status indicator + action buttons
- `<div class="page-content">` – 7 sections (ẩn/hiện theo menu)
- 3 modals: Thêm task, Chi tiết nhân viên, Chi tiết dự án

**Thư viện CDN:**

- Chart.js 4.4.2
- Chart.js DataLabels Plugin 2.2.0

---

### 12.5 Frontend – `css/style.css`

**Design System tokens:**

```css
--bg-base: #080c18 /* Nền chính */ --bg-card: rgba(255, 255, 255, 0.04)
  /* Card glassmorphism */ --primary: #3b82f6 /* Xanh dương chính */
  --accent: #8b5cf6 /* Tím accent */ --glass-border: rgba(255, 255, 255, 0.08)
  /* Viền kính mờ */;
```

**Responsive**: Hỗ trợ 3 breakpoint (1200px, 768px).

---

### 12.6 Frontend – `js/app.js`

**Kiến trúc code:**

- `state` object lưu trữ dữ liệu toàn cục.
- `navigate(section)` – Điều hướng SPA (Single Page Application).
- `apiFetch(path)` / `apiPost()` / `apiPatch()` – HTTP client helpers.
- Mỗi section có hàm `load...()` riêng, lazy-load khi lần đầu truy cập.
- `init()` – Khởi động: load Dashboard, gắn event listeners cho lazy-load.

---

### 12.7 Frontend – `js/charts.js`

**5 biểu đồ Chart.js:**

| Biểu đồ                | Loại           | Vị trí                                  |
| ---------------------- | -------------- | --------------------------------------- |
| `chart-completion`     | Doughnut       | Dashboard – Tỷ lệ hoàn thành            |
| `chart-deadline`       | Horizontal Bar | Dashboard – Xác suất đúng hạn           |
| `chart-dept`           | Polar Area     | Dashboard – Hiệu suất phòng ban         |
| `chart-prediction-bar` | Grouped Bar    | AI Dự báo – So sánh xác suất vs tiến độ |
| `chart-perf-dist`      | Doughnut       | AI Hiệu suất – Phân bố 3 nhóm           |

---

## 13. TÍNH KHẢ THI VÀ KHẢ NĂNG MỞ RỘNG

### 13.1 Tính khả thi triển khai thực tế

| Tiêu chí                 | Đánh giá                                                 |
| ------------------------ | -------------------------------------------------------- |
| **Chi phí triển khai**   | Rất thấp – chỉ cần 1 máy tính, không cần server đắt tiền |
| **Độ phức tạp kỹ thuật** | Trung bình – Python + HTML/JS phổ biến, dễ bảo trì       |
| **Thời gian triển khai** | Nhanh – có thể deploy trong 1 ngày                       |
| **Đào tạo người dùng**   | Dễ – giao diện trực quan, tiếng Việt hoàn toàn           |
| **Bảo mật dữ liệu**      | An toàn – database SQLite nằm cục bộ, không upload cloud |

### 13.2 Khả năng mở rộng

| Hướng phát triển            | Mô tả                                                                         |
| --------------------------- | ----------------------------------------------------------------------------- |
| **Thêm xác thực đăng nhập** | JWT authentication + phân quyền admin/user                                    |
| **Nâng cấp database**       | Chuyển từ SQLite sang PostgreSQL cho multi-user                               |
| **Tích hợp email/SMS**      | Gửi cảnh báo tự động khi AI phát hiện rủi ro                                  |
| **Mobile responsive**       | Đã hỗ trợ cơ bản, có thể phát triển thêm app mobile                           |
| **Tích hợp ML nâng cao**    | Thay thế scoring bằng sklearn Random Forest thực sự khi có đủ dữ liệu lịch sử |
| **Export báo cáo**          | Xuất PDF/Excel báo cáo hiệu suất định kỳ                                      |
| **Kết nối hệ thống**        | Tích hợp với Cổng dịch vụ công, hệ thống nhân sự hiện tại                     |

### 13.3 Đánh giá theo tiêu chí cuộc thi

| Tiêu chí vòng sơ khảo | Đáp ứng | Giải trình                                                         |
| --------------------- | ------- | ------------------------------------------------------------------ |
| Tính mới, sáng tạo    | ✅      | 3 AI models tự xây dựng, Explainable AI                            |
| Mức độ cấp thiết      | ✅      | Giải quyết bài toán quản lý công việc thực tế của cơ quan nhà nước |
| Mức độ ứng dụng AI    | ✅      | 3 mô hình AI hoạt động thực sự, có logic nghiệp vụ riêng           |
| Tính khả thi          | ✅      | Chạy được ngay, phù hợp điều kiện địa phương                       |
| Vận hành thực tế      | ✅      | Sản phẩm demo được, có dữ liệu mẫu bối cảnh Đắk Lắk                |

---

> **Tài liệu này được lập bởi nhóm phát triển SmartWork AI – Cuộc thi Ứng dụng AI tỉnh Đắk Lắk 2026.**

Quản lý: director_khdt (Pass: 123456)
Admin: admin (Pass: admin123)
Nhân viên: user0 đến user99 (Pass: 123456)
