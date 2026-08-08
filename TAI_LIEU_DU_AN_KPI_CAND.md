# TÀI LIỆU DỰ ÁN

# HỆ THỐNG TÍNH ĐIỂM KPI TRONG CÔNG AN NHÂN DÂN

**Tên viết tắt: KPI-CAND**

---

> **Căn cứ nghiệp vụ**: Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026 của Ban Thường vụ Đảng ủy
> Công an Trung ương về phương pháp tính điểm và sử dụng chỉ số đo lường (KPI) trong đánh giá,
> xếp loại chất lượng đối với tập thể, cá nhân trong Công an nhân dân.
> **Phiên bản**: 3.0.0
> **Bản triển khai thử nghiệm**: https://smartwork-ai-3u7e.vercel.app

---

## MỤC LỤC

1. [Tổng quan](#1-tổng-quan)
2. [Bài toán và giải pháp](#2-bài-toán-và-giải-pháp)
3. [Kiến trúc hệ thống](#3-kiến-trúc-hệ-thống)
4. [Công nghệ sử dụng](#4-công-nghệ-sử-dụng)
5. [Cấu trúc mã nguồn](#5-cấu-trúc-mã-nguồn)
6. [Mô hình dữ liệu](#6-mô-hình-dữ-liệu)
7. [Phương pháp tính điểm KPI](#7-phương-pháp-tính-điểm-kpi)
8. [Quy trình đánh giá 03 bước](#8-quy-trình-đánh-giá-03-bước)
9. [Bốn mô hình hỗ trợ ra quyết định](#9-bốn-mô-hình-hỗ-trợ-ra-quyết-định)
10. [Nhiệm vụ có độ mật](#10-nhiệm-vụ-có-độ-mật)
11. [Bảo mật và phân quyền](#11-bảo-mật-và-phân-quyền)
12. [API Endpoints](#12-api-endpoints)
13. [Giao diện người dùng](#13-giao-diện-người-dùng)
14. [Dữ liệu mẫu](#14-dữ-liệu-mẫu)
15. [Kiểm thử](#15-kiểm-thử)
16. [Cài đặt, chạy và triển khai](#16-cài-đặt-chạy-và-triển-khai)
17. [Tính khả thi và khả năng mở rộng](#17-tính-khả-thi-và-khả-năng-mở-rộng)

---

## 1. TỔNG QUAN

### 1.1 Tên sản phẩm

**Hệ thống tính điểm KPI trong Công an nhân dân**, viết tắt **KPI-CAND**.

### 1.2 Mục tiêu

Số hoá trọn vẹn phương pháp tính điểm KPI quy định tại Hướng dẫn số 20-HD/ĐUCA, bảo đảm bốn yêu cầu:

- **Đúng công thức** — điểm A, B, C, D, điểm KPI, điểm tiêu chí chung (E) và tổng điểm xếp loại
  được tính đúng quy định, kể cả cách làm tròn và cách ghi số thập phân của Phụ lục; tính đúng đắn
  được chứng minh bằng kiểm thử tự động chứ không bằng cam kết.
- **Đúng quy trình** — hồ sơ đánh giá đi đủ 03 bước theo đúng thẩm quyền từng cấp, không bỏ bước,
  không vượt cấp.
- **Giữ được dữ liệu gốc** — mỗi lần nhắc nhở tiến độ, mỗi lần yêu cầu hoàn thiện, chỉnh sửa đều được
  ghi nhận ngay tại thời điểm phát sinh, để điểm B và điểm C suy ra từ số liệu có thật.
- **Hỗ trợ ra quyết định sớm** — bốn mô hình chạy tại chỗ giúp lãnh đạo can thiệp ngay giữa kỳ,
  nhưng không mô hình nào được quyết định điểm KPI.

### 1.3 Đối tượng sử dụng

| Đối tượng | Vai trò | Việc chính |
|---|---|---|
| Quản trị hệ thống | `admin` | Quản lý đơn vị, tài khoản, nhật ký hệ thống, huấn luyện lại mô hình |
| Lãnh đạo đơn vị (người đứng đầu) | `director` | Duyệt Danh mục nhiệm vụ · **Bước 3** xác định điểm KPI · chấm tiêu chí chung (E) · rà soát chất lượng |
| Lãnh đạo, chỉ huy | `leader` | Giao nhiệm vụ · nhắc nhở tiến độ · yêu cầu chỉnh sửa · **Bước 2** thẩm định |
| Cán bộ, chiến sĩ | `staff` | Thực hiện nhiệm vụ · **Bước 1** tự đánh giá và đề xuất mức xếp loại |

### 1.4 Phạm vi

Áp dụng cho tập thể (đơn vị) và cá nhân. Cá nhân chia hai nhóm tính điểm: **là lãnh đạo, chỉ huy**
(KPI theo 04 tiêu chí, có điểm D) và **không giữ chức vụ lãnh đạo, chỉ huy** (KPI theo 03 tiêu chí).

---

## 2. BÀI TOÁN VÀ GIẢI PHÁP

### 2.1 Thực trạng

| Vấn đề | Mô tả |
|---|---|
| Tính điểm thủ công | Cộng dồn 3–4 tiêu chí trên bảng tính; một ô công thức sai kéo theo cả đơn vị sai mà khó phát hiện |
| Mất dữ liệu gốc của B và C | Số lần chỉnh sửa, số lần nhắc nhở chỉ diễn ra bằng lời; đến kỳ đánh giá không ai nhớ chính xác |
| Quy trình trên giấy | Không biết hồ sơ của ai đang ở bước nào, không lưu vết ai sửa số liệu nào |
| Tổng hợp quý, năm thủ công | KPI quý, năm là bình quân KPI tháng, phải cộng tay nhiều kỳ |
| Không phát hiện được chấm hình thức | Văn bản yêu cầu đánh giá "thực chất" nhưng không kèm cơ chế kiểm tra |
| Nhiệm vụ có độ mật | Không thể đưa nội dung lên hệ thống dùng chung, nhưng bỏ ra ngoài thì KPI thiếu |

### 2.2 Cách hệ thống đáp ứng

| Yêu cầu của Hướng dẫn | Cách đáp ứng |
|---|---|
| Xác định điểm từng công việc theo 03 nhóm độ phức tạp | Trang **Danh mục nhiệm vụ**, kiểm soát điểm nằm đúng dải của nhóm |
| Điểm B theo số lần hoàn thiện, chỉnh sửa | Thao tác *Yêu cầu hoàn thiện, chỉnh sửa* tăng `revision_count` |
| Điểm C theo số lần bị nhắc nhở | Thao tác *Nhắc nhở tiến độ* tăng `reminder_count` |
| Điểm D của lãnh đạo, chỉ huy | Tính tự động từ tỷ lệ cán bộ thuộc quyền đạt Nhóm 1 hoặc Nhóm 2 |
| KPI người đứng đầu không cao hơn KPI tập thể | Hệ thống tự áp mức trần khi xác định điểm |
| Tổng điểm xếp loại = E + KPI × 0,7 | Trang **Tiêu chí chung (E)** hiển thị tổng điểm tức thì |
| KPI quý, năm là bình quân KPI tháng | Hàm tổng hợp theo quý, theo năm trong `kpi_service.py` |
| Đánh giá bảo đảm thực chất | Trang **Rà soát chất lượng** nêu dấu hiệu chấm hình thức |

### 2.3 Tính mới

- **Trung thành với văn bản đến từng chữ số thập phân.** Phụ lục ghi A, B, C ở 03 chữ số thập phân
  và KPI ở 02 chữ số thập phân, đồng thời tính KPI từ chính các giá trị đã làm tròn. Hệ thống làm tròn
  tại nguồn theo đúng cách này.
- **Một nguồn công thức duy nhất.** Toàn bộ công thức nằm ở `services/kpi_service.py`, dùng chung cho
  router, seeder, mô-đun tra cứu văn bản và bộ kiểm thử — không nơi nào chép lại công thức.
- **Hai ranh giới cứng cho các mô hình** (xem mục 9): không mô hình nào ghi vào kết quả điểm KPI;
  không một byte dữ liệu nào rời hệ thống. Cả hai đều được khoá bằng kiểm thử tự động.
- **Kiểm chứng bằng ví dụ của chính văn bản.** Ví dụ chấm điểm tại Phụ lục được cài thành test:
  KPI = 97,97 và tổng điểm xếp loại = 98,579.
- **Xử lý được nhiệm vụ có độ mật** mà không lưu nội dung mật trên hệ thống (xem mục 10).

---

## 3. KIẾN TRÚC HỆ THỐNG

```
┌──────────────────────────────────────────────────────────────────┐
│                  FRONTEND (React 19 + TypeScript)                │
│  Trang chủ · Cơ cấu tổ chức · Nhiệm vụ · Danh mục · Tổng quan KPI │
│  Quy trình đánh giá · Tiêu chí chung (E) · Kết quả xếp loại       │
│  Cán bộ · Rà soát chất lượng · Nhật ký · Hồ sơ cá nhân            │
│         Axios — tự gắn và làm mới thẻ JWT khi hết hạn            │
└───────────────────────────┬──────────────────────────────────────┘
                            │  HTTPS · REST API (JSON)
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ROUTERS                                                    │  │
│  │ auth · departments · employees · tasks · comments           │  │
│  │ notifications · kpi · ai            (+ audit-logs, health)  │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼─────────────────────────────────┐  │
│  │ SERVICES — NGHIỆP VỤ                                       │  │
│  │ kpi_service   công thức A, B, C, D · KPI · xếp nhóm        │  │
│  │ seeder / kpi_seeder   sinh dữ liệu mẫu phủ đủ trường hợp   │  │
│  │ notification_service · audit_service                       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ SERVICES/AI — HỖ TRỢ RA QUYẾT ĐỊNH (chạy tại chỗ)          │  │
│  │ assignment  gợi ý phân công    (công thức có trọng số)     │  │
│  │ risk        cảnh báo sớm        (hồi quy logistic × 2)     │  │
│  │ anomaly     chấm hình thức      (thống kê, 5 dấu hiệu)     │  │
│  │ guideline   tra cứu văn bản     (máy quy tắc + tìm kiếm)   │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼─────────────────────────────────┐  │
│  │ MODELS                                                     │  │
│  │ schemas · kpi_schemas · kpi_criteria (Phụ lục E)           │  │
│  │ security_policy (chính sách tiếp cận nhiệm vụ có độ mật)   │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │  Motor (bất đồng bộ)               │
└─────────────────────────────┼────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                           MongoDB                                │
│  users · departments · tasks · comments · notifications          │
│  audit_logs · kpi_task_catalog · kpi_evaluations                 │
└──────────────────────────────────────────────────────────────────┘
```

**Đặc điểm kiến trúc**

- **Tách Frontend / Backend** — giao tiếp hoàn toàn qua REST API JSON, triển khai độc lập, chuyển được
  vào mạng nội bộ mà không sửa mã nguồn.
- **Stateless + JWT** — máy chủ không giữ phiên; thẻ truy cập ngắn hạn, thẻ làm mới lưu phía máy chủ
  để thu hồi được khi đăng xuất.
- **Nghiệp vụ tập trung** — mọi công thức ở một nơi duy nhất.
- **Mô hình tách riêng** — nhóm `services/ai` chỉ đọc dữ liệu, không ghi vào kết quả đánh giá.
- **Phân quyền ở tầng máy chủ** — kiểm soát bằng dependency của FastAPI trên từng endpoint, và giới hạn
  phạm vi ngay trong điều kiện truy vấn cơ sở dữ liệu.

---

## 4. CÔNG NGHỆ SỬ DỤNG

### 4.1 Backend

| Công nghệ | Phiên bản | Vai trò |
|---|---|---|
| **Python** | 3.12 | Ngôn ngữ chính |
| **FastAPI** | 0.111.0 | Web framework (REST API) |
| **Uvicorn** | 0.30.0 | ASGI server |
| **MongoDB** | — | Cơ sở dữ liệu tài liệu |
| **Motor / PyMongo** | 3.7.1 / 4.17.0 | Truy cập MongoDB bất đồng bộ |
| **Pydantic** | 2.13.4 | Định nghĩa và kiểm tra dữ liệu |
| **python-jose** | 3.5.0 | Tạo, xác thực JWT |
| **passlib + bcrypt** | 1.7.4 / 3.2.2 | Băm mật khẩu |
| **scikit-learn** | 1.5.0 | Hồi quy logistic, chuẩn hoá, đánh giá mô hình |
| **NumPy / SciPy** | 1.26.4 / 1.17.1 | Tính toán số |
| **python-dotenv** | 1.2.2 | Nạp cấu hình từ tệp `.env` |
| **pytest** | 8.3.4 | Kiểm thử |

### 4.2 Frontend

| Công nghệ | Phiên bản | Vai trò |
|---|---|---|
| **React** | 19 | Thư viện giao diện |
| **TypeScript** | 6.x | Kiểm tra kiểu tĩnh |
| **Vite** | 8.x | Công cụ build, máy chủ phát triển |
| **Tailwind CSS** | 4.x | Hệ thống thiết kế |
| **Recharts** | 3.x | Biểu đồ diễn biến KPI, chất lượng, tiến độ |
| **React Router** | 7.x | Điều hướng |
| **Axios** | 1.x | Gọi API, tự làm mới thẻ truy cập |
| **lucide-react** | 1.x | Bộ biểu tượng |
| **react-hot-toast** | 2.x | Thông báo thao tác |

### 4.3 Thuật toán của các mô hình

| Mô hình | Thuật toán | Vì sao chọn |
|---|---|---|
| Gợi ý phân công | Tổng có trọng số 5 thành phần | Dữ liệu quá mỏng để học; cần giải thích được từng thành phần |
| Cảnh báo sớm (2 mô hình) | Hồi quy logistic có chuẩn hoá, cân bằng trọng số lớp | Đóng góp từng đặc trưng = hệ số × giá trị → diễn giải thành lời được |
| Phát hiện chấm hình thức | Thống kê mô tả với ngưỡng công khai | Mỗi dấu hiệu phải là quy tắc rõ ràng để người đọc tự thẩm định |
| Tra cứu Hướng dẫn | Máy quy tắc + so khớp từ khoá tiếng Việt bỏ dấu | Cần nguyên văn điều khoản, không cần diễn giải có thể sai lệch |

---

## 5. CẤU TRÚC MÃ NGUỒN

```
smartwork-ai/
│
├── backend/
│   ├── main.py                      # Khởi tạo FastAPI, CORS, gắn router, /health, nhật ký
│   ├── config.py                    # Nạp .env, CORS, cờ ALLOW_DEMO_ACCOUNTS
│   ├── database.py                  # Kết nối MongoDB (Motor)
│   ├── security.py                  # Băm mật khẩu, JWT, lấy người dùng hiện tại
│   ├── dependencies.py              # Phân quyền: admin > director > leader > staff
│   ├── test_kpi.py                  # 47 test công thức tính điểm
│   ├── test_ai.py                   # 46 test mô hình, bảo mật, cấu hình triển khai
│   │
│   ├── models/
│   │   ├── schemas.py               # Đơn vị, cán bộ, nhiệm vụ, ý kiến, thông báo, nhật ký
│   │   ├── kpi_schemas.py           # Danh mục nhiệm vụ, kỳ đánh giá, mức chất lượng/tiến độ
│   │   ├── kpi_criteria.py          # Khung tiêu chí chung (E) — 03 danh mục theo Phụ lục
│   │   └── security_policy.py       # Chính sách tiếp cận nhiệm vụ có độ mật
│   │
│   ├── routers/
│   │   ├── auth.py                  # Đăng nhập, làm mới thẻ, đăng xuất, hồ sơ cá nhân
│   │   ├── departments.py           # Đơn vị, cây cơ cấu tổ chức, cán bộ thuộc quyền
│   │   ├── employees.py             # Cán bộ, cấp bậc hàm, chức vụ, cấp độ tiếp cận
│   │   ├── tasks.py                 # Nhiệm vụ, nhắc nhở tiến độ, yêu cầu chỉnh sửa
│   │   ├── comments.py              # Ý kiến trao đổi
│   │   ├── notifications.py         # Thông báo
│   │   ├── kpi.py                   # Danh mục, quy trình 3 bước, xếp hạng, tiêu chí chung
│   │   └── ai.py                    # 4 mô hình hỗ trợ ra quyết định
│   │
│   ├── services/
│   │   ├── kpi_service.py           # A, B, C, D · KPI · phân nhóm · KPI quý/năm
│   │   ├── kpi_seeder.py            # Sinh dữ liệu KPI phủ đủ mọi trường hợp
│   │   ├── seeder.py                # Sinh đơn vị, cán bộ, nhiệm vụ, ý kiến, thông báo
│   │   ├── notification_service.py  # Gửi thông báo
│   │   ├── audit_service.py         # Ghi nhật ký hệ thống
│   │   └── ai/
│   │       ├── __init__.py          # Hai ràng buộc bất di bất dịch của nhóm mô hình
│   │       ├── assignment.py        # Gợi ý cán bộ phù hợp để giao nhiệm vụ
│   │       ├── risk.py              # Cảnh báo sớm: rơi Nhóm 3 · nhiệm vụ trễ hạn
│   │       ├── anomaly.py           # Phát hiện dấu hiệu chấm điểm hình thức
│   │       └── guideline.py         # Tra cứu Hướng dẫn 20-HD/ĐUCA
│   │
│   └── scripts/
│       └── set_password.py          # Đặt mật khẩu mạnh cho bản triển khai
│
├── frontend/
│   └── src/
│       ├── App.tsx                  # Định tuyến
│       ├── components/
│       │   ├── Layout.tsx           # Khung trang, menu theo thẩm quyền
│       │   ├── TaskModal.tsx        # Biểu mẫu giao/sửa nhiệm vụ
│       │   ├── EarlyWarning.tsx     # Khối cảnh báo sớm trên Trang chủ
│       │   └── GuidelineLookup.tsx  # Ô tra cứu Hướng dẫn
│       ├── lib/
│       │   ├── api.ts               # Axios, gắn thẻ, tự làm mới khi hết hạn
│       │   ├── task-api.ts          # API nhiệm vụ, nhãn tiếng Việt
│       │   ├── kpi-api.ts           # API KPI
│       │   └── ai-api.ts            # API các mô hình
│       └── pages/                   # 15 trang giao diện (xem mục 13)
│
├── HUONG_DAN_SU_DUNG.md             # Hướng dẫn cho người dùng cuối
├── KICH_BAN_DEMO.md                 # 7 kịch bản trình diễn theo từng vai
├── TAI_LIEU_DU_AN_KPI_CAND.md       # Tài liệu này
├── pytest.ini
└── render.yaml                      # Cấu hình triển khai backend
```

**Quy mô mã nguồn**: khoảng **6.680 dòng** backend (Python) và **5.909 dòng** frontend
(TypeScript/React), tổng khoảng **12.600 dòng**, không tính thư viện bên ngoài.

---

## 6. MÔ HÌNH DỮ LIỆU

Hệ thống dùng 8 collection trong MongoDB.

### 6.1 `departments` — Đơn vị

| Trường | Mô tả |
|---|---|
| `name`, `code` | Tên đơn vị và mã đơn vị (VD: `VPB-P1`) |
| `level` | Cấp đơn vị: `bo` / `cuc` / `phong` / `doi` |
| `parent_id` | Đơn vị cấp trên — tạo thành cây nhiều cấp |
| `force_system` | Hệ lực lượng, dùng khi xây dựng Danh mục nhiệm vụ theo hệ |
| `description` | Chức năng, nhiệm vụ |

### 6.2 `users` — Cán bộ

| Trường | Mô tả |
|---|---|
| `username`, `name`, `email` | Định danh, họ tên, hòm thư |
| `hashed_password` | Mật khẩu băm bcrypt |
| `role` | `admin` / `director` / `leader` / `staff` |
| `department_id` | Đơn vị công tác |
| `position`, `rank` | Chức vụ và cấp bậc hàm |
| `is_commander` | Là lãnh đạo, chỉ huy → KPI theo **04 tiêu chí** |
| **`clearance_level`** | **Cấp độ tiếp cận tài liệu (0–3)** |
| `capacity_points` | Định mức điểm nhiệm vụ trong kỳ, dùng để tính tải việc |
| `active_refresh_token` | Thẻ làm mới đang hiệu lực (xoá khi đăng xuất) |

### 6.3 `kpi_task_catalog` — Khung Danh mục nhiệm vụ công tác theo KPI

| Trường | Mô tả |
|---|---|
| `department_id`, `period_year` | Đơn vị và năm áp dụng |
| `status` | `draft` (bản nháp) hoặc `approved` (đã duyệt) |
| `items[].task_name` | Tên nhiệm vụ |
| `items[].category` | Sản phẩm: công văn, báo cáo, tờ trình, thông tư, quy định, kế hoạch, đề án, khác |
| `items[].complexity_group` | Nhóm độ phức tạp 1 / 2 / 3 |
| `items[].kpi_point` | Điểm của công việc (0–100) |

### 6.4 `tasks` — Nhiệm vụ công tác được giao

| Trường | Mô tả |
|---|---|
| `code`, `title`, `description` | Mã hiệu, tên và nội dung |
| `catalog_item_id` | Trỏ tới mục trong Danh mục (lấy nhóm và số điểm) |
| `product` | Sản phẩm công việc đầu ra |
| `kpi_point` | Điểm được giao theo Danh mục |
| `quantity_assigned` / `quantity_completed` | Số lượng sản phẩm giao / đã hoàn thành |
| `assigned_to`, `co_assignees` | Cán bộ chủ trì và phối hợp |
| `status` | `assigned` → `in_progress` → `review` → `done` |
| `deadline`, `actual_end` | Thời hạn và thời điểm hoàn thành thực tế |
| **`revision_count`** | **Số lần phải hoàn thiện, chỉnh sửa → quyết định mức điểm B** |
| **`reminder_count`** | **Số lần bị nhắc nhở tiến độ → quyết định mức điểm C** |
| **`classification`** | **Độ mật: `thuong` / `mat` / `toi_mat` / `tuyet_mat`** |
| `file_reference`, `file_location` | Số hiệu hồ sơ gốc và nơi lưu (nhiệm vụ có độ mật) |
| `period_month`, `period_year` | Kỳ đánh giá mà nhiệm vụ thuộc về |

### 6.5 `kpi_evaluations` — Hồ sơ kỳ đánh giá

Mỗi bản ghi là hồ sơ của một đối tượng (tập thể hoặc cá nhân) trong một kỳ, gồm 4 khối tương ứng
4 giai đoạn:

```
kpi_evaluations
├── evaluation_type      individual | collective
├── target_id / target_name / target_role · department_id
├── period_type          monthly | quarterly | yearly
├── period_month / period_year
├── overall_status       draft → self_evaluating → reviewing → approved
│                        (hoặc rejected — trả lại)
│
├── self_evaluation   ← Bước 1: cán bộ tự đánh giá
│     task_scores[]:  task_name, kpi_point, is_completed,
│                     quality_tier, timeline_tier,
│                     quality_percent, quality_score,
│                     timeline_percent, timeline_score
│     proposed_rating
│
├── review            ← Bước 2: cơ quan liên quan thẩm định
│     reviewed_by · task_scores[] · review_note
│
├── approval          ← Bước 3: cấp có thẩm quyền xác định điểm
│     approved_by · total_assigned_points
│     score_A · score_B · score_C · score_D
│     kpi_score · kpi_group · capped_by_collective
│
└── general_criteria  ← Điểm E và tổng điểm xếp loại
      criteria_type · scores[] · total_E
      total_kpi_weighted · total_final_score
```

### 6.6 Các collection còn lại

| Collection | Nội dung |
|---|---|
| `comments` | Ý kiến trao đổi trên từng nhiệm vụ |
| `notifications` | Thông báo: giao việc, nhắc nhở, yêu cầu chỉnh sửa, đến kỳ tự đánh giá, đã xác định điểm |
| `audit_logs` | Nhật ký: người thực hiện, hành động, đối tượng, thời điểm — gồm cả `task.classified_access` và `task.classified_denied` |

---

## 7. PHƯƠNG PHÁP TÍNH ĐIỂM KPI

Toàn bộ mục này được cài đặt trong `backend/services/kpi_service.py`.

### 7.1 Điểm của từng công việc

Mỗi công việc trong Danh mục được xác định điểm trên thang **100 điểm**, chia 03 nhóm theo tính chất,
mức độ phức tạp:

| Nhóm | Dải điểm |
|---|---|
| Nhóm 1 | 0 đến dưới 50 điểm |
| Nhóm 2 | 50 đến dưới 70 điểm |
| Nhóm 3 | 70 đến 100 điểm |

### 7.2 Điểm A — Số lượng kết quả thực hiện nhiệm vụ

```
       Điểm số lượng công việc đã hoàn thành
A = ─────────────────────────────────────────
       Điểm công việc được giao theo Danh mục
```

Chỉ công việc có `is_completed = true` được cộng vào tử số.

### 7.3 Điểm B — Chất lượng kết quả thực hiện nhiệm vụ

```
       Điểm về chất lượng của công việc đã hoàn thành
B = ────────────────────────────────────────────────
              Điểm công việc được giao
```

| Đánh giá | Số lần sửa | Mức điểm | Mã |
|---|---|---|---|
| Vượt mức yêu cầu | — | không quá **120%** | `excellent` |
| Đảm bảo chất lượng | 0 | **100%** | `good` |
| Cơ bản đảm bảo | 01 lần | không quá **75%** | `fair_1` |
| Còn thiếu sót | 02 – 04 lần | không quá **50%** | `fair_2_4` |
| Thiếu sót | 05 – 06 lần | không quá **25%** | `poor_5_6` |
| Không đạt | từ 07 lần | **không tính điểm** | `fail_7` |

### 7.4 Điểm C — Tiến độ thực hiện nhiệm vụ

```
       Điểm về tiến độ của công việc hoàn thành
C = ────────────────────────────────────────────
              Điểm công việc được giao
```

| Đánh giá | Số lần nhắc nhở | Mức điểm | Mã |
|---|---|---|---|
| Vượt tiến độ và đảm bảo chất lượng | — | không quá **120%** | `ahead` |
| Đảm bảo tiến độ và chất lượng | 0 | **100%** | `on_time` |
| Chưa đảm bảo tiến độ | 01 lần | không quá **75%** | `late_1` |
| Chưa đảm bảo tiến độ | 02 lần | không quá **50%** | `late_2` |
| Chưa đảm bảo tiến độ | 03 lần | không quá **25%** | `late_3` |
| Chưa đảm bảo tiến độ | từ 04 lần | **không tính điểm** | `fail_4` |

> Mức không xác định luôn cho **0 điểm**, không bao giờ mặc định thành mức tối đa — có test khoá lại.

### 7.5 Điểm D — Kết quả lãnh đạo, chỉ đạo

Chỉ áp dụng với cá nhân là lãnh đạo, chỉ huy:

```
      Số tập thể, cá nhân thuộc quyền quản lý được đánh giá hoàn thành nhiệm vụ trở lên
D = ──────────────────────────────────────────────────────────────────────────────────   (0 – 01)
                            Số tập thể, cá nhân được đánh giá
```

Hệ thống đếm các hồ sơ đã xác định điểm trong cùng đơn vị, cùng kỳ (không tính chính người lãnh đạo đó),
lấy tỷ lệ số hồ sơ thuộc **Nhóm 1** hoặc **Nhóm 2**.

### 7.6 Điểm KPI

```
KPI tập thể                        = (A + B + C) / 3 × 100
KPI cá nhân không giữ chức vụ      = (A + B + C) / 3 × 100
KPI cá nhân là lãnh đạo, chỉ huy   = (A + B + C + D) / 4 × 100
```

> **KPI của người đứng đầu không cao hơn KPI của tập thể, đơn vị do mình đứng đầu.**
> Hệ thống đối chiếu hồ sơ tập thể cùng kỳ, cùng đơn vị đã duyệt, tự áp mức trần và xếp lại nhóm
> theo điểm đã áp trần; bản ghi lưu cờ `capped_by_collective`.

**Cách ghi số**: A, B, C ghi ở **03 chữ số thập phân**; KPI ghi ở **02 chữ số thập phân**. Việc làm tròn
thực hiện ngay tại nguồn để kết quả trùng với cách tính chính thức (ví dụ `0,939` chứ không phải
`0,9388059…`). Do công việc vượt mức được tính tới 120%, điểm B và C **có thể vượt 100%**.

### 7.7 Điểm tiêu chí chung (E) và tổng điểm xếp loại

| Thành phần | Tối đa |
|---|---|
| **E** — Điểm theo nhóm tiêu chí chung | 30 điểm |
| Điểm theo kết quả thực hiện nhiệm vụ = KPI × 0,7 | 70 điểm |

```
F (tập thể)                      = E + KPI tập thể   × 0,7
G (cá nhân không là lãnh đạo)    = E + KPI cá nhân   × 0,7
H (cá nhân là lãnh đạo, chỉ huy) = E + KPI lãnh đạo  × 0,7
```

Khung tiêu chí chung được số hoá nguyên văn trong `backend/models/kpi_criteria.py`:

| Đối tượng | Mã | Bố cục thang điểm |
|---|---|---|
| Tập thể | `collective` | 6 tiêu chí × 5 điểm = 30 |
| Cá nhân là lãnh đạo, chỉ huy | `leader` | 18 + 04 + 08 = 30 |
| Cá nhân không là lãnh đạo, chỉ huy | `staff` | 20 + 08 + 02 = 30 |

Mỗi tiêu chí lá chấm theo 2 mức: **Đảm bảo** (đạt tối đa điểm) hoặc **Không đảm bảo** (0 điểm).
Hệ thống tự chọn đúng bộ theo loại đánh giá và chức vụ của đối tượng.

### 7.8 Phân nhóm cán bộ

| Nhóm | Điểm KPI | Ý nghĩa | Mã |
|---|---|---|---|
| Nhóm 1 | 70 – 100 | Đáp ứng tốt yêu cầu nhiệm vụ trở lên | `group_1` |
| Nhóm 2 | 50 – dưới 70 | Đáp ứng yêu cầu nhiệm vụ | `group_2` |
| Nhóm 3 | dưới 50 | Chưa đáp ứng yêu cầu nhiệm vụ | `group_3` |

### 7.9 KPI quý, năm

Điểm KPI hằng quý, hằng năm bằng **bình quân điểm KPI hằng tháng** đã xác định trong kỳ tương ứng.

### 7.10 Ví dụ tính điểm theo Phụ lục

Ví dụ chấm điểm đồng chí A tháng 6/2026:

| Nhiệm vụ | Sản phẩm | Số lượng × điểm | Điểm giao | Mức chất lượng | Điểm B |
|---|---|---|---|---|---|
| NV1 | Công văn | 10 × 05 | 50 | Đảm bảo (100%) | 50 |
| NV2 | Báo cáo | 03 × 15 | 45 | Đảm bảo (100%) | 45 |
| NV3 | Tờ trình | 03 × 20 | 60 | 02 đảm bảo + 01 vượt mức (110%) | 62 |
| NV4 | Thông tư | 01 × 90 | 90 | Đảm bảo (100%) | 90 |
| NV5 | Quy định | 01 × 90 | 90 | Chỉnh sửa 01 lần (75%) | 67,5 |
| **Tổng** | | | **335** | | **314,5** |

```
A = 335 / 335     = 1
B = 314,5 / 335   = 0,939
C = 335 / 335     = 1

KPI = (1 + 0,939 + 1) / 3 × 100 = 97,97      → Nhóm 1
Tổng điểm xếp loại = 30 + 97,97 × 0,7 = 98,579
```

Ví dụ này được cài thành **test tự động** trong `backend/test_kpi.py`.

---

## 8. QUY TRÌNH ĐÁNH GIÁ 03 BƯỚC

```
   Bước 1                    Bước 2                       Bước 3
┌──────────────┐        ┌──────────────────┐        ┌────────────────────┐
│ Tự đánh giá  │───────►│ Cơ quan có liên  │───────►│ Cấp có thẩm quyền  │
│ và đề xuất   │        │ quan thẩm định,  │        │ xác định điểm KPI  │
│ mức xếp loại │        │ đề xuất          │        │                    │
│ (cán bộ /    │        │ (lãnh đạo,       │        │ (người đứng đầu)   │
│  tập thể)    │        │  chỉ huy)        │        │                    │
└──────────────┘        └──────────────────┘        └────────────────────┘
       │                        │                            │
       ▼                        ▼                            ▼
 self_evaluating           reviewing                     approved
                                │
                                └──── không khớp hồ sơ ───► rejected
```

**Bước 1 — Tự đánh giá.** Cán bộ báo cáo kết quả thực hiện nhiệm vụ, tự chấm mức chất lượng và tiến độ
cho từng công việc, nêu nguyên nhân chưa bảo đảm (nếu có), đề xuất mức xếp loại.
→ `PUT /api/kpi/evaluations/{id}/self-evaluate`

**Bước 2 — Thẩm định.** Cơ quan tổ chức cán bộ phối hợp cơ quan tham mưu đối chiếu Danh mục với kết quả
thực tế; có quyền sửa lại bảng chấm điểm và ghi nhận xét.
→ `PUT /api/kpi/evaluations/{id}/review`

**Bước 3 — Xác định điểm KPI.** Hệ thống lấy bảng chấm của Bước 2 (nếu chưa thẩm định thì lấy của Bước 1),
tính A, B, C, D, điểm KPI, áp mức trần với người đứng đầu rồi xếp nhóm.
→ `PUT /api/kpi/evaluations/{id}/approve`

Sau đó chấm **điểm tiêu chí chung (E)** để ra tổng điểm xếp loại.
→ `PUT /api/kpi/evaluations/{id}/general-criteria`

| Trạng thái | Hiển thị |
|---|---|
| `draft` | Chưa tự đánh giá |
| `self_evaluating` | Chờ thẩm định |
| `reviewing` | Chờ xác định điểm KPI |
| `approved` | Đã xác định điểm KPI |
| `rejected` | Trả lại do số liệu chưa khớp hồ sơ |

---

## 9. BỐN MÔ HÌNH HỖ TRỢ RA QUYẾT ĐỊNH

### 9.1 Hai ràng buộc bất di bất dịch

Ghi thành quy ước bắt buộc ngay đầu gói `backend/services/ai/__init__.py`:

**1. Mô hình không được quyết định điểm KPI.** Điểm A, B, C, D và cách phân nhóm là công thức của văn bản
pháp quy; nếu mô hình đề xuất điểm thì mất căn cứ pháp lý khi có khiếu nại. Không module nào trong gói này
được ghi vào `kpi_evaluations.approval` — chỉ đọc dữ liệu, trả về gợi ý và cảnh báo.

**2. Không một byte dữ liệu nào rời hệ thống.** Toàn bộ tính toán chạy tại chỗ; không import `requests`,
`httpx`, `openai`, `google.generativeai` hay bất kỳ thư viện gọi mạng nào. **Có test tự động quét mã nguồn
để kiểm điều này.**

Hệ quả kỹ thuật: ưu tiên mô hình **giải thích được**. Cơ quan nhà nước không chấp nhận hộp đen — mọi kết quả
phải nêu được lý do, nên hệ thống dùng công thức có trọng số và hồi quy logistic thay vì mô hình phức tạp
không diễn giải nổi.

### 9.2 Mô hình 1 — Gợi ý cán bộ phù hợp để giao nhiệm vụ

`backend/services/ai/assignment.py`

Xếp hạng cán bộ trong đơn vị theo điểm phù hợp, là tổng có trọng số:

| Thành phần | Trọng số | Cách tính |
|---|---|---|
| Dư địa tải việc | 35% | `1 − tải việc / 100` |
| Chất lượng lịch sử | 25% | `1 − số lần sửa TB ở cùng nhóm độ phức tạp / 7` |
| Tiến độ lịch sử | 20% | `1 − số lần nhắc TB ở cùng loại sản phẩm / 4` |
| Không tồn việc quá hạn | 10% | 1,0 nếu không có việc quá hạn; 0,4 nếu có |
| KPI 3 kỳ gần nhất | 10% | `min(KPI bình quân / 100 , 1,0)` |

Hai bộ **lọc cứng** áp trước khi tính điểm: cán bộ không đủ cấp độ tiếp cận so với độ mật của nhiệm vụ bị
loại bắt buộc; cán bộ đang mang tải quá **130%** định mức cũng bị loại. Kết quả trả về **cả danh sách được
đề xuất lẫn danh sách bị loại kèm lý do**, để lãnh đạo thấy hệ thống đã cân nhắc những ai.

Mốc chuẩn hoá 7 lần sửa và 4 lần nhắc lấy đúng từ bảng mức của Hướng dẫn — là ngưỡng mà công việc không
còn được tính điểm.

> **Mức độ hoàn thiện**: phần xử lý và endpoint đã hoàn chỉnh, đã có sẵn hàm gọi ở `frontend/src/lib/ai-api.ts`,
> nhưng **chưa gắn vào màn hình giao nhiệm vụ**. Đây là hạng mục đang tiếp tục hoàn thiện.

### 9.3 Mô hình 2 — Cảnh báo sớm nguy cơ (hai mô hình hồi quy logistic)

`backend/services/ai/risk.py`

Mục đích: để lãnh đạo can thiệp **giữa kỳ** thay vì biết khi đã hết kỳ.

**2a. Nguy cơ cán bộ rơi Nhóm 3 khi kết thúc kỳ** — 8 đặc trưng:

`ty_le_diem_hoan_thanh` · `ty_le_viec_xong` · `so_lan_sua_tich_luy` · `so_lan_nhac_tich_luy`
· `so_viec_qua_han` · `kpi_binh_quan_truoc` · `xu_the_kpi` · `tai_viec`

Huấn luyện từ các kỳ đã duyệt, nhãn là cán bộ có rơi Nhóm 3 hay không.

**2b. Nguy cơ một nhiệm vụ hoàn thành trễ hạn** — 6 đặc trưng:

`so_lan_nhac` · `so_lan_sua` · `ty_le_hoan_thanh` · `diem_nhiem_vu` · `nhom_do_phuc_tap` · `tong_so_ngay`

Huấn luyện từ các nhiệm vụ đã kết thúc, nhãn là có hoàn thành trễ hay không.

**Cách bảo đảm chất lượng và tính trung thực:**

| Cơ chế | Nội dung |
|---|---|
| Tách tập kiểm tra | Chia 80/20 có phân tầng theo nhãn; AUC đo trên tập chưa từng dùng để huấn luyện |
| Ngưỡng tối thiểu | AUC ≥ **0,70**, tối thiểu **80 mẫu** và **10 trường hợp dương** |
| Dưới ngưỡng | Mô hình bị đánh dấu **không dùng được** kèm lý do — *thà không có cảnh báo còn hơn cảnh báo sai* |
| Minh bạch | `POST /api/ai/retrain` luôn trả về AUC, ma trận nhầm lẫn và hệ số từng đặc trưng để người quản trị tự thẩm định |

**Giải thích kết quả**: mỗi cảnh báo kèm 3 yếu tố đóng góp nhiều nhất, tính bằng `hệ số × giá trị đã chuẩn hoá`,
diễn đạt theo hướng nêu thẳng điều quan sát được — ví dụ *"bị nhắc nhở nhiều lần trong kỳ → tăng nguy cơ"*,
*"đã đạt phần lớn số điểm được giao → giảm nguy cơ"*.

> **Lưu ý về chỉ số AUC trên dữ liệu mẫu**: trên dữ liệu do seeder sinh ra, AUC rất cao (khoảng 0,99) vì nhiệm vụ
> và kỳ đánh giá đều bắt nguồn từ cùng một mức năng lực theo tháng — mô hình gần như khôi phục lại đúng quy tắc
> sinh dữ liệu. **Đây không phải dự báo về hiệu quả thực tế.** Với dữ liệu thật, con người không hành xử theo
> quy tắc cố định nên AUC sẽ thấp hơn đáng kể. Chỉ số đáng tin duy nhất là chỉ số đo trên dữ liệu vận hành thật
> sau vài kỳ.

Kết quả hiển thị trong khối **Cảnh báo sớm** trên Trang chủ, kèm ghi chú rõ đây là dự báo để đôn đốc,
hỗ trợ kịp thời, **không phải kết quả đánh giá và không ảnh hưởng tới điểm KPI**.

### 9.4 Mô hình 3 — Phát hiện dấu hiệu chấm điểm hình thức

`backend/services/ai/anomaly.py`

Hướng dẫn yêu cầu đánh giá bảo đảm "thực chất" nhưng không có cơ chế phát hiện đơn vị chấm cho có.
Module này nêu dấu hiệu bất thường để cơ quan tổ chức cán bộ **rà soát** — không phải kết luận vi phạm.

| Dấu hiệu | Ngưỡng | Mức độ |
|---|---|---|
| Điểm tiêu chí chung đồng loạt tối đa | ≥ 80% cán bộ đạt 30/30 | Cao |
| Điểm KPI trong đơn vị quá đồng đều | độ lệch chuẩn < 3 điểm | Trung bình |
| Tự đánh giá lệch xa kết quả thẩm định | tự nhận cao hơn ≥ 2 nhóm | Trung bình |
| Điểm KPI nhảy vọt bất thường | thay đổi ≥ 10 điểm **và** lệch > 2 lần dao động thường thấy | Thấp |
| Mâu thuẫn quá hạn / xếp loại | > 30% việc quá hạn mà không ai Nhóm 3 | Cao |

Thuần thống kê, **không dùng máy học**: mỗi dấu hiệu là một quy tắc rõ ràng, ngưỡng công khai ngay trên giao diện,
kèm số liệu cụ thể để người đọc tự thẩm định.

Hai cơ chế chống báo động giả: dấu hiệu điểm nhảy vọt phải thoả mãn **đồng thời** thay đổi tuyệt đối đáng kể
và lệch nhiều so với dao động của chính cán bộ đó (nếu chỉ dùng z-score, cán bộ có điểm rất ổn định sẽ bị báo
động chỉ vì chênh 1–2 điểm — vô nghĩa trên thang 100); đơn vị dưới **4 cán bộ** thì bỏ qua vì thống kê không
còn ý nghĩa.

### 9.5 Mô hình 4 — Tra cứu Hướng dẫn 20-HD/ĐUCA

`backend/services/ai/guideline.py`

Gồm hai phần:

1. **Máy quy tắc** nhận diện câu hỏi về con số và trả lời chính xác: *"Sửa 3 lần thì được bao nhiêu phần trăm?"*,
   *"Nhắc nhở 2 lần được bao nhiêu điểm?"*, *"KPI 65 thuộc nhóm mấy?"*. Hiểu được cả khi gõ **không dấu** nhờ
   chuẩn hoá tiếng Việt, và cả cách diễn đạt không dùng chữ số (*"không phải sửa lần nào"*, *"đúng hạn"*).
2. **Tìm kiếm điều khoản** trên 14 điều khoản đã lập chỉ mục, trả về **nguyên văn** kèm vị trí trong văn bản.

**Điểm mấu chốt**: mọi câu trả lời về con số lấy **trực tiếp từ hằng số của bộ máy chấm điểm** (`kpi_service`),
nên luôn khớp với điều hệ thống thực sự tính — ràng buộc này được khoá bằng test riêng.

Sản phẩm **chủ ý không dùng mô hình ngôn ngữ lớn** ở đây: đây là văn bản pháp quy, cán bộ cần nguyên văn điều
khoản để trích dẫn chứ không cần bản diễn giải có thể sai lệch; và một mô hình sinh văn bản không bảo đảm được
sự trùng khớp tuyệt đối với bộ máy chấm điểm.

Hiển thị dưới dạng ô tra cứu ngay trong màn hình **Quy trình đánh giá**.

---

## 10. NHIỆM VỤ CÓ ĐỘ MẬT

`backend/models/security_policy.py`

### 10.1 Nguyên tắc

Hệ thống **chỉ lưu phần thông tin quản lý** phục vụ tính điểm KPI:

```
mã hiệu · tên gọi quy ước · độ mật · điểm được giao · thời hạn
· số lần chỉnh sửa · số lần nhắc nhở · số hiệu hồ sơ gốc · nơi lưu
```

Toàn bộ nội dung nghiệp vụ nằm ở **hồ sơ gốc, ngoài hệ thống**. Điều này không làm mất tính năng nào:
công thức A, B, C, D không sử dụng đến nội dung nhiệm vụ.

### 10.2 Bốn cơ chế bảo vệ

| Cơ chế | Cách hoạt động |
|---|---|
| Phân quyền tiếp cận | Cán bộ chỉ xem được nhiệm vụ có độ mật **≤ cấp độ tiếp cận** của mình, hoặc nhiệm vụ do chính mình chủ trì / phối hợp |
| **Che ở tầng máy chủ** | Trường `description`, `file_reference`, `file_location`, `attachments` bị **loại khỏi phản hồi API**; tên nhiệm vụ thay bằng mã hiệu. Mở DevTools cũng không thấy |
| Chặn ghi nội dung | Lưu diễn giải hoặc đính kèm tệp vào nhiệm vụ có độ mật bị từ chối (HTTP 400) |
| Chặn giao vượt cấp | Giao nhiệm vụ ở độ mật cao hơn cấp độ của mình bị từ chối (HTTP 403) |
| Nhật ký truy cập | Ghi mọi lượt truy cập nhiệm vụ có độ mật, **kể cả lượt bị từ chối** |

Khi không đủ cấp độ tiếp cận, điểm, số lượng, thời hạn và số lần nhắc nhở **vẫn hiển thị** để việc chấm điểm
KPI luôn minh bạch.

### 10.3 Giới hạn — đọc kỹ trước khi triển khai

> Hệ thống này **KHÔNG** phải hệ thống xử lý bí mật nhà nước và **KHÔNG** được dùng để lưu trữ nội dung
> thuộc danh mục bí mật nhà nước, vì: cơ sở dữ liệu đặt trên hạ tầng điện toán đám mây dùng chung; không sử dụng
> sản phẩm mật mã của Ban Cơ yếu Chính phủ; không chạy trên mạng máy tính nội bộ tách biệt.
>
> Cơ chế ở đây là **phân quyền tiếp cận + ghi nhật ký**, là biện pháp quản lý nội bộ, **không thay thế** yêu cầu
> pháp lý về bảo vệ bí mật nhà nước theo Luật Bảo vệ bí mật nhà nước 2018.

---

## 11. BẢO MẬT VÀ PHÂN QUYỀN

### 11.1 Xác thực

- Không có đăng ký tự do; tài khoản do cấp có thẩm quyền tạo.
- Mật khẩu băm **bcrypt**, không lưu bản rõ.
- **Thẻ truy cập** hiệu lực 15 phút, **thẻ làm mới** hiệu lực 7 ngày và được lưu phía máy chủ để thu hồi
  ngay khi đăng xuất. Giao diện tự làm mới thẻ nên người dùng không bị đăng xuất giữa chừng.

### 11.2 Phân quyền

Thứ bậc `admin (3) > director (2) > leader (1) > staff (0)`.

| Chức năng | staff | leader | director | admin |
|---|:---:|:---:|:---:|:---:|
| Xem nhiệm vụ của mình | ✅ | ✅ | ✅ | ✅ |
| Xem nhiệm vụ toàn đơn vị phụ trách | — | ✅ | ✅ | ✅ |
| Tạo, xoá nhiệm vụ | — | ✅ | ✅ | ✅ |
| Nhắc nhở tiến độ / yêu cầu chỉnh sửa | — | ✅ | ✅ | ✅ |
| **Bước 1** tự đánh giá | ✅ | ✅ | ✅ | ✅ |
| **Bước 2** thẩm định | — | ✅ | ✅ | ✅ |
| **Bước 3** xác định điểm KPI | — | — | ✅ | ✅ |
| Chấm tiêu chí chung (E) | — | — | ✅ | ✅ |
| Tạo, duyệt Danh mục nhiệm vụ | — | — | ✅ | ✅ |
| Rà soát chất lượng (mô hình 3) | — | — | ✅ | ✅ |
| Cảnh báo sớm, gợi ý phân công | — | ✅ | ✅ | ✅ |
| Tra cứu Hướng dẫn | ✅ | ✅ | ✅ | ✅ |
| Quản lý cán bộ | — | — | ✅ | ✅ |
| Quản lý đơn vị · nhật ký · huấn luyện lại mô hình | — | — | — | ✅ |

> Phạm vi dữ liệu được giới hạn **ngay trong điều kiện truy vấn cơ sở dữ liệu**, không phải lọc sau khi lấy
> dữ liệu về hay ẩn nút trên giao diện.

### 11.3 Bảo vệ ở tầng kết nối

Chỉ tên miền đã khai báo mới gọi được API. Danh sách cho phép gồm ba phần (`nguon_cors()` trong `config.py`):

| Nguồn | Nội dung |
|---|---|
| Máy cục bộ | `http://localhost:5173`, `http://localhost:5199`, `http://127.0.0.1:5173` |
| Mẫu tên miền triển khai | `^https://smartwork-ai[a-z0-9-]*\.vercel\.app$` — phủ cả tên miền xem trước Vercel sinh sau mỗi lần đẩy mã |
| Biến `CORS_ORIGINS` | **Cộng thêm** tên miền riêng, không thay thế danh sách trên |

`allow_credentials` giữ nguyên **False**: hệ thống xác thực bằng thẻ Bearer trong `localStorage`, không dùng
cookie phiên, nên trang web lạ dù được phép gọi API cũng không đọc được thẻ. Ràng buộc này có test khoá lại.

### 11.4 Phòng ngừa rủi ro triển khai

- Máy chủ **từ chối đăng nhập** bằng danh sách mật khẩu mặc định phổ biến (`admin123`, `123456`, `password`,
  `12345678`) với mã lỗi 403 riêng để phân biệt với sai mật khẩu, trừ khi bật `ALLOW_DEMO_ACCOUNTS=true`.
  Có test bảo đảm mọi mật khẩu seeder dùng đều nằm trong danh sách chặn hoặc được cân nhắc có chủ đích.
- Công cụ `python -m backend.scripts.set_password` đặt mật khẩu mạnh sinh ngẫu nhiên, in ra một lần duy nhất.

> ⚠️ Mật khẩu dữ liệu mẫu hiện là `123456789a`, **cố ý nằm ngoài** danh sách chặn để bản demo đăng nhập được
> ngay. Đánh đổi: cơ chế chặn không bảo vệ các tài khoản mẫu. Chỉ chấp nhận được vì toàn bộ là dữ liệu giả —
> **bắt buộc đổi trước khi đưa dữ liệu thật vào**.

---

## 12. API ENDPOINTS

### 12.1 Xác thực — `/api/auth`

| Phương thức | Đường dẫn | Thẩm quyền | Mô tả |
|---|---|---|---|
| POST | `/register` | — | Tạo tài khoản (dùng khi khởi tạo) |
| POST | `/login` | — | Đăng nhập, trả thẻ truy cập + thẻ làm mới |
| POST | `/refresh` | — | Cấp lại thẻ truy cập |
| POST | `/logout` | Đã đăng nhập | Thu hồi thẻ làm mới |
| GET | `/me` | Đã đăng nhập | Thông tin cán bộ đang đăng nhập |
| POST | `/change-password` | Đã đăng nhập | Đổi mật khẩu |
| PUT | `/profile` | Đã đăng nhập | Cập nhật hồ sơ cá nhân |

### 12.2 Đơn vị và cán bộ

| Phương thức | Đường dẫn | Thẩm quyền | Mô tả |
|---|---|---|---|
| GET | `/api/departments/` | Đã đăng nhập | Danh sách đơn vị |
| GET | `/api/departments/tree` | Đã đăng nhập | Cây cơ cấu tổ chức nhiều cấp |
| GET | `/api/departments/{id}` | Đã đăng nhập | Chi tiết đơn vị |
| POST/PUT/DELETE | `/api/departments/…` | admin | Quản lý đơn vị |
| GET | `/api/employees/` | Đã đăng nhập | Danh sách cán bộ |
| POST/PUT/DELETE | `/api/employees/…` | director+ | Quản lý cán bộ |

### 12.3 Nhiệm vụ công tác — `/api/tasks`

| Phương thức | Đường dẫn | Thẩm quyền | Mô tả |
|---|---|---|---|
| GET | `/` | Đã đăng nhập | Danh sách nhiệm vụ (lọc theo cán bộ, đơn vị, trạng thái, kỳ) |
| POST | `/` | leader+ | Giao nhiệm vụ mới |
| PUT | `/{id}` | Người được giao / leader+ | Cập nhật nhiệm vụ |
| DELETE | `/{id}` | leader+ | Xoá nhiệm vụ |
| POST | `/{id}/remind` | leader+ | **Nhắc nhở tiến độ** → tăng `reminder_count` (điểm C) |
| POST | `/{id}/request-revision` | leader+ | **Yêu cầu hoàn thiện, chỉnh sửa** → tăng `revision_count` (điểm B) |
| GET/POST | `/{task_id}/comments` | Đã đăng nhập | Ý kiến trao đổi |

### 12.4 KPI — `/api/kpi`

| Phương thức | Đường dẫn | Thẩm quyền | Mô tả |
|---|---|---|---|
| GET | `/catalog` | Đã đăng nhập | Danh mục nhiệm vụ công tác |
| POST | `/catalog` | director+ | Tạo Danh mục (trạng thái `draft`) |
| PUT | `/catalog/{id}/approve` | director+ | Phê duyệt Danh mục |
| POST | `/evaluations` | leader+ | Mở kỳ đánh giá |
| GET | `/evaluations` | Đã đăng nhập | Danh sách hồ sơ (staff chỉ thấy của mình) |
| GET | `/evaluations/{id}` | Đã đăng nhập | Chi tiết hồ sơ |
| PUT | `/evaluations/{id}/self-evaluate` | Chủ hồ sơ / leader+ | **Bước 1** |
| PUT | `/evaluations/{id}/review` | leader+ | **Bước 2** |
| PUT | `/evaluations/{id}/approve` | director+ | **Bước 3** — tính A, B, C, D, KPI, nhóm |
| PUT | `/evaluations/{id}/general-criteria` | director+ | Chấm điểm E, tính tổng điểm xếp loại |
| GET | `/scores/ranking` | leader+ | Bảng xếp hạng KPI |
| GET | `/criteria-templates` | Đã đăng nhập | Khung tiêu chí chung theo Phụ lục |

### 12.5 Mô hình hỗ trợ ra quyết định — `/api/ai`

| Phương thức | Đường dẫn | Thẩm quyền | Mô tả |
|---|---|---|---|
| GET | `/suggest-assignee` | leader+ | Gợi ý cán bộ phù hợp để giao nhiệm vụ |
| GET | `/risk/officers` | leader+ | Cán bộ có nguy cơ rơi Nhóm 3 |
| GET | `/risk/tasks` | leader+ | Nhiệm vụ có nguy cơ trễ hạn |
| POST | `/retrain` | admin | Huấn luyện lại, trả về AUC và ma trận nhầm lẫn |
| GET | `/anomalies` | director+ | Dấu hiệu chấm điểm hình thức |
| GET | `/guideline/search` | Đã đăng nhập | Tra cứu Hướng dẫn 20-HD/ĐUCA |
| GET | `/guideline/clauses` | Đã đăng nhập | Toàn bộ điều khoản đã lập chỉ mục |

### 12.6 Khác

| Phương thức | Đường dẫn | Thẩm quyền | Mô tả |
|---|---|---|---|
| GET | `/api/notifications/` · `/unread-count` | Đã đăng nhập | Thông báo |
| PUT | `/api/notifications/{id}/read` · `/read-all` | Đã đăng nhập | Đánh dấu đã đọc |
| GET | `/api/audit-logs` | admin | Nhật ký hệ thống |
| GET | `/health` | — | Kiểm tra máy chủ sống |

---

## 13. GIAO DIỆN NGƯỜI DÙNG

### 13.1 Cấu trúc điều hướng

```
Tổng quan
├── Trang chủ                    /                    (kèm khối Cảnh báo sớm)
└── Cơ cấu tổ chức               /organization

Nhiệm vụ công tác
├── Nhiệm vụ được giao           /tasks
└── Danh mục nhiệm vụ            /kpi/catalog         (director+)

Đánh giá KPI
├── Tổng quan KPI                /kpi
├── Quy trình đánh giá           /kpi/evaluate        (kèm ô Tra cứu Hướng dẫn)
├── Tiêu chí chung (E)           /kpi/criteria        (leader+)
└── Kết quả xếp loại             /kpi/results

Quản lý
├── Cán bộ                       /employees           (director+)
├── Rà soát chất lượng           /quality-review      (director+)
└── Nhật ký hệ thống             /audit-logs          (admin)

Khác
├── Hồ sơ cán bộ                 /employees/:id
├── Thông báo                    /notifications
└── Hồ sơ cá nhân                /profile
```

### 13.2 Các trang

| Trang | Nội dung chính |
|---|---|
| **Trang chủ** | Nhiệm vụ trong tháng, số quá hạn, KPI kỳ gần nhất, KPI bình quân năm, biểu đồ diễn biến KPI theo tháng, phân bố chất lượng và tiến độ, **khối Cảnh báo sớm** |
| **Cơ cấu tổ chức** | Cây đơn vị nhiều cấp; chọn đơn vị để xem số cán bộ (gồm cấp dưới), KPI tập thể, phân bố nhóm xếp loại, bảng cán bộ kèm cột tải việc và cấp độ tiếp cận |
| **Hồ sơ cán bộ** | Định danh, số hiệu CAND, cấp độ tiếp cận, tải việc, thống kê nhiệm vụ trong kỳ, tổng số lần sửa (→ B) và nhắc nhở (→ C), biểu đồ diễn biến KPI |
| **Nhiệm vụ được giao** | Bảng nhiệm vụ kèm mã hiệu, độ mật, điểm, số lượng, hạn; tổng điểm được giao và **A / B / C dự kiến**; nút nhắc nhở và yêu cầu chỉnh sửa |
| **Danh mục nhiệm vụ** | Xây dựng Khung Danh mục theo năm; trạng thái Bản nháp / Đã duyệt |
| **Tổng quan KPI** | Biểu đồ KPI toàn đơn vị theo năm, phân bố cán bộ theo 3 nhóm |
| **Quy trình đánh giá** | Thực hiện 03 bước; chọn mức chất lượng và tiến độ kèm tỷ lệ phần trăm; ô tra cứu Hướng dẫn |
| **Tiêu chí chung (E)** | Chấm 30 điểm theo đúng Phụ lục, tự chọn bộ tiêu chí; hiển thị E, KPI, KPI × 0,7 và tổng điểm |
| **Kết quả xếp loại** | Bảng điểm chi tiết A, B, C, D, KPI, E, tổng điểm; xếp nhóm theo ngưỡng 70 / 50 |
| **Cán bộ** | Quản lý cấp bậc hàm, chức vụ, số hiệu, đơn vị, thẩm quyền, **cấp độ tiếp cận** |
| **Rà soát chất lượng** | Danh sách dấu hiệu chấm hình thức kèm mức độ, bằng chứng số liệu, khuyến nghị; nút huấn luyện lại mô hình |
| **Nhật ký hệ thống** | Lịch sử thao tác, gồm nhật ký truy cập nhiệm vụ có độ mật |

### 13.3 Phong cách

Giao diện sáng, bố cục hành chính, **toàn bộ bằng tiếng Việt**, dùng đúng thuật ngữ của Hướng dẫn.
Menu bên trái chia theo nhóm nghiệp vụ, mục ngoài thẩm quyền không hiển thị. Trên thiết bị di động
menu thu vào nút ☰. Số thông báo chưa đọc tự làm mới mỗi 30 giây.

---

## 14. DỮ LIỆU MẪU

```bash
python -m backend.services.seeder
```

> ⚠️ Lệnh này **xoá toàn bộ dữ liệu hiện có** trong cơ sở dữ liệu đang trỏ tới. Kiểm tra `MONGO_URI`
> và `DB_NAME` trước khi chạy.

### 14.1 Cơ cấu tổ chức mẫu — cây 3 cấp, 12 đơn vị

```
Bộ Công an (BCA)
├── Văn phòng Bộ Công an (VPB)
│   ├── Phòng Tham mưu tổng hợp (VPB-P1)
│   └── Phòng Thư ký - Biên tập (VPB-P2)
├── Cục Tổ chức cán bộ (X01)
│   ├── Phòng Chính sách cán bộ (X01-P1)
│   └── Phòng Đào tạo, bồi dưỡng (X01-P2)
├── Cục Pháp chế và cải cách hành chính, tư pháp (V03)
│   └── Phòng Xây dựng pháp luật (V03-P1)
└── Công an tỉnh Đắk Lắk (CADL)
    ├── Phòng Cảnh sát điều tra tội phạm về trật tự xã hội (CADL-PC02)
    └── Phòng An ninh chính trị nội bộ (CADL-PA03)
```

Cán bộ và việc chấm KPI bố trí ở **cấp Phòng**.

### 14.2 Tài khoản

Tổng cộng **64 tài khoản**, dùng chung mật khẩu `123456789a`:

| Thẩm quyền | Tài khoản | Số lượng | Cấp độ tiếp cận |
|---|---|---|---|
| Quản trị hệ thống | `admin` | 1 | Tuyệt mật |
| Trưởng phòng | `director_*` | 7 | Tuyệt mật |
| Lãnh đạo, chỉ huy | `leader1` … `leader14` | 14 | Tối mật |
| Cán bộ, chiến sĩ | `canbo0` … `canbo41` | 42 | Thường / Mật / Tối mật |

Mỗi phòng có 2 lãnh đạo, chỉ huy và 6 cán bộ. Cấp độ tiếp cận của cán bộ phân bố theo quy tắc
`N mod 6`: 0/1/2 là Thường, 3/4 là Mật, 5 là Tối mật — toàn hệ thống có 21 cán bộ Thường,
14 cán bộ Mật, 7 cán bộ Tối mật.

### 14.3 Độ phủ

Dữ liệu mẫu được thiết kế để mọi trường hợp của Hướng dẫn đều xuất hiện ít nhất một lần:

1. Danh mục nhiệm vụ đúng 03 nhóm điểm; có cả bản nháp và bản đã duyệt.
2. Đủ **06 mức điểm chất lượng** và **06 mức điểm tiến độ**.
3. Đủ **03 nhóm xếp loại KPI** và **05 trạng thái quy trình**.
4. Cả đánh giá tập thể và cá nhân; cá nhân gồm lãnh đạo, chỉ huy (có điểm D) và không giữ chức vụ.
5. **07 tháng liên tiếp** để tính được KPI quý và năm.
6. Đủ **04 loại nhiệm vụ** và **04 độ mật**; cán bộ có cấp độ tiếp cận khác nhau.
7. Điểm D suy ra từ tỷ lệ cán bộ thuộc quyền đạt Nhóm 1 hoặc Nhóm 2.
8. Ràng buộc KPI người đứng đầu không cao hơn KPI tập thể.

Điểm A, B, C của dữ liệu mẫu được **tính từ chính các hàm nghiệp vụ đang dùng thật**, nên số liệu luôn
nhất quán với công thức.

---

## 15. KIỂM THỬ

```bash
pip install -r backend/requirements-dev.txt
pytest -v
```

**93 test**, thuần logic, không cần kết nối cơ sở dữ liệu thật (dùng CSDL giả trong bộ nhớ).

| Tệp | Số test | Nội dung |
|---|---|---|
| `backend/test_kpi.py` | 47 | Công thức tính điểm |
| `backend/test_ai.py` | 46 | Mô hình hỗ trợ ra quyết định, ràng buộc bảo mật, cấu hình triển khai |

**`test_kpi.py`** kiểm chứng: 06 mức chất lượng và 06 mức tiến độ; mức không xác định phải cho 0 điểm;
suy điểm từng nhiệm vụ từ mức đã chấm; A, B, C chỉ tính công việc đã hoàn thành, chia cho 0 an toàn,
làm tròn 03 chữ số, cho phép vượt 100% khi vượt mức; hai công thức KPI cho 03 và 04 tiêu chí; biên phân
nhóm tại 70 và 50; tổng điểm `E + KPI × 0,7`; ba bộ tiêu chí chung đều đúng 30 điểm và điểm mục cha bằng
tổng điểm mục con; trần KPI người đứng đầu.

**`test_ai.py`** kiểm chứng: máy quy tắc tra cứu trả đúng mức điểm cho mọi số lần sửa và nhắc nhở; câu trả
lời khớp **cùng hằng số** mà bộ máy chấm điểm dùng; 05 dấu hiệu chấm hình thức được nhận diện đúng và
**không báo động giả** khi dữ liệu bình thường; **không module AI nào import thư viện gọi mạng**; cấu hình
CORS chỉ chấp nhận đúng tên miền hợp lệ và từ chối tên miền giả mạo; cờ `ALLOW_DEMO_ACCOUNTS` mặc định tắt.

**Test quan trọng nhất** — tái lập ví dụ mẫu tại Phụ lục:

```bash
pytest backend/test_kpi.py -v -k worked_example
```

Kiểm tra hệ thống tính ra đúng **KPI = 97,97** và **tổng điểm xếp loại = 98,579**, đồng thời dựng lại đúng
05 dòng nhiệm vụ của ví dụ (tổng 335 điểm giao, 314,5 điểm chất lượng, 335 điểm tiến độ).

Ngoài ra, `KICH_BAN_DEMO.md` cung cấp **07 kịch bản trình diễn thủ công** theo từng vai, mỗi bước ghi rõ
đăng nhập bằng gì, làm gì và phải thấy gì.

---

## 16. CÀI ĐẶT, CHẠY VÀ TRIỂN KHAI

### 16.1 Yêu cầu

- Python 3.12 · Node.js 20 trở lên · MongoDB (cục bộ hoặc dịch vụ quản lý)

### 16.2 Backend

```bash
pip install -r backend/requirements.txt

export MONGO_URI="mongodb://localhost:27017"
export DB_NAME="smartwork"

uvicorn backend.main:app --reload
```

| Biến môi trường | Bắt buộc | Mô tả |
|---|---|---|
| `MONGO_URI` | ✅ | Chuỗi kết nối MongoDB |
| `DB_NAME` | — | Tên cơ sở dữ liệu, mặc định `smartwork` |
| `SECRET_KEY` | ✅ khi chạy thật | Khoá ký JWT |
| `CORS_ORIGINS` | — | Cộng thêm tên miền riêng |
| `CORS_ORIGIN_REGEX` | — | Ghi đè mẫu khớp tên miền mặc định |
| `ALLOW_DEMO_ACCOUNTS` | — | Cho phép mật khẩu mặc định; **để `false` khi chạy thật** |

Tài liệu API tự sinh: `http://localhost:8000/docs`

### 16.3 Frontend

```bash
cd frontend && npm install && npm run dev
```

Địa chỉ API cấu hình qua `VITE_API_URL`, mặc định `http://localhost:8000/api`.

### 16.4 Triển khai

| Thành phần | Nền tảng | Ghi chú |
|---|---|---|
| Backend | Render (`render.yaml`) | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | Vercel (`frontend/vercel.json`) | Đặt `VITE_API_URL` trỏ tới backend, kèm hậu tố `/api` |
| Cơ sở dữ liệu | MongoDB | Dịch vụ quản lý hoặc máy chủ nội bộ của đơn vị |

Sau khi triển khai, đặt mật khẩu mạnh:

```bash
python -m backend.scripts.set_password admin
```

---

## 17. TÍNH KHẢ THI VÀ KHẢ NĂNG MỞ RỘNG

### 17.1 Tính khả thi

| Tiêu chí | Đánh giá |
|---|---|
| **Bám sát văn bản** | Công thức, mức điểm, quy trình, khung tiêu chí chung lấy nguyên theo Hướng dẫn 20-HD/ĐUCA |
| **Đã chạy được** | Bản triển khai công khai dùng thử ngay trên trình duyệt, không cần cài đặt |
| **Chi phí** | Toàn bộ nguồn mở; không phụ thuộc dịch vụ AI trả phí; chạy được trên gói miễn phí |
| **Độ phức tạp kỹ thuật** | Trung bình — Python và React phổ biến, dễ tiếp nhận, bảo trì |
| **Đào tạo người dùng** | Dễ — giao diện tiếng Việt, dùng đúng thuật ngữ của Hướng dẫn; có tài liệu và kịch bản demo |
| **Bảo mật** | Băm bcrypt, JWT, phân quyền 4 cấp ở tầng máy chủ, nhật ký đầy đủ, chặn mật khẩu mặc định |
| **Kiểm chứng được** | 93 test tự động, trong đó có test tái lập ví dụ mẫu của Phụ lục |

### 17.2 Hạn chế còn tồn tại

Nêu rõ để việc đánh giá được khách quan:

1. **Chỉ số AUC trên dữ liệu mẫu không phản ánh hiệu quả thực tế** — xem ghi chú ở mục 9.3.
2. **Chức năng gợi ý phân công chưa gắn giao diện** — phần xử lý và endpoint đã hoàn chỉnh.
3. **Mật khẩu mẫu yếu** (`123456789a`), bắt buộc đổi trước khi đưa dữ liệu thật vào.
4. **Không dùng cho bí mật nhà nước** với hạ tầng hiện tại — xem mục 10.3.

### 17.3 Khả năng mở rộng

| Hướng phát triển | Mô tả |
|---|---|
| **Xuất báo cáo** | Kết xuất bảng điểm và phiếu đánh giá ra Excel / PDF theo đúng mẫu Phụ lục |
| **Ký số** | Tích hợp chữ ký số cho hồ sơ ở Bước 3 |
| **Trang KPI quý, năm** | Công thức bình quân đã có sẵn ở backend, chỉ cần bổ sung giao diện |
| **Gắn gợi ý phân công vào màn hình giao việc** | Endpoint và hàm gọi đã sẵn sàng |
| **Đồng bộ nhân sự** | Kết nối hệ thống quản lý cán bộ để đồng bộ cấp bậc hàm, chức vụ, đơn vị |
| **Triển khai mạng nội bộ** | Kiến trúc tách rời cho phép chuyển vào hạ tầng nội bộ mà không sửa mã nguồn |
| **Phân cấp sâu hơn** | Cây đơn vị đã hỗ trợ nhiều cấp, mở rộng để tổng hợp KPI theo toàn bộ cây |

---

> **Tài liệu này mô tả hệ thống ở phiên bản 3.0.0.**
> Hướng dẫn thao tác cho người dùng cuối: `HUONG_DAN_SU_DUNG.md`
> Kịch bản trình diễn: `KICH_BAN_DEMO.md`
