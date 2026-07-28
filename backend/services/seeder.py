"""
Sinh dữ liệu mẫu cho Hệ thống tính điểm KPI trong Công an nhân dân.

Chạy trực tiếp:  python -m backend.services.seeder
"""
import asyncio
import random
from datetime import datetime, timedelta

from backend.database import db
from backend.security import get_password_hash
from backend.services.kpi_seeder import seed_kpi_data, CATALOG_TEMPLATE

SEED = 20260608

# Đơn vị theo hệ lực lượng
DEPARTMENTS = [
    ("Văn phòng Bộ Công an", "Tham mưu tổng hợp; chủ trì xây dựng Khung Danh mục nhiệm vụ công tác theo KPI", "Tham mưu"),
    ("Cục Tổ chức cán bộ", "Công tác tổ chức, cán bộ; theo dõi, chấm điểm KPI đối với cá nhân lãnh đạo, chỉ huy", "Tổ chức cán bộ"),
    ("Cục Pháp chế và cải cách hành chính, tư pháp", "Xây dựng văn bản quy phạm pháp luật; cải cách hành chính", "Pháp chế"),
    ("Phòng Cảnh sát điều tra tội phạm về trật tự xã hội", "Đấu tranh phòng, chống tội phạm về trật tự xã hội", "Cảnh sát hình sự"),
    ("Phòng An ninh chính trị nội bộ", "Bảo vệ an ninh chính trị nội bộ", "An ninh"),
]

RANKS_LEADERSHIP = ["Đại tá", "Thượng tá", "Trung tá"]
RANKS_STAFF = ["Thiếu tá", "Đại úy", "Thượng úy", "Trung úy", "Thiếu úy"]

HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
DEM = ["Văn", "Thị", "Hữu", "Minh", "Xuân", "Thu", "Hải", "Ngọc", "Đức", "Công", "Đình", "Quốc", "Thanh", "Bích", "Phương", "Gia"]
TEN = ["Hùng", "Hương", "Anh", "Tuấn", "Linh", "Cường", "Trang", "Khoa", "Nga", "Long", "Bình", "Châu", "Duy", "Phúc", "Khang", "Tâm", "Mai", "Quỳnh", "Thảo", "Sơn"]

DIRECTORS = [
    ("Trần Minh Đức", "director_vp"),
    ("Lê Thị Hương", "director_tccb"),
    ("Phạm Văn Tuấn", "director_pc"),
    ("Hoàng Thị Nga", "director_csdt"),
    ("Ngô Quốc Hùng", "director_anctnb"),
]

# Mức chất lượng / tiến độ ↔ số lần sửa, số lần nhắc nhở (khớp Hướng dẫn)
REVISION_CHOICES = [0, 0, 0, 1, 1, 3, 5, 7]
REMINDER_CHOICES = [0, 0, 0, 1, 1, 2, 3, 4]


async def run_seed():
    rng = random.Random(SEED)
    now = datetime.utcnow()
    print("Đang sinh dữ liệu mẫu...")

    for coll in (
        db.users, db.departments, db.tasks, db.comments,
        db.notifications, db.audit_logs,
        db.kpi_task_catalog, db.kpi_evaluations,
    ):
        await coll.delete_many({})

    # ---------- 1. Đơn vị ----------
    dept_docs = [
        {"name": name, "description": desc, "force_system": force, "parent_id": None}
        for name, desc, force in DEPARTMENTS
    ]
    res_depts = await db.departments.insert_many(dept_docs)
    dept_ids = res_depts.inserted_ids
    dept_names = [d[0] for d in DEPARTMENTS]

    # ---------- 2. Quản trị hệ thống ----------
    admin_res = await db.users.insert_one({
        "username": "admin",
        "name": "Quản trị viên hệ thống",
        "email": "admin@bocongan.gov.vn",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
        "department_id": str(dept_ids[0]),
        "position": "Quản trị hệ thống",
        "rank": "Thượng tá",
        "bio": "Quản trị hệ thống tính điểm KPI. Toàn quyền quản lý dữ liệu.",
        "is_admin": True,
        "is_commander": False,
    })
    admin_id = str(admin_res.inserted_id)

    # ---------- 3. Lãnh đạo đơn vị (người đứng đầu) ----------
    director_ids = []
    for i, (name, username) in enumerate(DIRECTORS):
        r = await db.users.insert_one({
            "username": username,
            "name": name,
            "email": f"{username}@bocongan.gov.vn",
            "hashed_password": get_password_hash("123456"),
            "role": "director",
            "department_id": str(dept_ids[i]),
            "position": "Trưởng đơn vị",
            "rank": RANKS_LEADERSHIP[i % len(RANKS_LEADERSHIP)],
            "bio": f"Người đứng đầu {dept_names[i]}. KPI không cao hơn KPI của tập thể đơn vị.",
            "is_admin": False,
            "is_commander": True,
        })
        director_ids.append(r.inserted_id)

    # ---------- 4. Lãnh đạo, chỉ huy cấp Phòng/Đội (2 mỗi đơn vị) ----------
    leader_ids = []
    counter = 0
    for i in range(len(dept_ids)):
        for j in range(2):
            counter += 1
            r = await db.users.insert_one({
                "username": f"leader{counter}",
                "name": f"{rng.choice(HO)} {rng.choice(DEM)} {rng.choice(TEN)}",
                "email": f"leader{counter}@bocongan.gov.vn",
                "hashed_password": get_password_hash("123456"),
                "role": "leader",
                "department_id": str(dept_ids[i]),
                "position": "Phó Trưởng đơn vị" if j == 0 else "Đội trưởng",
                "rank": RANKS_LEADERSHIP[counter % len(RANKS_LEADERSHIP)],
                "bio": f"Lãnh đạo, chỉ huy thuộc {dept_names[i]}. KPI tính theo 04 tiêu chí.",
                "is_admin": False,
                "is_commander": True,
            })
            leader_ids.append(r.inserted_id)

    # ---------- 5. Cán bộ, chiến sĩ (6 mỗi đơn vị = 30) ----------
    staff_ids = []
    idx = 0
    for i in range(len(dept_ids)):
        for _ in range(6):
            r = await db.users.insert_one({
                "username": f"canbo{idx}",
                "name": f"{rng.choice(HO)} {rng.choice(DEM)} {rng.choice(TEN)}",
                "email": f"canbo{idx}@bocongan.gov.vn",
                "hashed_password": get_password_hash("123456"),
                "role": "staff",
                "department_id": str(dept_ids[i]),
                "position": rng.choice(["Chuyên viên chính", "Chuyên viên", "Cán bộ"]),
                "rank": RANKS_STAFF[idx % len(RANKS_STAFF)],
                "bio": "Cán bộ thực hiện nhiệm vụ công tác theo Danh mục được giao.",
                "is_admin": False,
                "is_commander": False,
            })
            staff_ids.append(r.inserted_id)
            idx += 1

    print(f"  Đơn vị: {len(dept_ids)} · Cán bộ: {1 + len(director_ids) + len(leader_ids) + len(staff_ids)}")

    # ---------- 6. Danh mục nhiệm vụ + toàn bộ kỳ đánh giá KPI ----------
    kpi_stats = await seed_kpi_data(
        dept_ids=dept_ids,
        dept_names=dept_names,
        admin_id=admin_id,
        director_ids=director_ids,
        now=now,
        months_back=6,
        seed=SEED,
    )
    print(f"  Danh mục KPI: {kpi_stats['catalogs']} · Kỳ đánh giá: {kpi_stats['evaluations']}")

    # ---------- 7. Nhiệm vụ công tác của kỳ hiện tại ----------
    catalogs = await db.kpi_task_catalog.find({"status": "approved"}).to_list(None)
    items_by_dept = {c["department_id"]: c["items"] for c in catalogs}

    all_users = await db.users.find({"role": {"$ne": "admin"}}).to_list(None)
    task_docs = []
    for u in all_users:
        dept_id = u.get("department_id")
        items = items_by_dept.get(dept_id)
        if not items:
            continue

        for item in rng.sample(items, k=rng.randint(4, 7)):
            status = rng.choice(["assigned", "in_progress", "review", "done", "done"])
            qty_assigned = rng.randint(1, 3)
            qty_completed = qty_assigned if status == "done" else rng.randint(0, qty_assigned - 1) if qty_assigned > 1 else 0

            revisions = rng.choice(REVISION_CHOICES) if status in ("review", "done") else 0
            reminders = rng.choice(REMINDER_CHOICES)

            deadline = now + timedelta(days=rng.randint(-12, 20))
            task_docs.append({
                "title": item["task_name"],
                "description": item.get("description"),
                "catalog_item_id": item["id"],
                "product": item["category"],
                "kpi_point": item["kpi_point"],
                "quantity_assigned": qty_assigned,
                "quantity_completed": qty_completed,
                "assigned_to": str(u["_id"]),
                "department_id": dept_id,
                "status": status,
                "deadline": deadline,
                "actual_end": (deadline - timedelta(days=rng.randint(0, 4))) if status == "done" else None,
                "revision_count": revisions,
                "reminder_count": reminders,
                "period_month": now.month,
                "period_year": now.year,
                "attachments": [],
            })

    res_tasks = await db.tasks.insert_many(task_docs)
    task_ids = res_tasks.inserted_ids
    print(f"  Nhiệm vụ công tác: {len(task_docs)}")

    # ---------- 8. Ý kiến trao đổi ----------
    user_map = {str(u["_id"]): u["name"] for u in all_users}
    user_map[admin_id] = "Quản trị viên hệ thống"
    reviewer_pool = [str(x) for x in (director_ids + leader_ids)]

    comment_texts = [
        "Đề nghị đồng chí bổ sung căn cứ pháp lý trong dự thảo.",
        "Sản phẩm đã đảm bảo yêu cầu, đề nghị trình lãnh đạo phê duyệt.",
        "Cần đẩy nhanh tiến độ, đã sát thời hạn theo kế hoạch.",
        "Nội dung còn thiếu sót, đề nghị hoàn thiện và trình lại.",
        "Đã đối chiếu với Danh mục nhiệm vụ công tác, số liệu phù hợp.",
        "Nhất trí với đề xuất; đề nghị phối hợp với đơn vị liên quan.",
    ]
    comments = []
    for i, t in enumerate(task_docs):
        if rng.random() < 0.35:
            for _ in range(rng.randint(1, 3)):
                uid = rng.choice(reviewer_pool)
                comments.append({
                    "task_id": str(task_ids[i]),
                    "user_id": uid,
                    "user_name": user_map.get(uid, "Cán bộ"),
                    "content": rng.choice(comment_texts),
                    "created_at": now - timedelta(hours=rng.randint(1, 300)),
                })
    if comments:
        await db.comments.insert_many(comments)
    print(f"  Ý kiến trao đổi: {len(comments)}")

    # ---------- 9. Thông báo ----------
    notifications = []
    for u in all_users[:20]:
        notifications.append({
            "user_id": str(u["_id"]),
            "type": "kpi_self_eval_required",
            "title": "Đến kỳ tự đánh giá KPI",
            "message": f"Đề nghị đồng chí thực hiện tự đánh giá và đề xuất mức xếp loại tháng {now.month}/{now.year}.",
            "reference_id": None,
            "reference_type": "kpi_evaluation",
            "is_read": rng.random() < 0.4,
            "created_at": now - timedelta(days=rng.randint(0, 6)),
        })
    await db.notifications.insert_many(notifications)
    print(f"  Thông báo: {len(notifications)}")

    print("\nHoàn tất. Tài khoản mẫu:")
    print("  admin / admin123          — Quản trị hệ thống")
    print("  director_vp / 123456      — Lãnh đạo Văn phòng Bộ Công an")
    print("  leader1 / 123456          — Lãnh đạo, chỉ huy")
    print("  canbo0 / 123456           — Cán bộ, chiến sĩ")


if __name__ == "__main__":
    asyncio.run(run_seed())
