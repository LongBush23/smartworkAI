import asyncio
from datetime import datetime, timedelta
import random
from backend.database import db
from backend.security import get_password_hash

async def run_seed():
    now = datetime.utcnow()
    print("Force Seeding data...")
    # Xóa dữ liệu cũ
    await db.users.delete_many({})
    await db.departments.delete_many({})
    await db.projects.delete_many({})
    await db.tasks.delete_many({})
    await db.comments.delete_many({})
    await db.performance_logs.delete_many({})
    await db.task_requests.delete_many({})
    await db.notifications.delete_many({})
    await db.audit_logs.delete_many({})
    await db.kpi_task_catalog.delete_many({})
    await db.kpi_evaluations.delete_many({})

    # 1. Departments
    depts = [
        {"name": "Phòng Kỹ thuật (Engineering)", "description": "Phát triển phần mềm và hệ thống"},
        {"name": "Phòng Marketing & Sales", "description": "Tiếp thị và Kinh doanh"},
        {"name": "Phòng Nhân sự (HR)", "description": "Tuyển dụng và Hành chính"},
        {"name": "Phòng Tài chính (Finance)", "description": "Kế toán và Tài chính"},
        {"name": "Ban Giám đốc", "description": "Quản trị và Điều hành"}
    ]
    res_depts = await db.departments.insert_many(depts)
    dept_ids = res_depts.inserted_ids

    # 2. Admin user
    admin_id_result = await db.users.insert_one({
        "username": "admin",
        "name": "Quản trị viên Hệ thống",
        "email": "admin@smartwork.com",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
        "department_id": str(dept_ids[4]),  # Ban Giám đốc
        "skills": [],
        "preferences": {"interests": [], "preferred_task_types": [], "max_concurrent_tasks": 99},
        "bio": "Quản trị viên hệ thống SmartWork AI. Toàn quyền quản lý.",
        "ai_metrics": {"historical_quality_score": 95.0, "on_time_rate": 1.0, "capacity_hours_per_week": 40, "current_workload_hours": 0},
        "availability": 100.0,
        "is_admin": True,
    })

    # 3. Directors (1 per department)
    director_names = [
        ("Trần Minh Đức", "director_tech"),
        ("Lê Thị Hương", "director_mkt"),
        ("Phạm Văn Tuấn", "director_hr"),
        ("Hoàng Thị Nga", "director_finance"),
    ]
    director_ids = []
    for i, (dname, uname) in enumerate(director_names):
        r = await db.users.insert_one({
            "username": uname,
            "name": dname,
            "email": f"{uname}@smartwork.com",
            "hashed_password": get_password_hash("123456"),
            "role": "director",
            "department_id": str(dept_ids[i]),
            "skills": [
                {"skill_name": "Quản lý dự án", "self_rating": 5, "verified_rating": 4.8},
                {"skill_name": "Điều hành", "self_rating": 5, "verified_rating": 4.5},
            ],
            "bio": f"Giám đốc/Trưởng phòng {depts[i]['name']}. Có hơn 10 năm kinh nghiệm quản lý.",
            "preferences": {"interests": ["Quản lý chiến lược"], "preferred_task_types": ["Giám sát", "Phê duyệt"], "max_concurrent_tasks": 10},
            "ai_metrics": {"historical_quality_score": 90.0, "on_time_rate": 0.95, "capacity_hours_per_week": 40, "current_workload_hours": 10},
            "availability": 100.0,
            "is_admin": False,
        })
        director_ids.append(r.inserted_id)

    # 4. Leaders (2 per department)
    leader_ids = []
    leader_counter = 0
    for i in range(4):
        for j in range(2):
            leader_counter += 1
            lname = f"Trưởng nhóm {leader_counter} ({depts[i]['name'].split(' ')[1]})"
            r = await db.users.insert_one({
                "username": f"leader{leader_counter}",
                "name": lname,
                "email": f"leader{leader_counter}@smartwork.com",
                "hashed_password": get_password_hash("123456"),
                "role": "leader",
                "department_id": str(dept_ids[i]),
                "skills": [
                    {"skill_name": "Quản lý nhóm", "self_rating": 4, "verified_rating": 4.0},
                    {"skill_name": "Chuyên môn nghiệp vụ", "self_rating": 4, "verified_rating": 4.2},
                ],
                "bio": f"Trưởng nhóm thuộc {depts[i]['name']}. Chịu trách nhiệm trực tiếp phân công và giám sát.",
                "preferences": {"interests": ["Quản lý rủi ro"], "preferred_task_types": ["Giám sát", "Thực thi"], "max_concurrent_tasks": 8},
                "ai_metrics": {"historical_quality_score": 88.0, "on_time_rate": 0.92, "capacity_hours_per_week": 40, "current_workload_hours": random.randint(5, 20)},
                "availability": 100.0,
                "is_admin": False,
            })
            leader_ids.append(r.inserted_id)

    # 5. Staff (80 employees)
    first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
    middle_names = ["Văn", "Thị", "Hữu", "Minh", "Xuân", "Thu", "Hải", "Ngọc", "Đức", "Công", "Đình", "Quốc", "Thanh", "Bích", "Phương", "Gia"]
    last_names = ["Hùng", "Hương", "Anh", "Tuấn", "Linh", "Cường", "Trang", "Khoa", "Nga", "Long", "Bình", "Châu", "Duy", "Phúc", "Khang", "Tâm", "Mai", "Quỳnh", "Thảo"]

    skills_pool = ["Phát triển phần mềm", "Kiểm thử (QA/QC)", "Phân tích nghiệp vụ (BA)", "Lập trình Web",
                   "Thiết kế UI/UX", "Digital Marketing", "SEO/SEM", "Content Creator",
                   "Tuyển dụng (TA)", "Đào tạo nội bộ", "Kế toán tổng hợp", "Phân tích tài chính",
                   "Quản trị hệ thống (DevOps)", "Bảo mật thông tin", "Quản lý quan hệ khách hàng",
                   "Quản trị dự án (Agile/Scrum)", "Giao tiếp tiếng Anh", "Xử lý sự cố", "Lập báo cáo", "Pháp lý doanh nghiệp"]

    emp_ids = []
    for idx in range(80):
        name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"
        dept_idx = idx % 4
        sampled_skills = random.sample(skills_pool, k=random.randint(2, 5))
        emp_skills = [
            {
                "skill_name": s,
                "self_rating": random.randint(2, 5),
                "verified_rating": round(random.uniform(2.5, 5.0), 1) if random.choice([True, False]) else None,
                "last_used": (now - timedelta(days=random.randint(1, 100))).isoformat()
            } for s in sampled_skills
        ]

        r = await db.users.insert_one({
            "username": f"user{idx}",
            "name": name,
            "email": f"user{idx}@smartwork.com",
            "hashed_password": get_password_hash("123456"),
            "role": "staff",
            "department_id": str(dept_ids[dept_idx]),
            "skills": emp_skills,
            "bio": "Chuyên viên năng nổ, nhiệt tình. Đã tham gia nhiều dự án của công ty.",
            "preferences": {
                "interests": random.sample(["Trí tuệ nhân tạo", "Quản lý rủi ro", "Tự động hoá", "Giao tiếp đám đông", "Phần mềm dự toán"], k=random.randint(1, 2)),
                "preferred_task_types": random.sample(["Nghiên cứu", "Thực thi", "Báo cáo", "Nhập liệu", "Review"], k=random.randint(1, 2)),
                "max_concurrent_tasks": random.randint(2, 5)
            },
            "ai_metrics": {
                "historical_quality_score": round(random.uniform(60.0, 98.0), 1),
                "on_time_rate": round(random.uniform(0.7, 1.0), 2),
                "capacity_hours_per_week": 40,
                "current_workload_hours": 0
            },
            "availability": 100.0,
            "is_admin": False,
        })
        emp_ids.append(r.inserted_id)

    # 6. Projects (15)
    project_names = [
        "Phát triển Ứng dụng Di động SmartWork", "Chiến dịch Marketing Quý 3", 
        "Tuyển dụng 50 nhân sự IT", "Tối ưu hóa Hệ thống Kế toán nội bộ",
        "Triển khai CRM cho Khách hàng", "Đào tạo Kỹ năng mềm cho Nhân viên",
        "Quy hoạch Cơ sở hạ tầng Đám mây", "Tổ chức Sự kiện Year End Party",
        "Kiểm toán Báo cáo Tài chính Q2", "Nghiên cứu Thị trường Châu Á",
        "Nâng cấp Hệ thống Bảo mật", "Đánh giá Năng lực Cán bộ 2026",
        "Triển khai ERP Toàn Công ty", "Chiến dịch Social Media Mùa Hè",
        "Xây dựng Tiêu chuẩn Chất lượng ISO"
    ]

    proj_ids = []
    for i, pname in enumerate(project_names):
        start = now - timedelta(days=random.randint(10, 90))
        end = start + timedelta(days=random.randint(30, 180))
        p_status = random.choice(["planning", "in_progress", "completed", "delayed"])
        dept_idx = i % 4

        proj = {
            "name": pname,
            "description": f"Dự án chiến lược cấp công ty: {pname}. Yêu cầu hoàn thành đúng hạn và đạt chất lượng cao nhất.",
            "status": p_status,
            "start_date": start,
            "end_date": end,
            "progress": 100 if p_status == "completed" else (random.randint(10, 90) if p_status != "planning" else 0),
            "historical_score": round(random.uniform(70.0, 98.0), 1),
            "department_id": str(dept_ids[dept_idx]),
        }
        r = await db.projects.insert_one(proj)
        proj_ids.append(r.inserted_id)

    # 7. Tasks & Subtasks
    tasks = []
    emp_workloads = {str(eid): 0 for eid in emp_ids}

    for p_id in proj_ids:
        num_tasks = random.randint(8, 15)
        for i in range(num_tasks):
            t_status = random.choice(["todo", "in_progress", "review", "done"])
            assigned_to = str(random.choice(emp_ids)) if t_status != "todo" else None
            effort = random.randint(4, 40)
            
            subtasks = []
            num_subtasks = random.randint(3, 8)
            for j in range(num_subtasks):
                st_is_done = False
                if t_status == "done":
                    st_is_done = True
                elif t_status in ["in_progress", "review"]:
                    st_is_done = random.choice([True, False])
                    
                subtasks.append({
                    "id": f"sub_{random.randint(1000, 99999)}",
                    "title": f"Mục tiêu chi tiết: Hoàn thành cấu phần {j+1}",
                    "is_completed": st_is_done
                })

            task = {
                "project_id": str(p_id),
                "title": f"Công việc {i+1} - {random.choice(['Phân tích', 'Phát triển', 'Kiểm thử', 'Thiết kế', 'Lập báo cáo', 'Triển khai'])}",
                "description": f"Yêu cầu chuyên môn cao, chú ý deadline và chất lượng đầu ra. Tuân thủ quy trình.",
                "assigned_to": assigned_to,
                "status": t_status,
                "priority": random.choice(["low", "medium", "high", "urgent"]),
                "progress": 100 if t_status == "done" else (sum(1 for st in subtasks if st["is_completed"]) / len(subtasks) * 100 if len(subtasks) > 0 else 0),
                "deadline": now + timedelta(days=random.randint(-15, 60)),
                "actual_end": (now - timedelta(days=random.randint(1, 10))) if t_status == "done" else None,
                "effort_required": effort,
                "quality_score": round(random.uniform(75.0, 100.0), 1) if t_status == "done" else None,
                "required_skills": random.sample(skills_pool, k=random.randint(1, 3)),
                "max_assignees": 1,
                "subtasks": subtasks
            }

            if t_status in ["in_progress", "review"] and assigned_to:
                emp_workloads[assigned_to] = emp_workloads.get(assigned_to, 0) + effort
            tasks.append(task)

    res_tasks = await db.tasks.insert_many(tasks)
    inserted_task_ids = res_tasks.inserted_ids

    # Comments
    comments_list = []
    comment_texts = [
        "Tiến độ đang rất tốt nhé mọi người, tiếp tục phát huy.",
        "Tôi đã tải lên tài liệu mới nhất, vui lòng xem qua.",
        "Cần đẩy nhanh tiến độ vì sắp tới deadline rồi.",
        "Phần này có vài lỗi nhỏ, đề nghị sửa lại.",
        "Hoàn thành xuất sắc, chất lượng rất tốt.",
        "Đề nghị các phòng ban phối hợp chặt chẽ hơn."
    ]
    user_cursor = db.users.find({}, {"_id": 1, "name": 1})
    user_map = {str(u["_id"]): u["name"] for u in await user_cursor.to_list(None)}

    for i, t in enumerate(tasks):
        if random.random() < 0.4:
            for _ in range(random.randint(2, 6)):
                uid = str(random.choice(emp_ids + leader_ids + director_ids))
                comments_list.append({
                    "task_id": str(inserted_task_ids[i]),
                    "user_id": uid,
                    "user_name": user_map.get(uid, "Người dùng"),
                    "content": random.choice(comment_texts),
                    "created_at": now - timedelta(hours=random.randint(1, 200))
                })
    if comments_list:
        await db.comments.insert_many(comments_list)

    # 10. KPI Catalogs (1 per department)
    kpi_categories = ["Chuyên môn", "Kỷ luật", "Phối hợp", "Hỗ trợ", "Đột xuất"]
    kpi_catalogs = []
    for dept_id in dept_ids:
        items = []
        for j in range(random.randint(5, 10)):
            items.append({
                "id": f"item_{random.randint(1000, 9999)}",
                "task_name": f"Nhiệm vụ trọng tâm {j+1}",
                "category": random.choice(kpi_categories),
                "complexity_group": random.choice([1, 2, 3]),
                "kpi_point": random.choice([10, 20, 30, 40, 50, 60, 80, 100])
            })
        kpi_catalogs.append({
            "department_id": str(dept_id),
            "period_year": now.year,
            "name": f"Danh mục KPI Năm {now.year} - Phòng {user_map.get(str(dept_id), 'Chuyên môn')}",
            "status": "approved",
            "items": items,
            "approved_by": str(director_ids[0]),
            "approved_at": now - timedelta(days=30),
            "created_by": str(admin_id_result.inserted_id),
            "created_at": now - timedelta(days=32),
            "updated_at": now - timedelta(days=30)
        })
    await db.kpi_task_catalog.insert_many(kpi_catalogs)

    # 11. Generate PAST Evaluations for Last Month (to populate the Ranking Board!)
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1
    
    past_evaluations = []
    
    # helper for realistic scores
    def random_kpi_score():
        # Score A, B, C
        score_a = round(random.uniform(0.7, 1.0), 2)
        score_b = round(random.uniform(0.7, 1.2), 2)
        score_c = round(random.uniform(0.7, 1.2), 2)
        kpi = ((score_a + score_b + score_c) / 3) * 100
        grp = 'group_1' if kpi >= 70 else ('group_2' if kpi >= 50 else 'group_3')
        return score_a, score_b, score_c, round(kpi, 2), grp

    all_users = await db.users.find({"role": {"$ne": "admin"}}).to_list(None)
    for u in all_users:
        uid = str(u["_id"])
        is_leader = u["role"] in ["director", "leader"]
        
        sa, sb, sc, kpi, grp = random_kpi_score()
        sd = round(random.uniform(0.6, 1.0), 2) if is_leader else None
        
        if is_leader:
            kpi = ((sa + sb + sc + sd) / 4) * 100
            grp = 'group_1' if kpi >= 70 else ('group_2' if kpi >= 50 else 'group_3')
            kpi = round(kpi, 2)
            
        total_e = round(random.uniform(20.0, 30.0), 1)
        final_score = round(total_e + (kpi * 0.7), 2)
            
        past_evaluations.append({
            "evaluation_type": "individual",
            "target_id": uid,
            "target_name": u["name"],
            "target_role": u["role"],
            "department_id": u["department_id"],
            "period_type": "monthly",
            "period_month": last_month,
            "period_year": last_month_year,
            "overall_status": "approved",
            "created_at": now - timedelta(days=10),
            "updated_at": now - timedelta(days=2),
            "approval": {
                "score_A": sa,
                "score_B": sb,
                "score_C": sc,
                "score_D": sd,
                "kpi_score": kpi,
                "kpi_group": grp,
                "total_assigned_points": random.randint(50, 300)
            },
            "general_criteria": {
                "total_E": total_e,
                "total_final_score": final_score
            }
        })
        
    await db.kpi_evaluations.insert_many(past_evaluations)
    
    # 12. Create DRAFT Evaluations for THIS month so users can test self-evaluate
    draft_evaluations = []
    for u in all_users[:15]:  # Just first 15 for demo
        draft_evaluations.append({
            "evaluation_type": "individual",
            "target_id": str(u["_id"]),
            "target_name": u["name"],
            "target_role": u["role"],
            "department_id": u["department_id"],
            "period_type": "monthly",
            "period_month": now.month,
            "period_year": now.year,
            "overall_status": "draft",
            "created_at": now,
            "updated_at": now
        })
    await db.kpi_evaluations.insert_many(draft_evaluations)

    print("DONE! Fully populated database with realistic professional data.")

if __name__ == "__main__":
    asyncio.run(run_seed())
