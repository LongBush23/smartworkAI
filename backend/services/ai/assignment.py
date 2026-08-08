"""
Gợi ý cán bộ phù hợp để giao một nhiệm vụ công tác.

VÌ SAO DÙNG CÔNG THỨC CÓ TRỌNG SỐ, KHÔNG DÙNG MÁY HỌC
------------------------------------------------------
Đây là lựa chọn kỹ thuật có chủ đích:

  1. Dữ liệu quá ít để học "ai hợp việc gì". Mỗi cán bộ chỉ có vài nhiệm vụ
     mỗi kỳ, chia tiếp theo nhóm độ phức tạp và loại sản phẩm thì còn rất mỏng.
     Mô hình học trên đó sẽ khớp nhiễu chứ không học được quy luật.

  2. Giao nhiệm vụ là quyết định về con người, phải giải thích được. Lãnh đạo
     cần biết VÌ SAO hệ thống xếp người này trước người kia — công thức có
     trọng số in ra được từng thành phần, mô hình học máy thì không.

  3. Không cần huấn luyện lại, không lệch theo thời gian.

Hệ thống chỉ GỢI Ý. Người có thẩm quyền quyết định giao cho ai.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.database import db
from backend.services.ai.projections import KPI_TOI_THIEU, NHIEM_VU_DAC_TRUNG
from backend.models.security_policy import rank_of, CLASSIFICATION_LABELS

# Trọng số từng thành phần. Tổng bằng 1,0.
TRONG_SO = {
    "du_dia_tai_viec": 0.35,      # còn chỗ nhận việc không
    "chat_luong_lich_su": 0.25,   # ít phải chỉnh sửa ở nhóm độ phức tạp này
    "tien_do_lich_su": 0.20,      # ít bị nhắc nhở ở loại sản phẩm này
    "khong_qua_han": 0.10,        # đang không tồn việc quá hạn
    "kpi_gan_nhat": 0.10,         # kết quả 3 kỳ gần nhất
}

# Ngưỡng loại cứng
TAI_VIEC_TOI_DA = 130.0   # quá 130% định mức thì không giao thêm

# Mốc chuẩn hoá, lấy từ bảng mức trong Hướng dẫn
SO_LAN_SUA_MAT_DIEM = 7     # từ 7 lần thì không tính điểm
SO_LAN_NHAC_MAT_DIEM = 4    # từ 4 lần thì không tính điểm


async def suggest(
    department_id: str,
    classification: str = "thuong",
    complexity_group: Optional[int] = None,
    product: Optional[str] = None,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Xếp hạng cán bộ trong đơn vị theo mức phù hợp với nhiệm vụ sắp giao.

    Trả về cả danh sách được đề xuất VÀ danh sách bị loại kèm lý do, để lãnh đạo
    thấy rõ hệ thống đã cân nhắc những ai.
    """
    now = datetime.utcnow()
    month = period_month or now.month
    year = period_year or now.year
    required_clearance = rank_of(classification)

    users = await db.users.find({
        "department_id": department_id,
        "role": {"$ne": "admin"},
    }, {
        "name": 1, "rank": 1, "position": 1, "department_id": 1,
        "capacity_points": 1, "clearance_level": 1,
    }).to_list(500)

    tasks = await db.tasks.find({
        "department_id": department_id,
        "period_month": month,
        "period_year": year,
    }, NHIEM_VU_DAC_TRUNG).to_list(2000)

    # Lịch sử để đánh giá chất lượng, tiến độ — lấy cả các kỳ trước
    history = await db.tasks.find(
        {"department_id": department_id}, NHIEM_VU_DAC_TRUNG
    ).to_list(5000)

    evaluations = await db.kpi_evaluations.find({
        "department_id": department_id,
        "evaluation_type": "individual",
        "period_type": "monthly",
        "overall_status": "approved",
        "period_year": year,
    }, KPI_TOI_THIEU).to_list(2000)

    # Gom dữ liệu theo cán bộ
    tasks_by_user: Dict[str, List[dict]] = {}
    for t in tasks:
        if t.get("assigned_to"):
            tasks_by_user.setdefault(t["assigned_to"], []).append(t)

    history_by_user: Dict[str, List[dict]] = {}
    for t in history:
        if t.get("assigned_to"):
            history_by_user.setdefault(t["assigned_to"], []).append(t)

    kpi_by_user: Dict[str, List[float]] = {}
    for e in sorted(evaluations, key=lambda x: x.get("period_month") or 0):
        score = (e.get("approval") or {}).get("kpi_score")
        if score is not None:
            kpi_by_user.setdefault(e["target_id"], []).append(score)

    suggested: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []

    for u in users:
        uid = str(u["_id"])
        name = u.get("name", "")
        rank_position = " · ".join(x for x in (u.get("rank"), u.get("position")) if x)
        clearance = int(u.get("clearance_level", 0) or 0)

        # ---- Lọc cứng 1: cấp độ tiếp cận ----
        if clearance < required_clearance:
            excluded.append({
                "id": uid, "name": name, "rank_position": rank_position,
                "reason_code": "thieu_cap_do_tiep_can",
                "reason": (
                    f"Không đủ cấp độ tiếp cận để nhận nhiệm vụ độ "
                    f"{CLASSIFICATION_LABELS.get(classification, classification)}"
                ),
            })
            continue

        # ---- Tải việc hiện tại ----
        my_tasks = tasks_by_user.get(uid, [])
        capacity = int(u.get("capacity_points", 300) or 300)
        open_points = sum(
            t.get("kpi_point", 0) * (t.get("quantity_assigned", 1) or 1)
            for t in my_tasks if t.get("status") != "done"
        )
        workload = round(open_points / capacity * 100, 1) if capacity else 0.0

        # ---- Lọc cứng 2: quá tải ----
        if workload > TAI_VIEC_TOI_DA:
            excluded.append({
                "id": uid, "name": name, "rank_position": rank_position,
                "reason_code": "qua_tai",
                "reason": f"Đang quá tải {workload:.0f}% định mức ({open_points}/{capacity} điểm)",
            })
            continue

        # ---- Các thành phần điểm ----
        my_history = history_by_user.get(uid, [])

        # Chất lượng: số lần chỉnh sửa trung bình ở CÙNG nhóm độ phức tạp
        same_group = [t for t in my_history if complexity_group is None
                      or t.get("complexity_group") == complexity_group]
        avg_revision = (
            sum(t.get("revision_count", 0) for t in same_group) / len(same_group)
            if same_group else 0.0
        )

        # Tiến độ: số lần bị nhắc trung bình ở CÙNG loại sản phẩm
        same_product = [t for t in my_history if product is None or t.get("product") == product]
        avg_reminder = (
            sum(t.get("reminder_count", 0) for t in same_product) / len(same_product)
            if same_product else 0.0
        )

        overdue = sum(
            1 for t in my_tasks
            if t.get("status") != "done" and t.get("deadline") and t["deadline"] < now
        )

        recent_kpi = kpi_by_user.get(uid, [])[-3:]
        avg_kpi = sum(recent_kpi) / len(recent_kpi) if recent_kpi else None

        parts = {
            "du_dia_tai_viec": max(0.0, 1 - workload / 100),
            "chat_luong_lich_su": max(0.0, 1 - avg_revision / SO_LAN_SUA_MAT_DIEM),
            "tien_do_lich_su": max(0.0, 1 - avg_reminder / SO_LAN_NHAC_MAT_DIEM),
            "khong_qua_han": 1.0 if overdue == 0 else 0.4,
            # KPI có thể vượt 100 khi hoàn thành vượt mức, nên chặn trên ở 1,0
            "kpi_gan_nhat": min(avg_kpi / 100, 1.0) if avg_kpi is not None else 0.5,
        }
        total = sum(parts[k] * w for k, w in TRONG_SO.items())

        suggested.append({
            "id": uid,
            "name": name,
            "rank_position": rank_position,
            "clearance_level": clearance,
            "score": round(total * 100, 1),
            "workload_percent": workload,
            "open_points": open_points,
            "capacity_points": capacity,
            "avg_revision": round(avg_revision, 2),
            "avg_reminder": round(avg_reminder, 2),
            "tasks_overdue": overdue,
            "recent_kpi": round(avg_kpi, 1) if avg_kpi is not None else None,
            "reasons": _build_reasons(parts, workload, avg_revision, avg_reminder, overdue, avg_kpi),
            "score_breakdown": {k: round(parts[k] * TRONG_SO[k] * 100, 1) for k in TRONG_SO},
        })

    suggested.sort(key=lambda x: -x["score"])

    return {
        "department_id": department_id,
        "classification": classification,
        "required_clearance": required_clearance,
        "complexity_group": complexity_group,
        "product": product,
        "period_month": month,
        "period_year": year,
        "suggested": suggested[:limit],
        "excluded": excluded,
        "total_considered": len(users),
        "weights": TRONG_SO,
        "explanation": (
            "Đây là GỢI Ý để tham khảo, không phải quyết định. Điểm phù hợp là tổng có "
            "trọng số của 5 thành phần, mỗi thành phần đều hiển thị được. "
            "Cán bộ không đủ cấp độ tiếp cận bị loại bắt buộc, không phải bị trừ điểm."
        ),
    }


def _build_reasons(
    parts: Dict[str, float], workload: float, avg_revision: float,
    avg_reminder: float, overdue: int, avg_kpi: Optional[float],
) -> List[str]:
    """Diễn giải bằng lời vì sao cán bộ này được xếp hạng như vậy."""
    reasons: List[str] = []

    if workload < 50:
        reasons.append(f"Còn nhiều dư địa nhận việc (đang dùng {workload:.0f}% định mức)")
    elif workload < 85:
        reasons.append(f"Khối lượng vừa phải ({workload:.0f}% định mức)")
    else:
        reasons.append(f"Gần đầy định mức ({workload:.0f}%)")

    if avg_revision == 0:
        reasons.append("Chưa từng phải chỉnh sửa ở nhóm nhiệm vụ này")
    elif avg_revision < 1:
        reasons.append(f"Ít phải chỉnh sửa (trung bình {avg_revision:.1f} lần)")
    else:
        reasons.append(f"Trung bình phải chỉnh sửa {avg_revision:.1f} lần")

    if avg_reminder == 0:
        reasons.append("Chưa từng bị nhắc nhở ở loại sản phẩm này")
    elif avg_reminder >= 1:
        reasons.append(f"Trung bình bị nhắc nhở {avg_reminder:.1f} lần")

    if overdue > 0:
        reasons.append(f"Đang có {overdue} nhiệm vụ quá hạn")

    if avg_kpi is not None:
        reasons.append(f"KPI bình quân 3 kỳ gần nhất {avg_kpi:.1f}")
    else:
        reasons.append("Chưa có kỳ đánh giá nào được duyệt")

    return reasons
