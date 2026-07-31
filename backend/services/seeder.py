"""
Sinh dữ liệu mẫu cho Hệ thống tính điểm KPI trong Công an nhân dân.

Chạy trực tiếp:  python -m backend.services.seeder
"""
import asyncio
import random
from datetime import datetime, timedelta

from backend.database import db
from backend.security import get_password_hash
from backend.models.security_policy import CLASSIFICATION_RANK
from backend.services.kpi_seeder import seed_kpi_data

SEED = 20260608

# Cây cơ cấu tổ chức 3 cấp: Bộ → Cục / Công an tỉnh → Phòng
# (tên, tên viết tắt, mô tả, hệ lực lượng, cấp, khoá đơn vị cha)
ORG_TREE = [
    ("Bộ Công an", "BCA",
     "Cơ quan Bộ", "Cơ quan Bộ", "bo", None),

    ("Văn phòng Bộ Công an", "VPB",
     "Tham mưu tổng hợp; chủ trì xây dựng Khung Danh mục nhiệm vụ công tác theo KPI",
     "Tham mưu", "cuc", "Bộ Công an"),
    ("Cục Tổ chức cán bộ", "X01",
     "Công tác tổ chức, cán bộ; tham mưu chấm điểm KPI đối với lãnh đạo, chỉ huy",
     "Tổ chức cán bộ", "cuc", "Bộ Công an"),
    ("Cục Pháp chế và cải cách hành chính, tư pháp", "V03",
     "Xây dựng văn bản quy phạm pháp luật; cải cách hành chính, tư pháp",
     "Pháp chế", "cuc", "Bộ Công an"),
    ("Công an tỉnh Đắk Lắk", "CADL",
     "Công an cấp tỉnh", "Công an địa phương", "cuc", "Bộ Công an"),

    # Cấp Phòng — nơi bố trí cán bộ và chấm điểm KPI
    ("Phòng Tham mưu tổng hợp", "VPB-P1",
     "Tổng hợp, theo dõi, kiểm đếm công việc toàn lực lượng",
     "Tham mưu", "phong", "Văn phòng Bộ Công an"),
    ("Phòng Thư ký - Biên tập", "VPB-P2",
     "Thư ký lãnh đạo Bộ; biên tập văn bản",
     "Tham mưu", "phong", "Văn phòng Bộ Công an"),
    ("Phòng Chính sách cán bộ", "X01-P1",
     "Chính sách, chế độ đối với cán bộ, chiến sĩ",
     "Tổ chức cán bộ", "phong", "Cục Tổ chức cán bộ"),
    ("Phòng Đào tạo, bồi dưỡng", "X01-P2",
     "Đào tạo, bồi dưỡng nâng cao trình độ cán bộ",
     "Tổ chức cán bộ", "phong", "Cục Tổ chức cán bộ"),
    ("Phòng Xây dựng pháp luật", "V03-P1",
     "Chủ trì xây dựng dự thảo văn bản quy phạm pháp luật",
     "Pháp chế", "phong", "Cục Pháp chế và cải cách hành chính, tư pháp"),
    ("Phòng Cảnh sát điều tra tội phạm về trật tự xã hội", "CADL-PC02",
     "Đấu tranh phòng, chống tội phạm về trật tự xã hội",
     "Cảnh sát hình sự", "phong", "Công an tỉnh Đắk Lắk"),
    ("Phòng An ninh chính trị nội bộ", "CADL-PA03",
     "Bảo vệ an ninh chính trị nội bộ",
     "An ninh", "phong", "Công an tỉnh Đắk Lắk"),
]

RANKS_LEADERSHIP = ["Đại tá", "Thượng tá", "Trung tá"]
RANKS_STAFF = ["Thiếu tá", "Đại úy", "Thượng úy", "Trung úy", "Thiếu úy"]

HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
DEM = ["Văn", "Thị", "Hữu", "Minh", "Xuân", "Thu", "Hải", "Ngọc", "Đức", "Công", "Đình", "Quốc", "Thanh", "Bích", "Phương", "Gia"]
TEN = ["Hùng", "Hương", "Anh", "Tuấn", "Linh", "Cường", "Trang", "Khoa", "Nga", "Long", "Bình", "Châu", "Duy", "Phúc", "Khang", "Tâm", "Mai", "Quỳnh", "Thảo", "Sơn"]

DIRECTOR_NAMES = [
    ("Trần Minh Đức", "director_tmth"),
    ("Lê Thị Hương", "director_tkbt"),
    ("Phạm Văn Tuấn", "director_cscb"),
    ("Hoàng Thị Nga", "director_dtbd"),
    ("Ngô Quốc Hùng", "director_xdpl"),
    ("Vũ Đình Khang", "director_pc02"),
    ("Đặng Thu Trang", "director_pa03"),
]

# Mức chất lượng / tiến độ ↔ số lần sửa, số lần nhắc nhở (khớp Hướng dẫn)
REVISION_CHOICES = [0, 0, 0, 1, 1, 3, 5, 7]
REMINDER_CHOICES = [0, 0, 0, 1, 1, 2, 3, 4]

# Loại nhiệm vụ và độ mật
TASK_TYPES = ["thuong_xuyen", "thuong_xuyen", "thuong_xuyen", "dot_xuat", "chuyen_de", "phoi_hop"]
# Phần lớn là nhiệm vụ thường; nhiệm vụ có độ mật là thiểu số, đúng thực tế
CLASSIFICATIONS = ["thuong"] * 12 + ["mat"] * 4 + ["toi_mat"] * 2 + ["tuyet_mat"]

CLASSIFIED_CODENAMES = [
    "Nhiệm vụ chuyên đề A1", "Nhiệm vụ chuyên đề A2", "Nhiệm vụ chuyên đề B1",
    "Chuyên án K3", "Chuyên án M7", "Kế hoạch nghiệp vụ số 4",
    "Rà soát địa bàn trọng điểm", "Xác minh theo yêu cầu nghiệp vụ",
]

ASSIGN_BASIS = [
    "Kế hoạch công tác năm 2026 của đơn vị",
    "Chương trình công tác trọng tâm quý",
    "Công văn số 1245/BCA-V01 ngày 12/5/2026",
    "Chỉ đạo trực tiếp của lãnh đạo đơn vị",
    "Kế hoạch số 12/KH-BCA ngày 03/4/2026",
]


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

    # ---------- 1. Cây cơ cấu tổ chức ----------
    # Chèn theo thứ tự cha trước con để gán được parent_id
    id_by_name: dict = {}
    for name, short, desc, force, level, parent in ORG_TREE:
        res = await db.departments.insert_one({
            "name": name,
            "short_name": short,
            "description": desc,
            "force_system": force,
            "level": level,
            "parent_id": str(id_by_name[parent]) if parent else None,
        })
        id_by_name[name] = res.inserted_id

    # Cán bộ và KPI chỉ bố trí ở cấp Phòng (đơn vị cơ sở trực tiếp thực hiện)
    unit_names = [t[0] for t in ORG_TREE if t[4] == "phong"]
    unit_ids = [id_by_name[n] for n in unit_names]
    dept_ids, dept_names = unit_ids, unit_names

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
        "service_number": "CAND-000001",
        "clearance_level": 3,
        "capacity_points": 200,
        "bio": "Quản trị hệ thống tính điểm KPI. Toàn quyền quản lý dữ liệu.",
        "is_admin": True,
        "is_commander": False,
    })
    admin_id = str(admin_res.inserted_id)

    # ---------- 3. Lãnh đạo đơn vị (người đứng đầu) ----------
    director_ids = []
    for i, (name, username) in enumerate(DIRECTOR_NAMES[:len(dept_ids)]):
        r = await db.users.insert_one({
            "username": username,
            "name": name,
            "email": f"{username}@bocongan.gov.vn",
            "hashed_password": get_password_hash("123456"),
            "role": "director",
            "department_id": str(dept_ids[i]),
            "position": "Trưởng phòng",
            "rank": RANKS_LEADERSHIP[i % len(RANKS_LEADERSHIP)],
            "service_number": f"CAND-{100 + i:06d}",
            # Người đứng đầu được tiếp cận tới Tuyệt mật
            "clearance_level": 3,
            "capacity_points": 1200,
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
                "position": "Phó Trưởng phòng" if j == 0 else "Đội trưởng",
                "rank": RANKS_LEADERSHIP[counter % len(RANKS_LEADERSHIP)],
                "service_number": f"CAND-{200 + counter:06d}",
                # Lãnh đạo, chỉ huy cấp Phòng/Đội: tiếp cận tới Tối mật
                "clearance_level": 2,
                "capacity_points": 950,
                "bio": f"Lãnh đạo, chỉ huy thuộc {dept_names[i]}. KPI tính theo 04 tiêu chí.",
                "is_admin": False,
                "is_commander": True,
            })
            leader_ids.append(r.inserted_id)

    # ---------- 5. Cán bộ, chiến sĩ (6 mỗi đơn vị) ----------
    # Cấp độ tiếp cận khác nhau để kiểm chứng cơ chế che thông tin
    staff_ids = []
    idx = 0
    for i in range(len(dept_ids)):
        for j in range(6):
            clearance = [0, 0, 0, 1, 1, 2][j]
            r = await db.users.insert_one({
                "username": f"canbo{idx}",
                "name": f"{rng.choice(HO)} {rng.choice(DEM)} {rng.choice(TEN)}",
                "email": f"canbo{idx}@bocongan.gov.vn",
                "hashed_password": get_password_hash("123456"),
                "role": "staff",
                "department_id": str(dept_ids[i]),
                "position": rng.choice(["Chuyên viên chính", "Chuyên viên", "Cán bộ"]),
                "rank": RANKS_STAFF[idx % len(RANKS_STAFF)],
                "service_number": f"CAND-{1000 + idx:06d}",
                "clearance_level": clearance,
                # Định mức điểm mỗi kỳ — đặt tương xứng khối lượng nhiệm vụ được giao
                "capacity_points": rng.choice([450, 550, 550, 650, 750]),
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

    # Người giao nhiệm vụ của từng đơn vị là trưởng phòng
    head_of_dept = {
        u["department_id"]: str(u["_id"])
        for u in all_users if u.get("role") == "director" and u.get("department_id")
    }
    # Đồng nghiệp cùng đơn vị, để chọn cán bộ phối hợp
    peers_by_dept: dict = {}
    for u in all_users:
        if u.get("department_id"):
            peers_by_dept.setdefault(u["department_id"], []).append(str(u["_id"]))

    task_docs = []
    seq = 0
    for u in all_users:
        dept_id = u.get("department_id")
        items = items_by_dept.get(dept_id)
        if not items:
            continue

        for item in rng.sample(items, k=rng.randint(4, 7)):
            seq += 1
            status = rng.choice(["assigned", "in_progress", "review", "done", "done"])
            qty_assigned = rng.randint(1, 3)
            qty_completed = qty_assigned if status == "done" else (
                rng.randint(0, qty_assigned - 1) if qty_assigned > 1 else 0
            )

            revisions = rng.choice(REVISION_CHOICES) if status in ("review", "done") else 0
            reminders = rng.choice(REMINDER_CHOICES)

            # Độ mật — chỉ giao nhiệm vụ mật cho cán bộ đủ cấp độ tiếp cận
            classification = rng.choice(CLASSIFICATIONS)
            if CLASSIFICATION_RANK[classification] > int(u.get("clearance_level", 0) or 0):
                classification = "thuong"
            is_classified = classification != "thuong"

            # Cán bộ phối hợp
            peers = [p for p in peers_by_dept.get(dept_id, []) if p != str(u["_id"])]
            co = rng.sample(peers, k=rng.randint(0, 2)) if peers else []

            deadline = now + timedelta(days=rng.randint(-12, 20))
            task_docs.append({
                "code": f"NV-{now.year}-{now.month:02d}-{seq:04d}",
                # Nhiệm vụ có độ mật chỉ mang tên gọi quy ước, không phải nội dung thật
                "title": rng.choice(CLASSIFIED_CODENAMES) if is_classified else item["task_name"],
                # Không lưu nội dung với nhiệm vụ có độ mật
                "description": None if is_classified else item.get("description"),
                "task_type": rng.choice(TASK_TYPES),
                "classification": classification,
                "file_reference": f"Số {rng.randint(100, 499)}/HS-{rng.choice(['PA03','PC02','V03','X01'])}" if is_classified else None,
                "file_location": "Bộ phận cơ yếu đơn vị" if is_classified else None,
                "catalog_item_id": item["id"],
                "complexity_group": item["complexity_group"],
                "product": item["category"],
                "kpi_point": item["kpi_point"],
                "quantity_assigned": qty_assigned,
                "quantity_completed": qty_completed,
                "assigned_to": str(u["_id"]),
                "co_assignees": co,
                "assigned_by": head_of_dept.get(dept_id, admin_id),
                "assigned_at": now - timedelta(days=rng.randint(5, 25)),
                "assigned_basis": rng.choice(ASSIGN_BASIS),
                "department_id": dept_id,
                "support_department_ids": [],
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

    classified = sum(1 for t in task_docs if t["classification"] != "thuong")
    print(f"  Trong đó có độ mật: {classified} nhiệm vụ")

    print("\nHoàn tất. Tài khoản mẫu:")
    print("  admin      / admin123  — Quản trị hệ thống (tiếp cận Tuyệt mật)")
    print("  director_tmth / 123456 — Trưởng phòng (tiếp cận Tuyệt mật)")
    print("  leader1    / 123456    — Lãnh đạo, chỉ huy (tiếp cận Tối mật)")
    print("  canbo5     / 123456    — Cán bộ (tiếp cận Tối mật)")
    print("  canbo0     / 123456    — Cán bộ (chỉ tài liệu thường)")


if __name__ == "__main__":
    asyncio.run(run_seed())
