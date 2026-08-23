"""
Khoá lại quy tắc che giấu nhiệm vụ có độ mật khi kết xuất phiếu đánh giá KPI
ra Excel (backend/services/kpi_export_service.py).

Đây là test QUAN TRỌNG NHẤT của tính năng xuất Excel: phiếu in ra để lưu hồ
sơ không được làm lộ tên gọi, mô tả hay hồ sơ gốc của nhiệm vụ có độ mật khi
người xuất phiếu không đủ cấp độ tiếp cận — dù dữ liệu đó có được lưu sẵn
trong bảng chấm điểm hay không (xem models/security_policy.py).

Các test này thuần logic, không cần kết nối cơ sở dữ liệu.
Chạy:  pytest backend/test_kpi_export.py -v
"""
from openpyxl import Workbook

from backend.services.kpi_export_service import (
    dung_bang_tong_hop,
    dung_phieu_ca_nhan,
    ten_hien_thi_nhiem_vu,
)

TEN_THAT = "Chuyên án triệt phá đường dây X"
MO_TA_MAT = "Nội dung diễn biến chuyên án, danh sách đối tượng theo dõi..."
HO_SO_GOC = "HS-2026-0099"
MA_HIEU = "NV-2026-06-0007"


def nhiem_vu_mat(assigned_to="u_khac", co_assignees=None):
    return {
        "code": MA_HIEU,
        "title": TEN_THAT,
        "description": MO_TA_MAT,
        "classification": "toi_mat",
        "file_reference": HO_SO_GOC,
        "file_location": "Tủ hồ sơ mật, Phòng Tổ chức cán bộ",
        "attachments": ["mat-01.pdf"],
        "assigned_to": assigned_to,
        "co_assignees": co_assignees or [],
        "kpi_point": 90,
    }


def diem_nhiem_vu(task_id="t1", ten_luu="Chuyên án X (đã lưu lúc tự đánh giá)"):
    return {
        "task_id": task_id,
        "task_name": ten_luu,
        "kpi_point": 90,
        "is_completed": True,
        "quality_tier": "good",
        "timeline_tier": "on_time",
    }


def phieu_don_gian(task_id="t1", ten_luu="Chuyên án X (đã lưu lúc tự đánh giá)"):
    return {
        "target_id": "u_target",
        "target_name": "Đồng chí Nguyễn Văn A",
        "target_role": "staff",
        "period_type": "monthly",
        "period_month": 6,
        "period_year": 2026,
        "self_evaluation": {"task_scores": [diem_nhiem_vu(task_id, ten_luu)]},
        "approval": {
            "score_A": 1.0, "score_B": 1.0, "score_C": 1.0, "score_D": None,
            "kpi_score": 100.0, "kpi_group": "group_1",
        },
        "general_criteria": {"scores": [], "total_final_score": 100.0},
    }


def noi_dung_toan_bo(wb: Workbook) -> str:
    """Gộp mọi ô của mọi sheet thành 1 chuỗi để rà soát rò rỉ."""
    manh = []
    for ws in wb.worksheets:
        for hang in ws.iter_rows():
            for o in hang:
                if o.value is not None:
                    manh.append(str(o.value))
    return "\n".join(manh)


# ================= ten_hien_thi_nhiem_vu — đơn vị nhỏ nhất =================

def test_nhiem_vu_mat_bi_che_khi_khong_du_cap_do():
    nguoi_xuat_phieu = {"_id": "u_van_thu", "clearance_level": 0}
    ten, bi_che = ten_hien_thi_nhiem_vu(nhiem_vu_mat(), diem_nhiem_vu(), nguoi_xuat_phieu)
    assert bi_che is True
    assert ten == MA_HIEU
    assert TEN_THAT not in ten


def test_nhiem_vu_mat_hien_thi_that_khi_du_cap_do():
    nguoi_xuat_phieu = {"_id": "u_giam_doc", "clearance_level": 2}  # toi_mat rank = 2
    ten, bi_che = ten_hien_thi_nhiem_vu(nhiem_vu_mat(), diem_nhiem_vu(), nguoi_xuat_phieu)
    assert bi_che is False
    assert ten == TEN_THAT


def test_nhiem_vu_mat_hien_thi_that_cho_chinh_nguoi_thuc_hien():
    """Người được đánh giá xuất phiếu của chính mình vẫn thấy tên thật, dù clearance = 0."""
    nguoi_xuat_phieu = {"_id": "u_target", "clearance_level": 0}
    ten, bi_che = ten_hien_thi_nhiem_vu(
        nhiem_vu_mat(assigned_to="u_target"), diem_nhiem_vu(), nguoi_xuat_phieu
    )
    assert bi_che is False
    assert ten == TEN_THAT


def test_khong_tim_thay_nhiem_vu_goc_thi_dung_ten_da_luu():
    """Nhiệm vụ đã bị xoá khỏi hệ thống: không có gì để áp redact(), đành giữ tên đã lưu."""
    nguoi_xuat_phieu = {"_id": "u_van_thu", "clearance_level": 0}
    ten, bi_che = ten_hien_thi_nhiem_vu(None, diem_nhiem_vu(ten_luu="Tên đã lưu"), nguoi_xuat_phieu)
    assert bi_che is False
    assert ten == "Tên đã lưu"


# ================= Toàn bộ phiếu Excel =================

def test_phieu_ca_nhan_khong_lo_thong_tin_khi_nguoi_xuat_thieu_cap_do():
    nguoi_xuat_phieu = {"_id": "u_van_thu", "clearance_level": 0, "role": "director"}
    wb = dung_phieu_ca_nhan(
        evaluation=phieu_don_gian(),
        tasks_by_id={"t1": nhiem_vu_mat()},
        current_user=nguoi_xuat_phieu,
        ten_don_vi="Phòng Tham mưu",
    )
    noi_dung = noi_dung_toan_bo(wb)

    assert TEN_THAT not in noi_dung
    assert MO_TA_MAT not in noi_dung
    assert HO_SO_GOC not in noi_dung
    assert "mat-01.pdf" not in noi_dung
    assert "Tủ hồ sơ mật" not in noi_dung
    # Tên đã lưu lúc tự đánh giá (bởi người có quyền xem) cũng không được lọt qua
    assert "đã lưu lúc tự đánh giá" not in noi_dung

    assert MA_HIEU in noi_dung
    assert "che nội dung" in noi_dung.lower() or "chỉ hiển thị mã hiệu" in noi_dung


def test_phieu_ca_nhan_hien_thi_day_du_khi_nguoi_xuat_du_cap_do():
    nguoi_xuat_phieu = {"_id": "u_giam_doc", "clearance_level": 2, "role": "director"}
    wb = dung_phieu_ca_nhan(
        evaluation=phieu_don_gian(),
        tasks_by_id={"t1": nhiem_vu_mat()},
        current_user=nguoi_xuat_phieu,
        ten_don_vi="Phòng Tham mưu",
    )
    noi_dung = noi_dung_toan_bo(wb)
    assert TEN_THAT in noi_dung


def test_phieu_ca_nhan_khong_tin_ten_da_luu_ke_ca_khi_khong_co_nhiem_vu_mat():
    """Nhiệm vụ thường (không mật) thì không có gì để che — tên đã lưu vẫn hiện ra bình thường."""
    task_thuong = {
        "code": "NV-2026-06-0008", "title": "Soạn thảo báo cáo tháng",
        "classification": "thuong", "kpi_point": 90,
        "assigned_to": "u_khac", "co_assignees": [],
    }
    nguoi_xuat_phieu = {"_id": "u_van_thu", "clearance_level": 0, "role": "director"}
    wb = dung_phieu_ca_nhan(
        evaluation=phieu_don_gian(),
        tasks_by_id={"t1": task_thuong},
        current_user=nguoi_xuat_phieu,
        ten_don_vi="Phòng Tham mưu",
    )
    noi_dung = noi_dung_toan_bo(wb)
    assert "Soạn thảo báo cáo tháng" in noi_dung


def test_phieu_ca_nhan_khong_vo_khi_thieu_review_va_approval():
    """Kỳ mới ở Bước 1, chưa thẩm định / chưa xác định điểm vẫn xuất được phiếu (điền 'Chưa xác định')."""
    phieu = {
        "target_id": "u_target", "target_name": "Đồng chí B", "target_role": "staff",
        "period_type": "monthly", "period_month": 7, "period_year": 2026,
        "self_evaluation": {"task_scores": [diem_nhiem_vu()]},
    }
    wb = dung_phieu_ca_nhan(
        evaluation=phieu, tasks_by_id={}, current_user={"_id": "u1", "clearance_level": 0},
        ten_don_vi="Đội 1",
    )
    noi_dung = noi_dung_toan_bo(wb)
    assert "Chưa xác định" in noi_dung


def test_bang_tong_hop_khong_dinh_kem_thong_tin_nhiem_vu():
    """Bảng tổng hợp cấp đơn vị chỉ có điểm số, không có dữ liệu nhiệm vụ nên không thể rò rỉ độ mật."""
    items = [{
        "target_name": "Đồng chí C", "role": "leader",
        "score_A": 1.0, "score_B": 0.939, "score_C": 1.0, "score_D": 0.8,
        "kpi_score": 97.97, "kpi_group": "group_1",
        "total_E": 30, "total_final_score": 98.579,
    }]
    wb = dung_bang_tong_hop(items=items, ten_don_vi="Phòng Tham mưu", ky_danh_gia="Tháng 6/2026")
    noi_dung = noi_dung_toan_bo(wb)
    assert "Đồng chí C" in noi_dung
    assert "98,579" in noi_dung or "98.579" in noi_dung


# ---------------------------------------------------------------------------
# Phiếu phải IN RA KÝ ĐƯỢC
#
# Nhóm test trên khoá phần bảo mật. Nhóm dưới khoá phần công dụng: một tờ phiếu
# đúng số liệu nhưng in ra vỡ ba trang, thiếu dòng tổng, hoặc điểm là chữ không
# cộng được thì đơn vị vẫn không dùng vào việc gì.
# ---------------------------------------------------------------------------

def phieu_co_tieu_chi_e():
    """Phiếu có chấm điểm tiêu chí chung, để kiểm phần mục III."""
    p = phieu_don_gian()
    p["general_criteria"] = {
        "scores": [
            {"criteria_id": "III_1_1", "criteria_name": "Bản lĩnh chính trị",
             "max_score": 2, "rating": "dam_bao", "actual_score": 2},
            {"criteria_id": "III_1_2", "criteria_name": "Chấp hành kỷ luật",
             "max_score": 2, "rating": "khong_dam_bao", "actual_score": 0},
        ],
        "total_E": 28.0,
        "total_final_score": 98.0,
    }
    return p


def test_phieu_ca_nhan_dat_du_thiet_lap_in():
    """
    Không đặt khổ giấy và co vừa bề ngang thì Excel dùng mặc định Letter, in dọc,
    không co — phiếu 8 cột tràn sang trang thứ hai theo chiều ngang.
    """
    wb = dung_phieu_ca_nhan(
        evaluation=phieu_co_tieu_chi_e(), tasks_by_id={},
        current_user={"role": "admin", "clearance_level": 3, "_id": "u1"},
        ten_don_vi="Phòng Thử nghiệm",
    )
    ws = wb.active
    # openpyxl khai báo hằng số khổ giấy là chuỗi nhưng lưu vào tệp là số
    assert int(ws.page_setup.paperSize) == int(ws.PAPERSIZE_A4)
    assert ws.page_setup.orientation == "portrait"
    assert ws.sheet_properties.pageSetUpPr.fitToPage is True
    assert ws.page_setup.fitToWidth == 1
    # fitToHeight = 0 nghĩa là dài bao nhiêu trang cũng được, chỉ ép bề ngang
    assert ws.page_setup.fitToHeight == 0
    assert ws.print_area, "Thiếu vùng in nên Excel tự đoán, dễ lôi theo cột thừa"
    assert ws.print_title_rows, "Bảng nhiệm vụ sang trang sau sẽ mất hàng tiêu đề cột"


def test_bang_tong_hop_in_ngang_va_ghim_dong_tieu_de():
    """Bảng tổng hợp 11 cột chỉ vừa khổ ngang; danh sách dài nên phải ghim tiêu đề."""
    wb = dung_bang_tong_hop(items=[], ten_don_vi="Phòng Thử nghiệm", ky_danh_gia="Tháng 6/2026")
    ws = wb.active
    assert ws.page_setup.orientation == "landscape"
    assert ws.page_setup.fitToWidth == 1
    assert ws.print_title_rows
    assert ws.freeze_panes


def test_phieu_ca_nhan_in_ro_tong_diem_tieu_chi_chung():
    """
    Mục IV lấy E để ra tổng điểm, nên E phải hiện thành một con số. Thiếu dòng
    này thì người ký phải tự cộng từng tiêu chí.
    """
    wb = dung_phieu_ca_nhan(
        evaluation=phieu_co_tieu_chi_e(), tasks_by_id={},
        current_user={"role": "admin", "clearance_level": 3, "_id": "u1"},
        ten_don_vi="Phòng Thử nghiệm",
    )
    ws = wb.active
    o_tong_e = [
        ws.cell(row=h, column=5).value
        for h in range(1, ws.max_row + 1)
        if str(ws.cell(row=h, column=1).value or "").startswith("Tổng điểm tiêu chí chung")
    ]
    assert o_tong_e, "Phiếu không có dòng tổng điểm tiêu chí chung (E)"
    assert o_tong_e[0] == 28.0


def test_diem_tren_phieu_la_so_that_khong_phai_chuoi():
    """
    Ghi điểm bằng chuỗi đã format sẵn thì Excel không cộng, không lọc, không vẽ
    biểu đồ được — bảng điểm mất luôn công dụng của bảng tính.
    """
    wb = dung_phieu_ca_nhan(
        evaluation=phieu_co_tieu_chi_e(), tasks_by_id={},
        current_user={"role": "admin", "clearance_level": 3, "_id": "u1"},
        ten_don_vi="Phòng Thử nghiệm",
    )
    ws = wb.active
    kiem = 0
    for h in range(1, ws.max_row + 1):
        nhan = str(ws.cell(row=h, column=1).value or "")
        if nhan.startswith(("A —", "B —", "C —", "Điểm KPI", "Tổng điểm xếp loại")):
            o = ws.cell(row=h, column=7)
            assert isinstance(o.value, float), f"Ô {nhan!r} đang là {type(o.value).__name__}"
            assert o.number_format in ("0.000", "0.00")
            kiem += 1
    assert kiem >= 4, "Không tìm đủ các ô điểm để kiểm"


def test_bang_tong_hop_khong_lap_lai_cot_xep_loai():
    """Bản đầu có cả 'Nhóm xếp loại' lẫn 'Xếp loại' in ra y hệt nhau."""
    wb = dung_bang_tong_hop(
        items=[{"target_name": "Đồng chí B", "role": "staff", "score_A": 1.0,
                "score_B": 1.0, "score_C": 1.0, "kpi_score": 100.0,
                "kpi_group": "group_1", "total_E": 30.0, "total_final_score": 100.0}],
        ten_don_vi="Phòng Thử nghiệm", ky_danh_gia="Tháng 6/2026",
    )
    ws = wb.active
    hang_tieu_de = next(
        h for h in range(1, ws.max_row + 1) if ws.cell(row=h, column=1).value == "STT"
    )
    tieu_de = [ws.cell(row=hang_tieu_de, column=c).value for c in range(1, ws.max_column + 1)]
    assert len(tieu_de) == len(set(tieu_de)), f"Có cột trùng tên: {tieu_de}"
    assert "Nhóm xếp loại" not in tieu_de and "Xếp loại" in tieu_de

    hang_du_lieu = hang_tieu_de + 1
    gia_tri = [ws.cell(row=hang_du_lieu, column=c).value for c in range(1, ws.max_column + 1)]
    nhan_nhom = [g for g in gia_tri if isinstance(g, str) and g.startswith("Nhóm 1")]
    assert len(nhan_nhom) == 1, f"Nhãn xếp loại bị in {len(nhan_nhom)} lần trên cùng một dòng"
