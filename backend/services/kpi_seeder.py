"""
Sinh dữ liệu mẫu KPI phủ đủ mọi trường hợp của Hướng dẫn số 20-HD/ĐUCA.

Các trường hợp được bảo đảm có mặt trong dữ liệu:
  1. Danh mục nhiệm vụ đúng 03 nhóm điểm: N1 (0–49), N2 (50–69), N3 (70–100)
  2. Danh mục ở cả 2 trạng thái: đã phê duyệt và bản nháp
  3. Đủ 06 mức điểm chất lượng (B) và 06 mức điểm tiến độ (C)
  4. Đủ 03 nhóm xếp loại KPI: nhóm 1 (70–100), nhóm 2 (50–<70), nhóm 3 (<50)
  5. Đủ 05 trạng thái quy trình: draft, self_evaluating, reviewing, approved, rejected
  6. Cả đánh giá tập thể và cá nhân; cá nhân gồm lãnh đạo (có điểm D) và không lãnh đạo
  7. Nhiều tháng liên tiếp để tính KPI quý và năm (bình quân theo tháng)
  8. Điểm D suy ra từ tỷ lệ cán bộ thuộc quyền hoàn thành nhiệm vụ (nhóm 1 + nhóm 2)
  9. Ràng buộc KPI người đứng đầu không cao hơn KPI tập thể do mình đứng đầu
 10. Điểm E chấm theo đúng bộ tiêu chí chung (tập thể / lãnh đạo / không lãnh đạo)

Điểm A, B, C được TÍNH TỪ task_scores nên số liệu lưu luôn nhất quán với công thức.
"""
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.database import db
from backend.models.kpi_criteria import flatten_criteria, criteria_type_for
from backend.services.kpi_service import (
    get_quality_percent, get_timeline_percent,
    calculate_score_A, calculate_score_B, calculate_score_C,
    calculate_kpi, determine_kpi_group,
)

# ================= KHUNG DANH MỤC NHIỆM VỤ CÔNG TÁC =================

# (tên nhiệm vụ, sản phẩm, nhóm độ phức tạp, điểm)
# Điểm phải nằm đúng dải của nhóm: N1 0–49, N2 50–69, N3 70–100
CATALOG_TEMPLATE = [
    # --- Nhóm 1: 0 đến dưới 50 điểm ---
    ("Tiếp nhận, xử lý văn bản đến", "cong_van", 1, 10),
    ("Soạn thảo công văn trao đổi nghiệp vụ", "cong_van", 1, 15),
    ("Lập báo cáo tuần về tình hình đơn vị", "bao_cao", 1, 20),
    ("Cập nhật, số hóa hồ sơ nghiệp vụ", "khac", 1, 25),
    ("Tổng hợp số liệu phục vụ giao ban", "bao_cao", 1, 30),
    ("Tham gia lớp bồi dưỡng nghiệp vụ", "khac", 1, 35),
    ("Lập báo cáo tháng theo hệ lực lượng", "bao_cao", 1, 45),
    # --- Nhóm 2: 50 đến dưới 70 điểm ---
    ("Xây dựng tờ trình xin ý kiến lãnh đạo Bộ", "to_trinh", 2, 50),
    ("Thẩm định hồ sơ chuyên môn theo thẩm quyền", "khac", 2, 55),
    ("Xây dựng kế hoạch công tác quý", "ke_hoach", 2, 60),
    ("Tham mưu văn bản chỉ đạo hệ lực lượng", "cong_van", 2, 65),
    # --- Nhóm 3: 70 đến 100 điểm ---
    ("Xây dựng dự thảo Thông tư của Bộ Công an", "thong_tu", 3, 70),
    ("Xây dựng Quy định về công tác nghiệp vụ", "quy_dinh", 3, 80),
    ("Chủ trì xây dựng Đề án trọng điểm", "de_an", 3, 90),
    ("Chủ trì xây dựng Khung Danh mục nhiệm vụ theo KPI", "de_an", 3, 100),
]

# ================= HỒ SƠ KẾT QUẢ THỰC HIỆN =================
# Mỗi profile định hướng mức hoàn thành để tạo ra nhóm xếp loại KPI mong muốn.
# (tỷ lệ hoàn thành, các mức chất lượng, các mức tiến độ)
PROFILES: Dict[str, Dict[str, Any]] = {
    "xuat_sac": {
        "completion": 1.00,
        "quality": ["excellent", "excellent", "good"],
        "timeline": ["ahead", "ahead", "on_time"],
    },
    "tot": {
        "completion": 1.00,
        "quality": ["good", "good", "fair_1"],
        "timeline": ["on_time", "on_time", "late_1"],
    },
    "kha": {
        "completion": 0.90,
        "quality": ["good", "fair_1"],
        "timeline": ["on_time", "late_1"],
    },
    "trung_binh": {   # hướng tới nhóm 2 (50 – dưới 70)
        "completion": 0.85,
        "quality": ["fair_1", "fair_2_4"],
        "timeline": ["late_1", "late_2"],
    },
    "yeu": {          # hướng tới nhóm 3 (dưới 50)
        "completion": 0.65,
        "quality": ["fair_2_4", "poor_5_6"],
        "timeline": ["late_2", "late_3"],
    },
    "khong_dat": {    # nhóm 3, sát đáy
        "completion": 0.40,
        "quality": ["poor_5_6", "fail_7"],
        "timeline": ["late_3", "fail_4"],
    },
}

ALL_QUALITY_TIERS = ["excellent", "good", "fair_1", "fair_2_4", "poor_5_6", "fail_7"]
ALL_TIMELINE_TIERS = ["ahead", "on_time", "late_1", "late_2", "late_3", "fail_4"]

# Số lần sửa / nhắc nhở tương ứng từng mức, dùng để dữ liệu nhiệm vụ khớp với mức đã chấm
REVISIONS_FOR_TIER = {"excellent": 0, "good": 0, "fair_1": 1, "fair_2_4": 3, "poor_5_6": 5, "fail_7": 7}
REMINDERS_FOR_TIER = {"ahead": 0, "on_time": 0, "late_1": 1, "late_2": 2, "late_3": 3, "fail_4": 4}


def _build_task_scores(
    catalog_items: List[dict],
    profile: str,
    rng: random.Random,
    force_quality: Optional[List[str]] = None,
    force_timeline: Optional[List[str]] = None,
) -> List[dict]:
    """
    Tạo danh sách chấm điểm từng nhiệm vụ. Mỗi phần tử đã có sẵn
    quality_score / timeline_score để dữ liệu tự nhất quán.
    """
    spec = PROFILES[profile]
    n = len(catalog_items)
    completed_count = max(1, round(n * spec["completion"])) if n else 0

    scores = []
    for idx, item in enumerate(catalog_items):
        is_completed = idx < completed_count
        point = item["kpi_point"]

        if not is_completed:
            # Chưa hoàn thành thì không tính điểm chất lượng, tiến độ
            q_tier, t_tier = "fail_7", "fail_4"
        elif force_quality and idx < len(force_quality):
            q_tier = force_quality[idx]
            t_tier = force_timeline[idx] if force_timeline and idx < len(force_timeline) else rng.choice(spec["timeline"])
        else:
            q_tier = rng.choice(spec["quality"])
            t_tier = rng.choice(spec["timeline"])

        q_pct = get_quality_percent(q_tier)
        t_pct = get_timeline_percent(t_tier)

        scores.append({
            "task_id": f"seed_{item['id']}",
            "catalog_item_id": item["id"],
            "task_name": item["task_name"],
            "kpi_point": point,
            "is_completed": is_completed,
            "quality_tier": q_tier,
            "timeline_tier": t_tier,
            "quality_percent": q_pct,
            "quality_score": round(point * q_pct, 2),
            "timeline_percent": t_pct,
            "timeline_score": round(point * t_pct, 2),
            "note": None,
        })
    return scores


def _compute_scores(task_scores: List[dict]) -> Dict[str, float]:
    """Tính A, B, C từ task_scores bằng chính hàm nghiệp vụ đang dùng thật."""
    total_assigned = sum(t["kpi_point"] for t in task_scores)
    return {
        "total_assigned_points": total_assigned,
        "score_A": round(calculate_score_A(task_scores, total_assigned), 4),
        "score_B": round(calculate_score_B(task_scores, total_assigned), 4),
        "score_C": round(calculate_score_C(task_scores, total_assigned), 4),
    }


def _build_general_criteria(
    criteria_type: str, kpi_score: float, rng: random.Random, fail_count: int = 0
) -> Dict[str, Any]:
    """Chấm điểm E theo bộ tiêu chí chung; fail_count tiêu chí bị 'không đảm bảo'."""
    leaves = flatten_criteria(criteria_type)
    fail_ids = set(rng.sample([l["id"] for l in leaves], k=min(fail_count, len(leaves))))

    scores = []
    for leaf in leaves:
        ok = leaf["id"] not in fail_ids
        scores.append({
            "criteria_id": leaf["id"],
            "criteria_name": leaf["name"],
            "max_score": leaf["max_score"],
            "rating": "dam_bao" if ok else "khong_dam_bao",
            "actual_score": leaf["max_score"] if ok else 0,
            "note": None if ok else "Cần khắc phục trong kỳ tiếp theo",
        })

    total_e = sum(s["actual_score"] for s in scores)
    return {
        "criteria_type": criteria_type,
        "scores": scores,
        "total_E": total_e,
        "total_kpi_weighted": round(kpi_score * 0.7, 2),
        "total_final_score": round(total_e + kpi_score * 0.7, 2),
        "scored_at": datetime.utcnow(),
    }


def _make_evaluation(
    *,
    evaluation_type: str,
    target_id: str,
    target_name: str,
    target_role: Optional[str],
    department_id: str,
    period_month: Optional[int],
    period_year: int,
    period_type: str,
    status: str,
    task_scores: List[dict],
    score_D: Optional[float] = None,
    kpi_cap: Optional[float] = None,
    rng: random.Random,
    reviewer_id: Optional[str] = None,
    approver_id: Optional[str] = None,
    now: datetime,
    criteria_fail_count: int = 0,
) -> Dict[str, Any]:
    """Dựng 1 bản ghi đánh giá ở đúng trạng thái quy trình yêu cầu."""
    computed = _compute_scores(task_scores)
    is_commander = target_role in ("leader", "director")

    kpi = calculate_kpi(
        computed["score_A"], computed["score_B"], computed["score_C"],
        score_D, is_leader=is_commander and score_D is not None,
    )
    # KPI của người đứng đầu không cao hơn KPI của tập thể do mình đứng đầu
    capped = False
    if kpi_cap is not None and kpi > kpi_cap:
        kpi, capped = kpi_cap, True
    kpi = round(kpi, 2)

    doc: Dict[str, Any] = {
        "evaluation_type": evaluation_type,
        "target_id": target_id,
        "target_name": target_name,
        "target_role": target_role,
        "department_id": department_id,
        "period_type": period_type,
        "period_month": period_month,
        "period_year": period_year,
        "overall_status": status,
        "created_at": now - timedelta(days=20),
        "updated_at": now - timedelta(days=1),
    }

    if status == "draft":
        return doc  # Chưa tự đánh giá — chờ Bước 1

    # Bước 1: tự đánh giá
    doc["self_evaluation"] = {
        "status": "submitted",
        "submitted_at": now - timedelta(days=12),
        "task_scores": task_scores,
        "proposed_rating": determine_kpi_group(kpi),
    }
    if status == "self_evaluating":
        return doc

    if status == "rejected":
        doc["review"] = {
            "status": "rejected",
            "reviewed_by": reviewer_id,
            "reviewed_at": now - timedelta(days=8),
            "task_scores": task_scores,
            "review_note": "Số liệu tự đánh giá chưa khớp hồ sơ, đề nghị báo cáo lại.",
        }
        return doc

    # Bước 2: cơ quan liên quan thẩm định
    doc["review"] = {
        "status": "reviewed",
        "reviewed_by": reviewer_id,
        "reviewed_at": now - timedelta(days=8),
        "task_scores": task_scores,
        "review_note": rng.choice([
            "Nhất trí với kết quả tự đánh giá của đồng chí.",
            "Đã đối chiếu Danh mục nhiệm vụ công tác, số liệu phù hợp.",
            "Đề nghị tiếp tục phát huy, khắc phục hạn chế về tiến độ.",
        ]),
    }
    if status == "reviewing":
        return doc

    # Bước 3: cấp có thẩm quyền xác định điểm KPI
    doc["approval"] = {
        "status": "approved",
        "approved_by": approver_id,
        "approved_at": now - timedelta(days=2),
        **computed,
        "score_D": round(score_D, 4) if score_D is not None else None,
        "kpi_score": kpi,
        "kpi_group": determine_kpi_group(kpi),
        "capped_by_collective": capped,
    }
    doc["general_criteria"] = _build_general_criteria(
        criteria_type_for(evaluation_type, target_role), kpi, rng, criteria_fail_count
    )
    return doc


# ================= HÀM CHÍNH =================

async def seed_kpi_data(
    *,
    dept_ids: List[Any],
    dept_names: List[str],
    admin_id: str,
    director_ids: List[Any],
    now: Optional[datetime] = None,
    months_back: int = 6,
    seed: int = 20260608,
) -> Dict[str, int]:
    """
    Sinh Danh mục nhiệm vụ + toàn bộ kỳ đánh giá KPI.
    Trả về số lượng bản ghi đã tạo theo từng loại.
    """
    rng = random.Random(seed)
    now = now or datetime.utcnow()

    await db.kpi_task_catalog.delete_many({})
    await db.kpi_evaluations.delete_many({})

    # ---------- 1. Danh mục nhiệm vụ công tác ----------
    catalogs_by_dept: Dict[str, List[dict]] = {}
    catalog_docs = []

    for i, dept_id in enumerate(dept_ids):
        items = [
            {
                "id": f"item_{i}_{j}",
                "task_name": name,
                "category": product,
                "complexity_group": group,
                "kpi_point": point,
                "description": f"Sản phẩm đầu ra: {name}.",
            }
            for j, (name, product, group, point) in enumerate(CATALOG_TEMPLATE)
        ]
        catalogs_by_dept[str(dept_id)] = items

        catalog_docs.append({
            "department_id": str(dept_id),
            "period_year": now.year,
            "name": f"Danh mục nhiệm vụ công tác theo KPI năm {now.year} — {dept_names[i]}",
            "status": "approved",
            "items": items,
            "approved_by": str(director_ids[0]) if director_ids else admin_id,
            "approved_at": now - timedelta(days=180),
            "created_by": admin_id,
            "created_at": now - timedelta(days=200),
            "updated_at": now - timedelta(days=180),
        })

    # Một danh mục bản nháp của năm sau để kiểm thử luồng phê duyệt.
    # Cấp id riêng cho từng mục, không dùng lại id của danh mục đã duyệt.
    draft_items = [
        {**item, "id": f"draft_{item['id']}"}
        for item in catalogs_by_dept[str(dept_ids[0])][:8]
    ]
    catalog_docs.append({
        "department_id": str(dept_ids[0]),
        "period_year": now.year + 1,
        "name": f"(Dự thảo) Danh mục nhiệm vụ công tác theo KPI năm {now.year + 1} — {dept_names[0]}",
        "status": "draft",
        "items": draft_items,
        "approved_by": None,
        "approved_at": None,
        "created_by": admin_id,
        "created_at": now - timedelta(days=5),
        "updated_at": now - timedelta(days=5),
    })
    await db.kpi_task_catalog.insert_many(catalog_docs)

    # ---------- 2. Phân hồ sơ kết quả cho từng cán bộ ----------
    users = await db.users.find({"role": {"$ne": "admin"}}).to_list(None)
    # Bảo đảm cả 3 nhóm xếp loại đều xuất hiện: xoay vòng hồ sơ theo thứ tự.
    # Thang này xếp từ tốt nhất đến kém nhất, dùng để dao động theo tháng.
    profile_cycle = ["xuat_sac", "tot", "kha", "trung_binh", "yeu", "khong_dat"]
    user_base_profile = {
        str(u["_id"]): idx % len(profile_cycle)
        for idx, u in enumerate(users)
    }

    def profile_for(uid: str, month: int, year: int) -> str:
        """
        Hồ sơ kết quả của một cán bộ TRONG MỘT THÁNG cụ thể.

        Mỗi người có xu hướng riêng, nhưng tháng nào cũng y hệt nhau là phi thực
        tế — và tai hại: khi kết quả tất định theo người, mô hình cảnh báo sớm
        chỉ học được "ai yếu thì yếu", tức nhắc lại điều lãnh đạo đã biết, chứ
        không rút ra được tín hiệu nào từ tiến độ trong kỳ.
        Vì vậy cho dao động quanh mức nền của từng người.
        """
        base = user_base_profile[uid]
        # Dao động tất định theo (người, kỳ) để chạy lại seeder vẫn ra kết quả cũ
        jitter = random.Random(f"{uid}-{year}-{month}").choice([-2, -1, 0, 0, 0, 1, 1, 2])
        return profile_cycle[max(0, min(len(profile_cycle) - 1, base + jitter))]

    months = []
    for k in range(months_back, 0, -1):
        m = now.month - k
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((m, y))

    evaluations: List[dict] = []
    # KPI tập thể theo (đơn vị, tháng) để làm mức trần cho người đứng đầu
    collective_kpi: Dict[tuple, float] = {}

    dept_director = {}
    for u in users:
        if u.get("role") == "director" and u.get("department_id"):
            dept_director[u["department_id"]] = str(u["_id"])

    # ---------- 3. Các kỳ đã phê duyệt (nhiều tháng) ----------
    for month, year in months:
        # 3a. Tập thể trước, để lấy mức trần cho người đứng đầu
        for i, dept_id in enumerate(dept_ids):
            items = catalogs_by_dept[str(dept_id)]
            profile = ["xuat_sac", "tot", "kha", "trung_binh"][i % 4]
            task_scores = _build_task_scores(items, profile, rng)
            doc = _make_evaluation(
                evaluation_type="collective",
                target_id=str(dept_id),
                target_name=dept_names[i],
                target_role=None,
                department_id=str(dept_id),
                period_month=month, period_year=year, period_type="monthly",
                status="approved",
                task_scores=task_scores,
                rng=rng, now=now,
                reviewer_id=dept_director.get(str(dept_id)),
                approver_id=admin_id,
                criteria_fail_count=rng.choice([0, 0, 1]),
            )
            collective_kpi[(str(dept_id), month, year)] = doc["approval"]["kpi_score"]
            evaluations.append(doc)

        # 3b. Cán bộ không giữ chức vụ lãnh đạo
        staff_results: Dict[str, List[str]] = {}
        for u in users:
            if u.get("role") != "staff":
                continue
            dept_id = u.get("department_id")
            items = catalogs_by_dept.get(dept_id)
            if not items:
                continue
            profile = profile_for(str(u["_id"]), month, year)
            task_scores = _build_task_scores(items, profile, rng)
            doc = _make_evaluation(
                evaluation_type="individual",
                target_id=str(u["_id"]),
                target_name=u["name"],
                target_role="staff",
                department_id=dept_id,
                period_month=month, period_year=year, period_type="monthly",
                status="approved",
                task_scores=task_scores,
                rng=rng, now=now,
                reviewer_id=dept_director.get(dept_id),
                approver_id=dept_director.get(dept_id) or admin_id,
                criteria_fail_count=0 if profile in ("xuat_sac", "tot") else rng.choice([1, 2]),
            )
            evaluations.append(doc)
            staff_results.setdefault(dept_id, []).append(doc["approval"]["kpi_group"])

        # 3c. Lãnh đạo, chỉ huy — điểm D suy ra từ kết quả cán bộ thuộc quyền
        for u in users:
            if u.get("role") not in ("leader", "director"):
                continue
            dept_id = u.get("department_id")
            items = catalogs_by_dept.get(dept_id)
            if not items:
                continue

            groups = staff_results.get(dept_id, [])
            score_D = (
                sum(1 for g in groups if g in ("group_1", "group_2")) / len(groups)
                if groups else 0.0
            )

            profile = profile_for(str(u["_id"]), month, year)
            task_scores = _build_task_scores(items, profile, rng)
            # Chỉ người đứng đầu đơn vị (director) bị chặn trần theo KPI tập thể
            cap = collective_kpi.get((dept_id, month, year)) if u["role"] == "director" else None

            doc = _make_evaluation(
                evaluation_type="individual",
                target_id=str(u["_id"]),
                target_name=u["name"],
                target_role=u["role"],
                department_id=dept_id,
                period_month=month, period_year=year, period_type="monthly",
                status="approved",
                task_scores=task_scores,
                score_D=score_D,
                kpi_cap=cap,
                rng=rng, now=now,
                reviewer_id=admin_id,
                approver_id=admin_id,
                criteria_fail_count=0 if profile in ("xuat_sac", "tot") else 1,
            )
            evaluations.append(doc)

    # ---------- 4. Kỳ hiện tại: phủ đủ 5 trạng thái quy trình ----------
    cur_m, cur_y = now.month, now.year
    statuses = ["draft", "self_evaluating", "reviewing", "approved", "rejected"]

    for i, dept_id in enumerate(dept_ids):
        items = catalogs_by_dept[str(dept_id)]
        # Tập thể kỳ hiện tại — đã duyệt để làm trần và để chấm tiêu chí chung
        task_scores = _build_task_scores(items, "tot", rng)
        doc = _make_evaluation(
            evaluation_type="collective",
            target_id=str(dept_id), target_name=dept_names[i], target_role=None,
            department_id=str(dept_id),
            period_month=cur_m, period_year=cur_y, period_type="monthly",
            status="approved", task_scores=task_scores,
            rng=rng, now=now,
            reviewer_id=dept_director.get(str(dept_id)), approver_id=admin_id,
        )
        collective_kpi[(str(dept_id), cur_m, cur_y)] = doc["approval"]["kpi_score"]
        evaluations.append(doc)

    dept_staff_groups: Dict[str, List[str]] = {}
    for idx, u in enumerate(users):
        dept_id = u.get("department_id")
        items = catalogs_by_dept.get(dept_id)
        if not items:
            continue

        status = statuses[idx % len(statuses)]
        profile = profile_for(str(u["_id"]), cur_m, cur_y)
        task_scores = _build_task_scores(items, profile, rng)

        is_commander = u.get("role") in ("leader", "director")
        score_D = None
        if is_commander:
            groups = dept_staff_groups.get(dept_id, [])
            score_D = (
                sum(1 for g in groups if g in ("group_1", "group_2")) / len(groups)
                if groups else 0.75
            )

        doc = _make_evaluation(
            evaluation_type="individual",
            target_id=str(u["_id"]), target_name=u["name"], target_role=u.get("role"),
            department_id=dept_id,
            period_month=cur_m, period_year=cur_y, period_type="monthly",
            status=status, task_scores=task_scores,
            score_D=score_D,
            kpi_cap=collective_kpi.get((dept_id, cur_m, cur_y)) if u.get("role") == "director" else None,
            rng=rng, now=now,
            reviewer_id=dept_director.get(dept_id) or admin_id,
            approver_id=dept_director.get(dept_id) or admin_id,
            criteria_fail_count=0 if profile in ("xuat_sac", "tot") else 1,
        )
        evaluations.append(doc)
        if status == "approved" and u.get("role") == "staff":
            dept_staff_groups.setdefault(dept_id, []).append(doc["approval"]["kpi_group"])

    # ---------- 5. Kỳ trưng bày: phủ trọn 6 mức chất lượng và 6 mức tiến độ ----------
    showcase_user = next((u for u in users if u.get("role") == "staff"), None)
    if showcase_user:
        dept_id = showcase_user.get("department_id")
        items = catalogs_by_dept.get(dept_id, catalogs_by_dept[str(dept_ids[0])])[:6]
        task_scores = _build_task_scores(
            items, "tot", rng,
            force_quality=ALL_QUALITY_TIERS,
            force_timeline=ALL_TIMELINE_TIERS,
        )
        # Ép toàn bộ là đã hoàn thành để mọi mức đều được tính vào B và C
        for ts in task_scores:
            ts["is_completed"] = True
        evaluations.append(_make_evaluation(
            evaluation_type="individual",
            target_id=str(showcase_user["_id"]),
            target_name=showcase_user["name"],
            target_role="staff",
            department_id=dept_id,
            period_month=None, period_year=now.year, period_type="yearly",
            status="approved", task_scores=task_scores,
            rng=rng, now=now,
            reviewer_id=admin_id, approver_id=admin_id,
        ))

    await db.kpi_evaluations.insert_many(evaluations)

    return {
        "catalogs": len(catalog_docs),
        "evaluations": len(evaluations),
        "months": len(months) + 1,
        "users": len(users),
        # Trả hàm này ra để phần sinh nhiệm vụ dùng CÙNG hồ sơ kết quả.
        # Nếu nhiệm vụ và kỳ đánh giá mô tả hai mức năng lực khác nhau thì dữ
        # liệu mâu thuẫn, và mô hình cảnh báo sớm không học được gì từ tiến độ.
        "profile_for": profile_for,
    }
