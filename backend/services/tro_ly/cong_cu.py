"""
Bộ công cụ trợ lý được phép gọi.

Mỗi công cụ tự áp phạm vi theo phân quyền của người hỏi và tự lọc nhiệm vụ có
độ mật. KHÔNG tin vào tham số do mô hình sinh ra để mở rộng phạm vi — mô hình
chỉ chọn công cụ và truyền tham số lọc, còn ai được xem gì là do đây quyết định.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database import db
from backend.models.security_policy import CLASSIFICATION_LABELS, rank_of
from backend.services.ai import guideline
from backend.services.kpi_service import determine_kpi_group

# Nhãn tiếng Việt để mô hình khỏi phải đoán nghĩa mã
NHAN_TRANG_THAI = {
    "assigned": "đã giao", "in_progress": "đang thực hiện",
    "review": "đang hoàn thiện", "done": "đã hoàn thành",
}
NHAN_NHOM = {
    "group_1": "Nhóm 1 (đáp ứng tốt)",
    "group_2": "Nhóm 2 (đáp ứng)",
    "group_3": "Nhóm 3 (chưa đáp ứng)",
}
NHAN_QUY_TRINH = {
    "draft": "chưa tự đánh giá", "self_evaluating": "chờ thẩm định",
    "reviewing": "chờ xác định điểm KPI", "approved": "đã xác định điểm KPI",
    "rejected": "bị trả lại",
}


# ================= PHẠM VI VÀ LỌC MẬT =================

def _pham_vi_nhiem_vu(nguoi_hoi: dict) -> Dict[str, Any]:
    """Điều kiện truy vấn nhiệm vụ, lặp đúng quy tắc của routers/tasks.py."""
    vai = nguoi_hoi.get("role", "staff")
    if vai == "admin":
        return {}
    if vai in ("leader", "director") and nguoi_hoi.get("department_id"):
        return {"department_id": nguoi_hoi["department_id"]}
    return {"assigned_to": str(nguoi_hoi["_id"])}


def loc_mat(nhiem_vu: List[dict], nguoi_hoi: dict) -> tuple[List[dict], int]:
    """
    Tách nhiệm vụ có độ mật ra khỏi danh sách gửi cho mô hình.

    Trả về (danh sách an toàn, số nhiệm vụ mật đã lược). Nhiệm vụ mật chỉ được
    ĐẾM, tuyệt đối không kể tên — kể cả tên gọi quy ước hay mã hiệu, kể cả khi
    người hỏi có đủ cấp độ tiếp cận. Người hỏi xem được trên giao diện là việc
    khác; đưa ra dịch vụ bên ngoài là việc khác.
    """
    an_toan, so_mat = [], 0
    for t in nhiem_vu:
        if rank_of(t.get("classification")) > 0:
            so_mat += 1
            continue
        an_toan.append(t)
    return an_toan, so_mat


def _gon_nhiem_vu(t: dict) -> dict:
    han = t.get("deadline")
    return {
        "ten": t.get("title"),
        "san_pham": t.get("product"),
        "diem": t.get("kpi_point"),
        "so_luong_giao": t.get("quantity_assigned"),
        "so_luong_xong": t.get("quantity_completed"),
        "trang_thai": NHAN_TRANG_THAI.get(t.get("status"), t.get("status")),
        "han": han.strftime("%d/%m/%Y") if han else None,
        "qua_han": bool(han and han < datetime.utcnow() and t.get("status") != "done"),
        "so_lan_sua": t.get("revision_count", 0),
        "so_lan_nhac": t.get("reminder_count", 0),
    }


# ================= CÁC CÔNG CỤ =================

async def tra_cuu_huong_dan(nguoi_hoi: dict, cau_hoi: str) -> dict:
    """
    Tra Hướng dẫn 20-HD/ĐUCA. Con số lấy từ hằng số của bộ máy chấm điểm nên
    luôn khớp với điều hệ thống thực sự tính — mô hình chỉ diễn đạt lại.
    """
    kq = guideline.answer(cau_hoi)
    return {
        "tra_loi_chinh_xac": kq.get("rule_answer"),
        "dieu_khoan": [
            {"tieu_de": c["title"], "muc": c["source"], "nguyen_van": c["text"]}
            for c in kq.get("clauses", [])[:3]
        ],
        "luu_y": "Đây là trích dẫn nguyên văn. Không diễn giải sai lệch con số.",
    }


async def nhiem_vu(nguoi_hoi: dict, trang_thai: Optional[str] = None,
                   chi_qua_han: bool = False) -> dict:
    """Nhiệm vụ trong phạm vi người hỏi được xem, kỳ hiện tại."""
    now = datetime.utcnow()
    q = {**_pham_vi_nhiem_vu(nguoi_hoi), "period_month": now.month, "period_year": now.year}
    if trang_thai in NHAN_TRANG_THAI:
        q["status"] = trang_thai

    ds = await db.tasks.find(q).sort("deadline", 1).to_list(300)
    if chi_qua_han:
        ds = [t for t in ds
              if t.get("status") != "done" and t.get("deadline") and t["deadline"] < now]

    an_toan, so_mat = loc_mat(ds, nguoi_hoi)
    tong_diem = sum(t.get("kpi_point", 0) * (t.get("quantity_assigned", 1) or 1) for t in ds)

    return {
        "ky": f"tháng {now.month}/{now.year}",
        "tong_so": len(ds),
        "so_qua_han": sum(1 for t in ds if t.get("status") != "done"
                          and t.get("deadline") and t["deadline"] < now),
        "so_da_hoan_thanh": sum(1 for t in ds if t.get("status") == "done"),
        "tong_diem_duoc_giao": tong_diem,
        "danh_sach": [_gon_nhiem_vu(t) for t in an_toan[:25]],
        "so_nhiem_vu_mat_da_luoc": so_mat,
        "ghi_chu_mat": (
            f"Có {so_mat} nhiệm vụ mang độ mật đã được lược khỏi danh sách. "
            "Chỉ nói số lượng, tuyệt đối không đoán hay bịa tên các nhiệm vụ này."
        ) if so_mat else None,
    }


async def ket_qua_kpi(nguoi_hoi: dict, nam: Optional[int] = None) -> dict:
    """Điểm KPI của chính người hỏi theo từng tháng trong năm."""
    nam = nam or datetime.utcnow().year
    ds = await db.kpi_evaluations.find({
        "target_id": str(nguoi_hoi["_id"]),
        "evaluation_type": "individual",
        "period_type": "monthly",
        "period_year": nam,
    }).sort("period_month", 1).to_list(24)

    ky = []
    diem_da_duyet = []
    for e in ds:
        a = e.get("approval") or {}
        g = e.get("general_criteria") or {}
        ky.append({
            "thang": e.get("period_month"),
            "trang_thai": NHAN_QUY_TRINH.get(e.get("overall_status"), e.get("overall_status")),
            "A": a.get("score_A"), "B": a.get("score_B"),
            "C": a.get("score_C"), "D": a.get("score_D"),
            "kpi": a.get("kpi_score"),
            "nhom": NHAN_NHOM.get(a.get("kpi_group")),
            "diem_tieu_chi_chung_E": g.get("total_E"),
            "tong_diem_xep_loai": g.get("total_final_score"),
        })
        if a.get("kpi_score") is not None:
            diem_da_duyet.append(a["kpi_score"])

    return {
        "nam": nam,
        "cac_ky": ky,
        "kpi_binh_quan_nam": round(sum(diem_da_duyet) / len(diem_da_duyet), 2) if diem_da_duyet else None,
        "so_ky_da_duyet": len(diem_da_duyet),
    }


async def tong_quan_don_vi(nguoi_hoi: dict) -> dict:
    """Tổng quan đơn vị — chỉ lãnh đạo, chỉ huy trở lên."""
    vai = nguoi_hoi.get("role", "staff")
    if vai not in ("leader", "director", "admin"):
        return {"tu_choi": "Chỉ lãnh đạo, chỉ huy trở lên mới xem được tổng quan đơn vị."}

    now = datetime.utcnow()
    dept = nguoi_hoi.get("department_id")
    q_user = {"role": {"$ne": "admin"}}
    q_task = {"period_month": now.month, "period_year": now.year}
    if vai != "admin" and dept:
        q_user["department_id"] = dept
        q_task["department_id"] = dept

    can_bo = await db.users.find(q_user).to_list(300)
    viec = await db.tasks.find(q_task).to_list(3000)

    q_eval = {"period_month": now.month, "period_year": now.year,
              "evaluation_type": "individual"}
    if vai != "admin" and dept:
        q_eval["department_id"] = dept
    ho_so = await db.kpi_evaluations.find(q_eval).to_list(500)

    theo_trang_thai: Dict[str, int] = {}
    for e in ho_so:
        n = NHAN_QUY_TRINH.get(e.get("overall_status"), "khác")
        theo_trang_thai[n] = theo_trang_thai.get(n, 0) + 1

    return {
        "ky": f"tháng {now.month}/{now.year}",
        "so_can_bo": len(can_bo),
        "so_nhiem_vu": len(viec),
        "so_da_hoan_thanh": sum(1 for t in viec if t.get("status") == "done"),
        "so_qua_han": sum(1 for t in viec if t.get("status") != "done"
                          and t.get("deadline") and t["deadline"] < now),
        "so_nhiem_vu_co_do_mat": sum(1 for t in viec if rank_of(t.get("classification")) > 0),
        "ho_so_danh_gia_theo_trang_thai": theo_trang_thai,
    }


async def can_bo_can_luu_y(nguoi_hoi: dict) -> dict:
    """Cán bộ trong đơn vị đang tồn nhiều việc hoặc quá hạn — lãnh đạo trở lên."""
    vai = nguoi_hoi.get("role", "staff")
    if vai not in ("leader", "director", "admin"):
        return {"tu_choi": "Chỉ lãnh đạo, chỉ huy trở lên mới xem được thông tin cán bộ khác."}

    now = datetime.utcnow()
    q_user = {"role": {"$ne": "admin"}}
    q_task = {"period_month": now.month, "period_year": now.year}
    if vai != "admin" and nguoi_hoi.get("department_id"):
        q_user["department_id"] = nguoi_hoi["department_id"]
        q_task["department_id"] = nguoi_hoi["department_id"]

    can_bo = await db.users.find(q_user).to_list(300)
    viec = await db.tasks.find(q_task).to_list(3000)

    theo_nguoi: Dict[str, List[dict]] = {}
    for t in viec:
        if t.get("assigned_to"):
            theo_nguoi.setdefault(t["assigned_to"], []).append(t)

    ds = []
    for u in can_bo:
        uid = str(u["_id"])
        cua_ho = theo_nguoi.get(uid, [])
        if not cua_ho:
            continue
        qua_han = sum(1 for t in cua_ho if t.get("status") != "done"
                      and t.get("deadline") and t["deadline"] < now)
        con_ton = sum(t.get("kpi_point", 0) * (t.get("quantity_assigned", 1) or 1)
                      for t in cua_ho if t.get("status") != "done")
        dinh_muc = int(u.get("capacity_points", 300) or 300)
        ds.append({
            "ten": u.get("name"),
            "cap_bac_chuc_vu": " · ".join(x for x in (u.get("rank"), u.get("position")) if x),
            "so_viec": len(cua_ho),
            "so_da_xong": sum(1 for t in cua_ho if t.get("status") == "done"),
            "so_qua_han": qua_han,
            "tai_viec_phan_tram": round(con_ton / dinh_muc * 100) if dinh_muc else None,
        })

    ds.sort(key=lambda x: (-x["so_qua_han"], -(x["tai_viec_phan_tram"] or 0)))
    return {"ky": f"tháng {now.month}/{now.year}", "can_bo": ds[:15]}


# ================= KHAI BÁO CHO MÔ HÌNH =================

BANG_CONG_CU = {
    "tra_cuu_huong_dan": tra_cuu_huong_dan,
    "nhiem_vu": nhiem_vu,
    "ket_qua_kpi": ket_qua_kpi,
    "tong_quan_don_vi": tong_quan_don_vi,
    "can_bo_can_luu_y": can_bo_can_luu_y,
}

KHAI_BAO = [
    {
        "name": "tra_cuu_huong_dan",
        "description": (
            "Tra Hướng dẫn số 20-HD/ĐUCA về cách tính điểm KPI: mức điểm chất lượng theo "
            "số lần chỉnh sửa, mức điểm tiến độ theo số lần nhắc nhở, công thức A/B/C/D, "
            "ngưỡng phân nhóm, tiêu chí chung E, quy trình 3 bước. BẮT BUỘC gọi công cụ này "
            "cho mọi câu hỏi về con số hoặc quy định — không được tự suy ra."
        ),
        "parameters": {
            "type": "object",
            "properties": {"cau_hoi": {"type": "string", "description": "Câu hỏi của người dùng"}},
            "required": ["cau_hoi"],
        },
    },
    {
        "name": "nhiem_vu",
        "description": (
            "Nhiệm vụ công tác trong kỳ hiện tại thuộc phạm vi người hỏi được xem. "
            "Dùng khi hỏi về việc được giao, việc quá hạn, tiến độ, khối lượng."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "trang_thai": {
                    "type": "string",
                    "enum": ["assigned", "in_progress", "review", "done"],
                    "description": "Lọc theo trạng thái, bỏ trống là lấy tất cả",
                },
                "chi_qua_han": {"type": "boolean", "description": "Chỉ lấy nhiệm vụ đã quá hạn"},
            },
        },
    },
    {
        "name": "ket_qua_kpi",
        "description": (
            "Điểm KPI theo từng tháng của chính người hỏi, gồm A, B, C, D, điểm KPI, "
            "nhóm xếp loại, điểm tiêu chí chung E và tổng điểm xếp loại."
        ),
        "parameters": {
            "type": "object",
            "properties": {"nam": {"type": "integer", "description": "Năm cần xem, mặc định năm hiện tại"}},
        },
    },
    {
        "name": "tong_quan_don_vi",
        "description": (
            "Tổng quan đơn vị trong kỳ: số cán bộ, số nhiệm vụ, số hoàn thành, số quá hạn, "
            "tình hình hồ sơ đánh giá. Chỉ lãnh đạo, chỉ huy trở lên dùng được."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "can_bo_can_luu_y",
        "description": (
            "Danh sách cán bộ trong đơn vị kèm số việc, số quá hạn và mức tải việc, "
            "sắp theo mức cần lưu ý. Chỉ lãnh đạo, chỉ huy trở lên dùng được."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
]


async def goi_cong_cu(ten: str, tham_so: dict, nguoi_hoi: dict) -> dict:
    """Gọi một công cụ. Tên lạ thì báo lỗi thay vì ném ngoại lệ."""
    ham = BANG_CONG_CU.get(ten)
    if not ham:
        return {"loi": f"Không có công cụ tên {ten}"}
    try:
        return await ham(nguoi_hoi, **(tham_so or {}))
    except TypeError as e:
        return {"loi": f"Tham số không hợp lệ: {e}"}
