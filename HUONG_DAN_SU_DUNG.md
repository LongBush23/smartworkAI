# HƯỚNG DẪN SỬ DỤNG
## Hệ thống tính điểm KPI trong Công an nhân dân (KPI-CAND)

Hệ thống được xây dựng theo **Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026** của Ban Thường vụ
Đảng ủy Công an Trung ương về phương pháp tính điểm và sử dụng chỉ số đo lường (KPI)
trong đánh giá, xếp loại chất lượng đối với tập thể, cá nhân trong Công an nhân dân.

---

## 1. Tài khoản mẫu

> ⚠️ **Toàn bộ 64 tài khoản đều dùng chung một mật khẩu: `123456789a`**
>
> Đây là mật khẩu của **dữ liệu mẫu**, cố ý đặt yếu để chạy thử cho nhanh.
> Phải đổi toàn bộ trước khi triển khai thật — xem mục *Đặt mật khẩu mạnh* ở cuối tài liệu.

Tổng cộng **64 tài khoản**: 1 quản trị · 7 Trưởng phòng · 14 lãnh đạo, chỉ huy · 42 cán bộ.

### 1.1. Tổng quan theo thẩm quyền

| Thẩm quyền | Tài khoản | Mật khẩu | Cấp độ tiếp cận | Làm được gì |
|---|---|---|---|---|
| Quản trị hệ thống | `admin` | `123456789a` | Tuyệt mật | Toàn bộ dữ liệu, quản lý đơn vị, nhật ký hệ thống |
| Trưởng phòng (người đứng đầu) | `director_*` (7) | `123456789a` | Tuyệt mật | Danh mục nhiệm vụ · **Bước 3** xác định điểm KPI · chấm tiêu chí chung (E) |
| Lãnh đạo, chỉ huy | `leader1` … `leader14` | `123456789a` | Tối mật | Giao nhiệm vụ · nhắc nhở · yêu cầu chỉnh sửa · **Bước 2** thẩm định |
| Cán bộ, chiến sĩ | `canbo0` … `canbo41` | `123456789a` | Thường / Mật / Tối mật | Nhiệm vụ của mình · **Bước 1** tự đánh giá |

> Lãnh đạo, chỉ huy (`director_*`, `leader*`) được tính KPI theo **04 tiêu chí**
> (có thêm điểm D về kết quả lãnh đạo, chỉ đạo); tập thể và cán bộ không giữ chức vụ
> tính theo **03 tiêu chí**.

### 1.2. Trưởng phòng theo từng đơn vị

| Tài khoản | Cấp bậc | Đơn vị phụ trách | Mã đơn vị |
|---|---|---|---|
| `director_tmth` | Đại tá | Phòng Tham mưu tổng hợp | VPB-P1 |
| `director_tkbt` | Thượng tá | Phòng Thư ký - Biên tập | VPB-P2 |
| `director_cscb` | Trung tá | Phòng Chính sách cán bộ | X01-P1 |
| `director_dtbd` | Đại tá | Phòng Đào tạo, bồi dưỡng | X01-P2 |
| `director_xdpl` | Thượng tá | Phòng Xây dựng pháp luật | V03-P1 |
| `director_pc02` | Trung tá | Phòng Cảnh sát điều tra tội phạm về trật tự xã hội | CADL-PC02 |
| `director_pa03` | Đại tá | Phòng An ninh chính trị nội bộ | CADL-PA03 |

### 1.3. Lãnh đạo, chỉ huy và cán bộ theo từng đơn vị

Mỗi phòng có **2 lãnh đạo, chỉ huy** (1 Phó Trưởng phòng + 1 Đội trưởng) và **6 cán bộ**.

| Đơn vị | Phó Trưởng phòng | Đội trưởng | Cán bộ |
|---|---|---|---|
| Phòng Tham mưu tổng hợp | `leader1` | `leader2` | `canbo0` … `canbo5` |
| Phòng Thư ký - Biên tập | `leader3` | `leader4` | `canbo6` … `canbo11` |
| Phòng Chính sách cán bộ | `leader5` | `leader6` | `canbo12` … `canbo17` |
| Phòng Đào tạo, bồi dưỡng | `leader7` | `leader8` | `canbo18` … `canbo23` |
| Phòng Xây dựng pháp luật | `leader9` | `leader10` | `canbo24` … `canbo29` |
| Phòng Cảnh sát điều tra tội phạm về trật tự xã hội | `leader11` | `leader12` | `canbo30` … `canbo35` |
| Phòng An ninh chính trị nội bộ | `leader13` | `leader14` | `canbo36` … `canbo41` |

### 1.4. Cấp độ tiếp cận tài liệu của cán bộ

Trong mỗi nhóm 6 cán bộ của một phòng, cấp độ tiếp cận được bố trí như sau
(lấy `canbo0`–`canbo5` của Phòng Tham mưu tổng hợp làm ví dụ):

| Vị trí trong nhóm | Ví dụ | Cấp độ tiếp cận | Xem được nhiệm vụ độ mật |
|---|---|---|---|
| Người thứ 1, 2, 3 | `canbo0`, `canbo1`, `canbo2` | Tài liệu thường | Không xem được nhiệm vụ có độ mật |
| Người thứ 4, 5 | `canbo3`, `canbo4` | Đến độ **Mật** | Mật |
| Người thứ 6 | `canbo5` | Đến độ **Tối mật** | Mật, Tối mật |

Quy tắc chung: với `canbo{N}`, lấy `N mod 6` — kết quả 0/1/2 là **Thường**,
3/4 là **Mật**, 5 là **Tối mật**.

Phân bố toàn hệ thống: 21 cán bộ Thường · 14 cán bộ Mật · 7 cán bộ Tối mật.

### 1.5. Tài khoản nên dùng để xem thử từng tình huống

| Muốn xem | Đăng nhập | Vào trang |
|---|---|---|
| Nhiệm vụ mật **đầy đủ** (có số hiệu hồ sơ gốc) | `director_tmth` | Nhiệm vụ được giao |
| Nhiệm vụ mật **bị che** vì chưa đủ cấp độ | `leader1` → lọc độ mật *Tuyệt mật* | Nhiệm vụ được giao |
| Cán bộ **không thấy** nhiệm vụ mật nào | `canbo0` | Nhiệm vụ được giao |
| Cây đơn vị và tải việc toàn lực lượng | `admin` | Cơ cấu tổ chức |
| Tự đánh giá (Bước 1) | `canbo0` | Quy trình đánh giá |
| Thẩm định (Bước 2) | `leader1` | Quy trình đánh giá |
| Xác định điểm KPI (Bước 3) | `director_tmth` | Quy trình đánh giá |
| Chấm tiêu chí chung (E) | `director_tmth` | Tiêu chí chung (E) |
| Nhật ký truy cập nhiệm vụ mật | `admin` | Nhật ký hệ thống |

---

## 1b. Cơ cấu tổ chức mẫu

Dữ liệu mẫu dựng cây **3 cấp**, gồm 12 đơn vị. Cán bộ và việc chấm KPI bố trí ở **cấp Phòng**.

```
Bộ Công an
├── Văn phòng Bộ Công an
│   ├── Phòng Tham mưu tổng hợp
│   └── Phòng Thư ký - Biên tập
├── Cục Tổ chức cán bộ
│   ├── Phòng Chính sách cán bộ
│   └── Phòng Đào tạo, bồi dưỡng
├── Cục Pháp chế và cải cách hành chính, tư pháp
│   └── Phòng Xây dựng pháp luật
└── Công an tỉnh Đắk Lắk
    ├── Phòng Cảnh sát điều tra tội phạm về trật tự xã hội
    └── Phòng An ninh chính trị nội bộ
```

Mỗi đơn vị có thêm **mã đơn vị** để tra cứu nhanh, hiển thị ở góc phải khi mở chi tiết đơn vị:

| Đơn vị | Mã đơn vị |
|---|---|
| Bộ Công an | BCA |
| Văn phòng Bộ Công an | VPB |
| Cục Tổ chức cán bộ | X01 |
| Cục Pháp chế và cải cách hành chính, tư pháp | V03 |
| Công an tỉnh Đắk Lắk | CADL |
| Phòng Tham mưu tổng hợp | VPB-P1 |
| Phòng Thư ký - Biên tập | VPB-P2 |
| Phòng Chính sách cán bộ | X01-P1 |
| Phòng Đào tạo, bồi dưỡng | X01-P2 |
| Phòng Xây dựng pháp luật | V03-P1 |
| Phòng Cảnh sát điều tra tội phạm về trật tự xã hội | CADL-PC02 |
| Phòng An ninh chính trị nội bộ | CADL-PA03 |

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
- Cán bộ chỉ thấy nhiệm vụ của mình; lãnh đạo, chỉ huy thấy nhiệm vụ **trong đơn vị mình
  phụ trách**; quản trị hệ thống thấy toàn bộ.
- Mỗi nhiệm vụ có: mã hiệu, loại, độ mật, sản phẩm, nhóm độ phức tạp, điểm/sản phẩm,
  số lượng giao và hoàn thành, **điểm tối đa đạt được** (gồm phần vượt mức 120%),
  cán bộ chủ trì và phối hợp, người giao, căn cứ giao, hạn và **số ngày còn lại/trễ**.
- Bảng tổng hợp hiển thị ngay **tổng điểm được giao** và **A / B / C dự kiến** của kỳ.
- Lãnh đạo, chỉ huy có 2 thao tác trực tiếp ảnh hưởng điểm KPI:
  - 🔔 **Nhắc nhở tiến độ** → tăng số lần nhắc nhở, giảm mức điểm **C**
  - 📝 **Yêu cầu hoàn thiện, chỉnh sửa** → tăng số lần sửa, giảm mức điểm **B**

**Loại nhiệm vụ** và **độ mật** là hai trục độc lập:

| Loại nhiệm vụ | Ý nghĩa |
|---|---|
| Thường xuyên | Nhiệm vụ theo chức năng, thực hiện định kỳ |
| Đột xuất | Nhiệm vụ phát sinh ngoài kế hoạch |
| Chuyên đề | Nhiệm vụ theo kế hoạch, chuyên đề riêng |
| Phối hợp | Nhiệm vụ có sự tham gia của nhiều đơn vị |

### 4.3b. Nhiệm vụ có độ mật

Độ mật theo Luật Bảo vệ bí mật nhà nước 2018: **Mật · Tối mật · Tuyệt mật**
(nhiệm vụ không thuộc danh mục thì để **Thường**).

> **Hệ thống KHÔNG lưu nội dung của nhiệm vụ có độ mật.**
> Chỉ lưu: mã hiệu · tên gọi quy ước · độ mật · điểm · thời hạn · số lần sửa
> · số lần nhắc nhở · số hiệu hồ sơ gốc · nơi lưu.
> Nội dung nghiệp vụ nằm ở hồ sơ gốc, quản lý theo chế độ mật tại đơn vị.
> Việc này không mất tính năng nào — công thức A, B, C, D không dùng đến nội dung.

Cơ chế bảo vệ:

| Cơ chế | Cách hoạt động |
|---|---|
| Phân quyền tiếp cận | Cán bộ chỉ xem được nhiệm vụ có độ mật **≤ cấp độ tiếp cận** của mình, hoặc nhiệm vụ do chính mình thực hiện |
| Che ở **máy chủ** | Trường nhạy cảm bị loại khỏi phản hồi API, không gửi về trình duyệt. Mở DevTools cũng không thấy |
| Chặn ghi nội dung | Lưu nội dung vào nhiệm vụ có độ mật bị từ chối (HTTP 400) |
| Chặn giao vượt cấp | Giao nhiệm vụ ở độ mật cao hơn cấp độ của mình bị từ chối (HTTP 403) |
| Nhật ký truy cập | Ghi lại mọi lượt truy cập nhiệm vụ có độ mật, **kể cả lượt bị từ chối** |

Khi không đủ cấp độ tiếp cận, giao diện hiển thị: tên nhiệm vụ thay bằng **mã hiệu**,
huy hiệu độ mật kèm ổ khoá, nhãn *"chưa đủ cấp độ tiếp cận"*. Điểm, số lượng, thời hạn
và số lần nhắc nhở **vẫn hiển thị** để việc chấm điểm KPI luôn minh bạch.

⚠️ Đây là biện pháp quản lý nội bộ, **không thay thế** yêu cầu pháp lý về bảo vệ bí mật
nhà nước (mạng nội bộ tách biệt, sản phẩm mật mã của Ban Cơ yếu Chính phủ). Xem ghi chú
đầy đủ ở `backend/models/security_policy.py`.

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

### 4.7. Cơ cấu tổ chức
Cây đơn vị nhiều cấp. Chọn một đơn vị để xem: số cán bộ (gồm cả đơn vị cấp dưới),
KPI tập thể kỳ gần nhất, phân bố cán bộ theo nhóm xếp loại, và bảng cán bộ thuộc quyền.

**Tình trạng nhận nhiệm vụ** của mỗi cán bộ được tính bằng
*tổng điểm nhiệm vụ chưa hoàn thành / định mức điểm của cán bộ trong kỳ*:

| Tình trạng | Mức tải | Ý nghĩa |
|---|---|---|
| 🟢 Sẵn sàng nhận nhiệm vụ | dưới 50% | Còn dư địa để giao thêm việc |
| 🔵 Đang thực hiện | 50% – dưới 85% | Khối lượng hợp lý |
| 🟡 Gần đầy định mức | 85% – 100% | Cân nhắc trước khi giao thêm |
| 🔴 Quá tải | trên 100% | Vượt định mức, cần điều tiết |

### 4.8. Hồ sơ cán bộ
Bấm vào tên cán bộ trong Cơ cấu tổ chức để xem hồ sơ công tác:

- **Định danh**: họ tên, cấp bậc hàm, chức vụ, đơn vị, số hiệu CAND, cấp độ tiếp cận
- **Tải việc**: điểm đang đảm nhận / định mức, tình trạng sẵn sàng
- **Nhiệm vụ trong kỳ**: được giao · đã hoàn thành · đang thực hiện · quá hạn, kèm số điểm
- **Chất lượng, tiến độ**: tổng số lần phải chỉnh sửa (→ điểm B) và bị nhắc nhở (→ điểm C)
- **KPI**: điểm kỳ gần nhất, nhóm xếp loại, bình quân năm, biểu đồ diễn biến theo tháng
- **Bảng nhiệm vụ** của kỳ, có đánh dấu nhiệm vụ mang độ mật

### 4.9. Cán bộ *(Lãnh đạo đơn vị trở lên)*
Quản lý cán bộ theo cấp bậc hàm, chức vụ, số hiệu, đơn vị, thẩm quyền và
**cấp độ tiếp cận tài liệu**. Đổi vai trò sang lãnh đạo, chỉ huy sẽ tự chuyển sang
cách tính KPI 04 tiêu chí.

### 4.10. Nhật ký hệ thống *(Quản trị hệ thống)*
Lưu vết thao tác trên hệ thống, trong đó có riêng nhật ký truy cập nhiệm vụ có độ mật:

| Hành động | Ý nghĩa |
|---|---|
| `task.classified_access` | Truy cập nhiệm vụ có độ mật **thành công** |
| `task.classified_denied` | Truy cập **bị từ chối** do chưa đủ cấp độ tiếp cận |

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

> ⚠️ **Mật khẩu của dữ liệu mẫu là `123456789a` — yếu, và không có cơ chế nào chặn nó.**
>
> Máy chủ chỉ từ chối một danh sách mật khẩu mặc định phổ biến (`admin123`, `123456`,
> `password`, `12345678`) và trả về lỗi 403, trừ khi bật `ALLOW_DEMO_ACCOUNTS=true`.
> Mật khẩu `123456789a` **cố ý nằm ngoài** danh sách đó để bản demo đăng nhập được ngay
> mà không phải mở cờ. Đánh đổi: cơ chế chặn không còn bảo vệ các tài khoản mẫu nữa.
>
> Chỉ chấp nhận được vì toàn bộ dữ liệu là dữ liệu giả. **Trước khi đưa dữ liệu thật vào,
> bắt buộc đổi mật khẩu** bằng `python -m backend.scripts.set_password <tài_khoản> --hoi`.

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

Dữ liệu mẫu sinh ra:

| Nội dung | Số lượng |
|---|---|
| Đơn vị (cây 3 cấp) | 12 |
| Cán bộ | 64 |
| Danh mục nhiệm vụ | 8 (7 đã duyệt + 1 bản nháp) |
| Kỳ đánh giá KPI | 491 |
| Nhiệm vụ công tác | 350, trong đó **73 có độ mật** |

Phủ đủ mọi trường hợp của Hướng dẫn: 3 nhóm độ phức tạp · 6 mức chất lượng · 6 mức tiến độ
· 3 nhóm xếp loại KPI · 5 trạng thái quy trình · cả tập thể và cá nhân · 7 tháng liên tiếp
để tính KPI quý và năm · 4 loại nhiệm vụ · 4 độ mật · cán bộ có cấp độ tiếp cận khác nhau.

Sau khi chạy, dùng bảng tài khoản ở **mục 1** để đăng nhập.

### 5.3. Frontend

```bash
cd frontend && npm install && npm run dev
```

### 5.3b. Triển khai lên máy chủ

**Backend (Render)** — cấu hình theo `render.yaml`. Đặt các biến sau trong bảng
điều khiển:

| Biến | Bắt buộc | Giá trị |
|---|---|---|
| `MONGO_URI` | ✅ | Chuỗi kết nối MongoDB |
| `CORS_ORIGINS` | — | Chỉ cần khi dùng **tên miền riêng**, ví dụ `https://kpi.bocongan.gov.vn` |
| `CORS_ORIGIN_REGEX` | — | Ghi đè mẫu khớp tên miền mặc định |
| `ALLOW_DEMO_ACCOUNTS` | — | Để `false` |

**Về CORS.** Trình duyệt chỉ cho giao diện gọi API nếu máy chủ khai báo tên miền
của giao diện là hợp lệ. Máy chủ cho phép sẵn:

- máy cục bộ: `http://localhost:5173`, `http://localhost:5199`, `http://127.0.0.1:5173`
- mọi bản triển khai Vercel của dự án, khớp mẫu `^https://smartwork-ai[a-z0-9-]*\.vercel\.app$`
  — kể cả tên miền xem trước Vercel sinh ra sau mỗi lần đẩy mã

Nhờ vậy **quên đặt `CORS_ORIGINS` không còn làm giao diện chết**. Giá trị đặt trong
`CORS_ORIGINS` được **cộng thêm** vào danh sách trên chứ không thay thế, nên đặt tên
miền thật rồi thì `npm run dev` ở máy vẫn chạy bình thường.

> Mở sẵn như vậy có an toàn không? Có. Hệ thống xác thực bằng thẻ Bearer lưu trong
> `localStorage`, không dùng cookie phiên, và `allow_credentials=False`. Một trang web
> lạ không đọc được `localStorage` của tên miền khác, nên dù được phép gọi API nó vẫn
> không có thẻ để gọi bất kỳ endpoint nào cần đăng nhập.

Log lúc khởi động in ra đúng danh sách đang áp dụng:

```
CORS cho phép: http://localhost:5173, ... · khớp mẫu: ^https://smartwork-ai[a-z0-9-]*\.vercel\.app$
```

**Frontend (Vercel)** — đặt biến `VITE_API_URL` trỏ tới backend, kèm hậu tố `/api`:

```
VITE_API_URL = https://smartwork-backend.onrender.com/api
```

**Đặt mật khẩu mạnh.** Bản triển khai hiện để mọi tài khoản mẫu dùng chung
`123456789a` cho tiện demo. Trước khi đưa dữ liệu thật vào, đổi mật khẩu:

```bash
python -m backend.scripts.set_password admin
```

Lệnh sinh mật khẩu ngẫu nhiên và in ra một lần duy nhất. Dùng `--hoi` nếu muốn
tự nhập mật khẩu.

Nếu cần đặt lại mật khẩu chung cho toàn bộ tài khoản (chỉ dùng cho bản demo):

```bash
python -m backend.scripts.set_password --tat-ca 123456789a
```

### 5.4. Kiểm thử

```bash
pip install -r backend/requirements-dev.txt
pytest -v
```

93 test kiểm chứng công thức tính điểm, các mô hình AI, ràng buộc bảo mật và cấu hình
triển khai — trong đó có test tái tạo đúng **ví dụ mẫu tại Phụ lục** (đồng chí A tháng
6/2026: KPI = 97,97; tổng điểm xếp loại = 98,579).

---

## 6. Xử lý sự cố đăng nhập

Trang đăng nhập phân biệt rõ ba nguyên nhân. Đọc đúng thông báo là biết phải sửa ở đâu.

### 6.1. *"Không kết nối được máy chủ…"*

Trình duyệt không gọi tới được API. **Không phải sai mật khẩu.** Hai nguyên nhân:

**a) Máy chủ chưa chạy.** Mở thẳng địa chỉ backend kèm `/health`:

```bash
curl https://smartwork-backend-ctda.onrender.com/health
```

Phải trả về `{"status":"ok"}`. Nếu treo lâu rồi mới trả lời, đó là Render đánh thức
dịch vụ ở gói miễn phí — chờ khoảng 50 giây rồi thử lại.

**b) Tên miền giao diện chưa được phép gọi API (CORS).** Kiểm tra bằng lệnh sau, thay
tên miền giao diện của bạn vào `Origin`:

```bash
curl -i -X OPTIONS https://smartwork-backend-ctda.onrender.com/api/auth/login -H "Origin: https://smartwork-ai-3u7e.vercel.app" -H "Access-Control-Request-Method: POST"
```

| Kết quả | Nghĩa là |
|---|---|
| `200` kèm dòng `access-control-allow-origin: …` | Đúng, không phải lỗi CORS |
| `400 Disallowed CORS origin` | Tên miền chưa được phép — thêm vào `CORS_ORIGINS` trên Render rồi khởi động lại dịch vụ |

Tên miền Vercel của dự án đã được cho phép sẵn (xem mục 5.3b), nên lỗi này chỉ xảy ra
với tên miền riêng.

### 6.2. *"Sai tài khoản hoặc mật khẩu"*

Máy chủ **có** trả lời, chỉ là thông tin đăng nhập không khớp. Mật khẩu của mọi tài
khoản dữ liệu mẫu là `123456789a`. Nếu quên mật khẩu tài khoản thật:

```bash
python -m backend.scripts.set_password admin --hoi
```

### 6.3. *"Tài khoản đang dùng mật khẩu mặc định…"*

Lỗi 403, không phải 401 — mật khẩu **đúng** nhưng nằm trong danh sách mặc định bị chặn
(`admin123`, `123456`, `password`, `12345678`). Đặt lại mật khẩu:

```bash
python -m backend.scripts.set_password --tat-ca 123456789a
```

### 6.4. Đăng nhập được nhưng trang trống

Không phải lỗi kết nối. Bộ chọn **Tháng/Năm** ở góc phải đang ở kỳ không có dữ liệu —
dữ liệu mẫu nằm ở tháng hiện tại. Nếu vẫn trống thì chạy lại seeder.
