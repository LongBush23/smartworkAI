"""
Phát hiện dấu hiệu chấm điểm hình thức, thiếu thực chất.

Hướng dẫn 20-HD/ĐUCA yêu cầu đánh giá bảo đảm "thực chất", nhưng không có cơ
chế nào phát hiện đơn vị chấm cho có. Module này nêu các dấu hiệu bất thường
để cơ quan tổ chức cán bộ RÀ SOÁT — không phải kết luận vi phạm.

Thuần thống kê, không dùng máy học: mỗi dấu hiệu là một quy tắc rõ ràng, có
ngưỡng công khai và số liệu kèm theo, để người đọc tự thẩm định.
"""
import statistics
from collections import defaultdict
from typing import Any, Dict, List, Optional

from backend.database import db
from backend.services.ai.projections import KPI_RA_SOAT, KPI_TOI_THIEU, NHIEM_VU_DAC_TRUNG

# Ngưỡng của từng dấu hiệu — đặt ở đây để dễ rà soát và điều chỉnh
NGUONG = {
    "ty_le_diem_E_toi_da": 0.80,      # ≥80% cán bộ đạt 30/30 → đáng ngờ
    "do_lech_chuan_kpi": 3.0,          # std KPI trong đơn vị < 3 điểm → quá đều
    "lech_nhom_tu_danh_gia": 2,        # tự nhận cách kết quả ≥2 nhóm
    "he_so_nhay_vot": 2.0,             # lệch > 2σ so với chính mình
    # Bắt buộc có cả thay đổi TUYỆT ĐỐI đáng kể. Nếu chỉ dùng z-score, cán bộ có
    # điểm rất ổn định (σ gần 0) sẽ bị báo động chỉ vì chênh 1-2 điểm — vô nghĩa
    # trên thang 100 điểm.
    "thay_doi_tuyet_doi_toi_thieu": 10.0,
    "do_lech_chuan_toi_thieu": 3.0,    # sàn cho σ, tránh chia cho số quá nhỏ
    "ty_le_qua_han": 0.30,             # >30% việc quá hạn
    "so_mau_toi_thieu": 4,             # dưới 4 cán bộ thì thống kê vô nghĩa
}

_GROUP_ORDER = {"group_1": 1, "group_2": 2, "group_3": 3}


def _flag(
    severity: str, code: str, title: str, target: str,
    evidence: str, suggestion: str, department_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "severity": severity,          # cao | trung_binh | thap
        "code": code,
        "title": title,
        "target": target,
        "evidence": evidence,
        "suggestion": suggestion,
        "department_id": department_id,
    }


async def detect(
    period_month: int,
    period_year: int,
    department_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rà soát một kỳ đánh giá, trả về danh sách dấu hiệu cần xem lại.

    Chỉ đọc dữ liệu. Không ghi, không thay đổi điểm của bất kỳ ai.
    """
    query: Dict[str, Any] = {
        "period_month": period_month,
        "period_year": period_year,
        "evaluation_type": "individual",
        "overall_status": "approved",
    }
    if department_id:
        query["department_id"] = department_id

    evaluations = await db.kpi_evaluations.find(query, KPI_RA_SOAT).to_list(5000)
    departments = {
        str(d["_id"]): d
        for d in await db.departments.find({}, {"name": 1, "code": 1}).to_list(500)
    }

    flags: List[Dict[str, Any]] = []

    # Gom theo đơn vị
    by_dept: Dict[str, List[dict]] = defaultdict(list)
    for e in evaluations:
        if e.get("department_id"):
            by_dept[e["department_id"]].append(e)

    for dept_id, evals in by_dept.items():
        dept_name = departments.get(dept_id, {}).get("name", "Đơn vị không xác định")
        if len(evals) < NGUONG["so_mau_toi_thieu"]:
            continue

        # --- Dấu hiệu 1: điểm tiêu chí chung đồng loạt tối đa ---
        with_e = [e for e in evals if (e.get("general_criteria") or {}).get("total_E") is not None]
        if with_e:
            maxed = [e for e in with_e if e["general_criteria"]["total_E"] >= 30]
            ratio = len(maxed) / len(with_e)
            if ratio >= NGUONG["ty_le_diem_E_toi_da"]:
                flags.append(_flag(
                    "cao", "diem_E_dong_loat_toi_da",
                    "Điểm tiêu chí chung đồng loạt đạt tối đa",
                    dept_name,
                    f"{len(maxed)}/{len(with_e)} cán bộ đạt 30/30 điểm ({ratio:.0%})",
                    "Rà soát lại việc chấm 30 điểm tiêu chí chung. Tỷ lệ tuyệt đối "
                    "thường là dấu hiệu chấm cho đủ, không đối chiếu thực tế từng tiêu chí.",
                    dept_id,
                ))

        # --- Dấu hiệu 2: điểm KPI quá đồng đều ---
        scores = [
            e["approval"]["kpi_score"] for e in evals
            if (e.get("approval") or {}).get("kpi_score") is not None
        ]
        if len(scores) >= NGUONG["so_mau_toi_thieu"]:
            std = statistics.pstdev(scores)
            if std < NGUONG["do_lech_chuan_kpi"]:
                flags.append(_flag(
                    "trung_binh", "kpi_qua_dong_deu",
                    "Điểm KPI trong đơn vị quá đồng đều",
                    dept_name,
                    f"Độ lệch chuẩn chỉ {std:.2f} điểm trên {len(scores)} cán bộ "
                    f"(thấp nhất {min(scores):.1f} · cao nhất {max(scores):.1f})",
                    "Kết quả thực hiện nhiệm vụ hiếm khi đồng đều đến vậy. "
                    "Đối chiếu lại số lần chỉnh sửa và nhắc nhở của từng cán bộ.",
                    dept_id,
                ))

        # --- Dấu hiệu 5: không ai Nhóm 3 dù nhiều việc quá hạn ---
        tasks = await db.tasks.find({
            "department_id": dept_id,
            "period_month": period_month,
            "period_year": period_year,
        }, NHIEM_VU_DAC_TRUNG).to_list(2000)
        if tasks:
            overdue = sum(
                1 for t in tasks
                if t.get("status") != "done" and t.get("actual_end") is None
                and t.get("deadline") and t["deadline"] < _end_of_period(period_month, period_year)
            )
            ratio_overdue = overdue / len(tasks)
            has_group3 = any(
                (e.get("approval") or {}).get("kpi_group") == "group_3" for e in evals
            )
            if ratio_overdue > NGUONG["ty_le_qua_han"] and not has_group3:
                flags.append(_flag(
                    "cao", "mau_thuan_qua_han_xep_loai",
                    "Nhiều việc quá hạn nhưng không có cán bộ nào xếp Nhóm 3",
                    dept_name,
                    f"{overdue}/{len(tasks)} nhiệm vụ quá hạn ({ratio_overdue:.0%}) "
                    f"nhưng {len(evals)} cán bộ đều xếp Nhóm 1 hoặc Nhóm 2",
                    "Đối chiếu số nhiệm vụ quá hạn với điểm tiến độ (C) của từng cán bộ. "
                    "Có thể việc nhắc nhở chưa được ghi nhận đầy đủ.",
                    dept_id,
                ))

    # --- Dấu hiệu 3: tự đánh giá lệch xa kết quả thẩm định ---
    for e in evaluations:
        proposed = (e.get("self_evaluation") or {}).get("proposed_rating")
        final = (e.get("approval") or {}).get("kpi_group")
        if not proposed or not final:
            continue
        gap = _GROUP_ORDER.get(final, 0) - _GROUP_ORDER.get(proposed, 0)
        if gap >= NGUONG["lech_nhom_tu_danh_gia"]:
            flags.append(_flag(
                "trung_binh", "tu_danh_gia_lech_xa",
                "Tự đánh giá cao hơn nhiều so với kết quả thẩm định",
                e.get("target_name", "Không rõ"),
                f"Tự nhận {_group_label(proposed)}, kết quả xác định là {_group_label(final)} "
                f"(điểm KPI {e['approval'].get('kpi_score', 0):.1f})",
                "Nhắc cán bộ đối chiếu Danh mục nhiệm vụ khi tự chấm. "
                "Chênh lệch lớn kéo dài cần đưa vào nhận xét đánh giá.",
                e.get("department_id"),
            ))

    # --- Dấu hiệu 4: điểm KPI nhảy vọt so với chính mình ---
    target_ids = list({e["target_id"] for e in evaluations})
    if target_ids:
        history = await db.kpi_evaluations.find({
            "target_id": {"$in": target_ids},
            "evaluation_type": "individual",
            "period_type": "monthly",
            "overall_status": "approved",
        }, KPI_TOI_THIEU).to_list(10000)

        by_target: Dict[str, List[dict]] = defaultdict(list)
        for h in history:
            by_target[h["target_id"]].append(h)

        for e in evaluations:
            current = (e.get("approval") or {}).get("kpi_score")
            if current is None:
                continue
            past = sorted(
                [
                    h for h in by_target[e["target_id"]]
                    if (h.get("period_year"), h.get("period_month")) < (period_year, period_month)
                    and (h.get("approval") or {}).get("kpi_score") is not None
                ],
                key=lambda h: (h.get("period_year"), h.get("period_month")),
            )[-3:]

            if len(past) < 3:
                continue
            past_scores = [h["approval"]["kpi_score"] for h in past]
            mean = statistics.mean(past_scores)
            change = abs(current - mean)

            # Phải vượt CẢ HAI: thay đổi tuyệt đối đáng kể VÀ lệch nhiều so với
            # dao động thường thấy của chính cán bộ đó.
            if change < NGUONG["thay_doi_tuyet_doi_toi_thieu"]:
                continue

            std = max(statistics.pstdev(past_scores), NGUONG["do_lech_chuan_toi_thieu"])
            deviation = change / std
            if deviation <= NGUONG["he_so_nhay_vot"]:
                continue

            direction = "tăng vọt" if current > mean else "sụt mạnh"
            flags.append(_flag(
                "thap", "kpi_nhay_vot",
                f"Điểm KPI {direction} bất thường so với chính cán bộ đó",
                e.get("target_name", "Không rõ"),
                f"Kỳ này {current:.1f} điểm, bình quân 3 kỳ trước {mean:.1f} "
                f"(chênh {change:.1f} điểm, gấp {deviation:.1f} lần dao động thường thấy)",
                "Xác minh nguyên nhân: thay đổi khối lượng nhiệm vụ, chuyển vị trí "
                "công tác, hay sai sót khi chấm điểm.",
                e.get("department_id"),
            ))

    order = {"cao": 0, "trung_binh": 1, "thap": 2}
    flags.sort(key=lambda f: order.get(f["severity"], 9))

    return {
        "period_month": period_month,
        "period_year": period_year,
        "total_evaluations": len(evaluations),
        "departments_reviewed": len(by_dept),
        "flags": flags,
        "summary": {
            "cao": sum(1 for f in flags if f["severity"] == "cao"),
            "trung_binh": sum(1 for f in flags if f["severity"] == "trung_binh"),
            "thap": sum(1 for f in flags if f["severity"] == "thap"),
        },
        "thresholds": NGUONG,
        "explanation": (
            "Đây là các DẤU HIỆU cần rà soát, không phải kết luận vi phạm. "
            "Mỗi dấu hiệu dựa trên một quy tắc thống kê có ngưỡng công khai, kèm số liệu "
            "cụ thể để người có thẩm quyền tự thẩm định. Hệ thống không thay đổi điểm của "
            "bất kỳ ai."
        ),
    }


def _group_label(group: str) -> str:
    return {
        "group_1": "Nhóm 1 (đáp ứng tốt)",
        "group_2": "Nhóm 2 (đáp ứng)",
        "group_3": "Nhóm 3 (chưa đáp ứng)",
    }.get(group, group)


def _end_of_period(month: int, year: int):
    """Thời điểm kết thúc kỳ, dùng để xác định việc quá hạn trong kỳ đó."""
    from datetime import datetime
    if month == 12:
        return datetime(year + 1, 1, 1)
    return datetime(year, month + 1, 1)
