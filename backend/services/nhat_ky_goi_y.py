"""
Nhật ký gợi ý phân công — ghi lại lãnh đạo có làm theo gợi ý của mô hình không.

VÌ SAO CÓ SỔ NÀY
----------------
Cả hệ thống dựa trên một tuyên bố: "mô hình chỉ gợi ý, người có thẩm quyền quyết
định". Tuyên bố đó tới nay không kiểm chứng được bằng gì — người đọc chỉ có thể
tin hoặc không tin. Sổ này biến nó thành con số: trong N lượt giao nhiệm vụ có mở
gợi ý, lãnh đạo chọn đúng người mô hình xếp đầu bao nhiêu lượt, chọn người khác
trong danh sách bao nhiêu, và chọn người hoàn toàn ngoài danh sách bao nhiêu.

Con số cuối cùng mới là con số đáng giá: nó chứng minh mô hình KHÔNG quyết định
thay người. Nếu tỷ lệ làm theo gợi ý đạt 100% thì đó là dấu hiệu xấu — lãnh đạo
đã bấm theo máy chứ không còn cân nhắc.

GHI ĐÚNG QUYẾT ĐỊNH, KHÔNG GHI GÌ THÊM
--------------------------------------
Không ghi tên nhiệm vụ, không ghi nội dung, không ghi độ mật — chỉ mã nhiệm vụ,
người được chọn, thứ hạng và điểm. Nhiệm vụ có độ mật đi qua đây cũng không để
lại chữ nào về nội dung.

Sổ này ghi vào collection riêng `ai_suggestion_logs`. TUYỆT ĐỐI không đụng tới
`kpi_evaluations` — ghi nhận một quyết định phân công không được phép làm xê dịch
điểm KPI của bất kỳ ai. Có test khoá lại điều này.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from backend.database import db

# Chỉ lấy các trường cần cho thống kê. Bản ghi rất nhỏ nhưng vẫn nêu projection
# cho thống nhất với phần còn lại của hệ thống.
NHAT_KY_TOI_THIEU = {"xep_hang_da_chon": 1, "so_goi_y": 1, "department_id": 1}


async def ghi(
    nguoi_quyet_dinh: Dict[str, Any],
    nhiem_vu_id: Optional[str],
    da_chon_id: Optional[str],
    xep_hang_da_chon: Optional[int],
    so_goi_y: int,
    diem_hang_1: Optional[float] = None,
    diem_da_chon: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Ghi một lượt quyết định phân công có mở gợi ý.

    `xep_hang_da_chon` là thứ hạng của người được chọn trong danh sách mô hình đưa
    ra, đếm từ 1. None nghĩa là lãnh đạo chọn người hoàn toàn ngoài danh sách —
    đây chính là trường hợp đáng ghi nhất.
    """
    ban_ghi = {
        "ma_mo_hinh": "goi_y_phan_cong",
        "nhiem_vu_id": nhiem_vu_id,
        "nguoi_quyet_dinh_id": str(nguoi_quyet_dinh.get("_id", "")),
        "nguoi_quyet_dinh_ten": nguoi_quyet_dinh.get("name"),
        "department_id": nguoi_quyet_dinh.get("department_id"),
        "da_chon_id": da_chon_id,
        "xep_hang_da_chon": xep_hang_da_chon,
        "so_goi_y": so_goi_y,
        "diem_hang_1": diem_hang_1,
        "diem_da_chon": diem_da_chon,
        "created_at": datetime.utcnow(),
    }
    await db.ai_suggestion_logs.insert_one(ban_ghi)
    return ban_ghi


async def tom_tat(department_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Đếm các lượt đã ghi, chia theo mức độ làm theo gợi ý.

    Không có lượt nào thì trả về tổng bằng 0 chứ không trả None: giao diện vẫn
    hiện khối và nói thẳng là chưa có dữ liệu, thay vì giấu đi làm người xem
    tưởng hệ thống không có cơ chế này.
    """
    loc = {"department_id": department_id} if department_id else {}
    ban_ghi = await db.ai_suggestion_logs.find(loc, NHAT_KY_TOI_THIEU).to_list(20000)

    tong = len(ban_ghi)
    theo_hang_1 = sum(1 for b in ban_ghi if b.get("xep_hang_da_chon") == 1)
    theo_goi_y_khac = sum(
        1 for b in ban_ghi
        if b.get("xep_hang_da_chon") is not None and b["xep_hang_da_chon"] > 1
    )
    ngoai_danh_sach = tong - theo_hang_1 - theo_goi_y_khac

    return {
        "tong": tong,
        "theo_hang_1": theo_hang_1,
        "theo_goi_y_khac": theo_goi_y_khac,
        "ngoai_danh_sach": ngoai_danh_sach,
        "ty_le_theo_goi_y": (
            round((theo_hang_1 + theo_goi_y_khac) / tong, 3) if tong else None
        ),
        "ghi_chu": (
            "Đếm các lượt giao nhiệm vụ mà lãnh đạo có mở gợi ý phân công. Lượt "
            "chọn người ngoài danh sách không phải là mô hình sai — mô hình chỉ "
            "nhìn được số liệu tải việc và lịch sử, còn lãnh đạo biết những điều "
            "hệ thống không có: ai đang đi học, ai vừa nhận việc đột xuất, ai cần "
            "được giao việc khó để rèn. Trên bản chạy thử với dữ liệu mẫu, các lượt "
            "này do bộ sinh dữ liệu tạo ra, không phải thao tác thật của cán bộ."
        ),
    }
