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
                {"skill_name": "Điều hành cuộc họp", "self_rating": 5, "verified_rating": 4.5},
            ],
            "bio": f"Trưởng phòng {depts[i]['name']}. Có hơn 10 năm kinh nghiệm quản lý hành chính nhà nước.",
            "preferences": {"interests": ["Quản lý chiến lược"], "preferred_task_types": ["Giám sát", "Phê duyệt"], "max_concurrent_tasks": 5},
            "ai_metrics": {"historical_quality_score": 90.0, "on_time_rate": 0.95, "capacity_hours_per_week": 40, "current_workload_hours": 10},
            "availability": 100.0,
            "is_admin": False,
        })
        director_ids.append(r.inserted_id)

    # 4. Leaders (1 per department)
    leader_ids = []
    leader_counter = 0
    for i in range(4):
        for j in range(1):
            leader_counter += 1
            lname = f"Nhóm trưởng {leader_counter}"
            r = await db.users.insert_one({
                "username": f"leader{leader_counter}",
                "name": lname,
                "email": f"leader{leader_counter}@smartwork.com",
                "hashed_password": get_password_hash("123456"),
                "role": "leader",
                "department_id": str(dept_ids[i]),
                "skills": [
                    {"skill_name": random.choice(["Phát triển phần mềm", "Phân tích Dữ liệu", "Digital Marketing", "Tuyển dụng"]), "self_rating": 4, "verified_rating": 4.0},
                    {"skill_name": random.choice(["Lập kế hoạch", "Quản lý chất lượng", "Tài chính doanh nghiệp"]), "self_rating": 4, "verified_rating": 3.5},
                ],
                "bio": f"Nhóm trưởng thuộc {depts[i]['name']}. Phụ trách giám sát và điều phối công việc trong nhóm.",
                "preferences": {"interests": random.sample(["Quản lý rủi ro", "Tự động hoá", "Phân tích dữ liệu"], k=1), "preferred_task_types": ["Giám sát", "Thực thi"], "max_concurrent_tasks": 4},
                "ai_metrics": {"historical_quality_score": round(random.uniform(75, 92), 1), "on_time_rate": round(random.uniform(0.85, 0.98), 2), "capacity_hours_per_week": 40, "current_workload_hours": random.randint(5, 20)},
                "availability": 100.0,
                "is_admin": False,
            })
            leader_ids.append(r.inserted_id)

    # 5. Staff (100 employees)
    first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
    middle_names = ["Văn", "Thị", "Hữu", "Minh", "Xuân", "Thu", "Hải", "Ngọc", "Đức", "Công", "Đình", "Quốc", "Thanh", "Bích", "Phương", "Gia"]
    last_names = ["Hùng", "Hương", "Anh", "Tuấn", "Linh", "Cường", "Trang", "Khoa", "Nga", "Long", "Bình", "Châu", "Duy", "Phúc", "Khang", "Tâm", "Mai", "Quỳnh", "Thảo"]

    skills_pool = ["Phát triển phần mềm", "Kiểm thử (QA/QC)", "Phân tích nghiệp vụ (BA)", "Lập trình Web",
                   "Thiết kế UI/UX", "Digital Marketing", "SEO/SEM", "Content Creator",
                   "Tuyển dụng (TA)", "Đào tạo nội bộ", "Kế toán tổng hợp", "Phân tích tài chính",
                   "Quản trị hệ thống (DevOps)", "Bảo mật thông tin", "Quản lý quan hệ khách hàng",
                   "Quản trị dự án (Agile/Scrum)", "Giao tiếp tiếng Anh", "Xử lý sự cố", "Lập báo cáo", "Pháp lý doanh nghiệp"]

    bio_templates = [
        "Chuyên viên có {} năm kinh nghiệm trong lĩnh vực {}. Từng tham gia {} dự án lớn tại doanh nghiệp.",
        "Am hiểu sâu sắc về quy trình {} và có khả năng {} tốt. Đặc biệt giỏi trong việc {}.",
        "Tốt nghiệp chuyên ngành {}. Có kinh nghiệm thực tiễn trong {} và đã hoàn thành xuất sắc nhiệm vụ được giao.",
        "Có {} năm kinh nghiệm làm việc thực tế. Kỹ năng {} rất tốt và luôn hoàn thành deadline."
    ]

    emp_ids = []
    for idx in range(20):
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

        bio = random.choice(bio_templates).format(
            random.randint(2, 8),
            random.choice(["công nghệ thông tin", "marketing", "tài chính", "nhân sự"]),
            random.randint(2, 6),
            depts[dept_idx]["name"]
        )

        r = await db.users.insert_one({
            "username": f"user{idx}",
            "name": name,
            "email": f"user{idx}@smartwork.com",
            "hashed_password": get_password_hash("123456"),
            "role": "staff",
            "department_id": str(dept_ids[dept_idx]),
            "skills": emp_skills,
            "bio": bio,
            "preferences": {
                "interests": random.sample(["Trí tuệ nhân tạo", "Quản lý rủi ro", "Tự động hoá", "Giao tiếp đám đông", "Phần mềm dự toán"], k=random.randint(1, 2)),
                "preferred_task_types": random.sample(["Nghiên cứu", "Thực thi", "Báo cáo", "Nhập liệu", "Review"], k=random.randint(1, 2)),
                "max_concurrent_tasks": random.randint(2, 5)
            },
            "ai_metrics": {
                "historical_quality_score": round(random.uniform(60.0, 95.0), 1),
                "on_time_rate": round(random.uniform(0.7, 1.0), 2),
                "capacity_hours_per_week": 40,
                "current_workload_hours": 0
            },
            "availability": 100.0,
            "is_admin": False,
        })
        emp_ids.append(r.inserted_id)

    # 6. Projects (6)
    project_names = [
        "Phát triển Ứng dụng Di động SmartWork", "Chiến dịch Marketing Quý 3", 
        "Tuyển dụng 50 nhân sự IT", "Tối ưu hóa Hệ thống Kế toán nội bộ",
        "Triển khai CRM cho Khách hàng", "Đào tạo Kỹ năng mềm cho Nhân viên"
    ]

    proj_ids = []
    for i, pname in enumerate(project_names):
        start = now - timedelta(days=random.randint(0, 60))
        end = start + timedelta(days=random.randint(30, 120))
        p_status = random.choice(["planning", "in_progress", "completed", "delayed"])
        dept_idx = i % 4

        proj = {
            "name": pname,
            "description": f"Dự án chiến lược: {pname}",
            "status": p_status,
            "start_date": start,
            "end_date": end,
            "progress": 100 if p_status == "completed" else (random.randint(0, 100) if p_status != "planning" else 0),
            "historical_score": round(random.uniform(60.0, 90.0), 1),
            "department_id": str(dept_ids[dept_idx]),
        }
        r = await db.projects.insert_one(proj)
        proj_ids.append(r.inserted_id)

    # 7. Tasks, Subtasks & Performance Logs
    tasks = []
    perf_logs = []
    comments_list = []
    emp_workloads = {str(eid): 0 for eid in emp_ids}

    required_skills_pool = ["Phát triển phần mềm", "Kiểm thử (QA/QC)", "Phân tích Dữ liệu", "Thiết kế UI/UX", "Digital Marketing", "Tài chính", "Lập trình Web", "Đào tạo nội bộ"]

    for p_id in proj_ids:
        num_tasks = random.randint(3, 5)
        for i in range(num_tasks):
            t_status = random.choice(["todo", "in_progress", "review", "done"])
            assigned_to = str(random.choice(emp_ids)) if t_status != "todo" else None
            effort = random.randint(2, 20)
            req_skills = random.sample(required_skills_pool, k=random.randint(1, 4))
            
            # Generate Subtasks
            subtasks = []
            num_subtasks = random.randint(2, 6)
            for j in range(num_subtasks):
                st_is_done = False
                if t_status == "done":
                    st_is_done = True
                elif t_status in ["in_progress", "review"]:
                    st_is_done = random.choice([True, False])
                    
                subtasks.append({
                    "id": f"sub_{random.randint(1000, 9999)}",
                    "title": f"Bước công việc nhỏ {j+1}",
                    "is_completed": st_is_done
                })

            task = {
                "project_id": str(p_id),
                "title": f"Công việc {i+1} - {random.choice(['Xử lý', 'Báo cáo', 'Phân tích', 'Kiểm tra', 'Soạn thảo', 'Triển khai'])}",
                "description": f"Chi tiết: Cần hoàn thành theo đúng tiến độ đề ra. Yêu cầu chuyên môn: {', '.join(req_skills)}.",
                "assigned_to": assigned_to,
                "status": t_status,
                "priority": random.choice(["low", "medium", "high", "urgent"]),
                "progress": 100 if t_status == "done" else (sum(1 for st in subtasks if st["is_completed"]) / len(subtasks) * 100 if len(subtasks) > 0 else 0),
                "deadline": now + timedelta(days=random.randint(-15, 45)),
                "actual_end": (now - timedelta(days=random.randint(1, 10))) if t_status == "done" else None,
                "effort_required": effort,
                "quality_score": round(random.uniform(70.0, 100.0), 1) if t_status == "done" else None,
                "required_skills": req_skills,
                "max_assignees": 1,
                "subtasks": subtasks
            }

            if t_status in ["in_progress", "review"] and assigned_to:
                emp_workloads[assigned_to] = emp_workloads.get(assigned_to, 0) + effort

            tasks.append(task)

    res_tasks = await db.tasks.insert_many(tasks)
    inserted_task_ids = res_tasks.inserted_ids
    
    # Generate Comments for some tasks
    comment_texts = [
        "Tiến độ đang rất tốt nhé mọi người.",
        "Phần này cần rà soát lại số liệu.",
        "Đã hoàn thành bước 1, chuẩn bị sang bước 2.",
        "Sếp xem qua giúp em file đính kèm với ạ.",
        "Đang gặp chút vướng mắc ở khâu integration, cần team kỹ thuật hỗ trợ.",
        "Đã cập nhật hệ thống theo yêu cầu.",
        "Deadline có thể bị trễ 2 ngày do chờ phản hồi từ đối tác."
    ]
    
    for i, t in enumerate(tasks):
        # 30% chance task has comments
        if random.random() < 0.3:
            num_comments = random.randint(1, 5)
            for _ in range(num_comments):
                commenter_id = str(random.choice(emp_ids + leader_ids + director_ids))
                # Giả lập tên commenter
                c_name = "Nhân viên"
                comments_list.append({
                    "task_id": str(inserted_task_ids[i]),
                    "user_id": commenter_id,
                    "user_name": c_name, # Sẽ hơi sai logic hiển thị nếu thiếu tên chuẩn, nhưng FE gọi Auth có khi ko cần tên chính xác. 
                    "content": random.choice(comment_texts),
                    "created_at": now - timedelta(hours=random.randint(1, 100))
                })
                
    if comments_list:
        # Lấy tên chuẩn cho comments (tối ưu hóa)
        user_cursor = db.users.find({}, {"_id": 1, "name": 1})
        user_map = {str(u["_id"]): u["name"] for u in await user_cursor.to_list(None)}
        for c in comments_list:
            c["user_name"] = user_map.get(c["user_id"], "Người dùng")
        await db.comments.insert_many(comments_list)

    # Performance Logs for completed tasks
    for i, t in enumerate(tasks):
        if t["status"] == "done" and t["assigned_to"]:
            perf_logs.append({
                "employee_id": t["assigned_to"],
                "task_id": str(inserted_task_ids[i]),
                "on_time": random.choice([True, True, True, False]),
                "quality": t["quality_score"],
                "effort": t["effort_required"],
                "timestamp": now - timedelta(days=random.randint(1, 20))
            })

    if perf_logs:
        await db.performance_logs.insert_many(perf_logs)

    # Update employee workloads
    from bson import ObjectId
    for eid, w in emp_workloads.items():
        await db.users.update_one({"_id": ObjectId(eid)}, {"$set": {"ai_metrics.current_workload_hours": w}})

    # 8. Sample Task Requests (pending)
    sample_requests = []
    todo_tasks = [t for i, t in enumerate(tasks) if t["status"] == "todo"]
    for _ in range(min(4, len(todo_tasks))):
        t_idx = tasks.index(random.choice(todo_tasks))
        emp = random.choice(emp_ids)
        sample_requests.append({
            "task_id": str(inserted_task_ids[t_idx]),
            "employee_id": str(emp),
            "employee_name": f"Nhân viên",
            "status": "pending",
            "ai_match_score": round(random.uniform(40, 99), 1),
            "message": random.choice([
                "Tôi muốn tham gia công việc này vì phù hợp với chuyên môn của mình.",
                "Sếp cho em nhận task này nhé.",
                "Đang còn rảnh nên có thể hỗ trợ task này.",
                "Chuyên ngành của em rất hợp với yêu cầu này."
            ]),
            "created_at": now - timedelta(hours=random.randint(1, 48)),
            "reviewed_by": None,
            "reviewed_at": None,
            "reject_reason": None,
        })
    if sample_requests:
        # Update names
        for req in sample_requests:
            req["employee_name"] = user_map.get(req["employee_id"], "Nhân viên")
        await db.task_requests.insert_many(sample_requests)

    # 9. Sample Notifications
    sample_notifs = []
    for uid in director_ids + [admin_id]:
        sample_notifs.append({
            "user_id": str(uid),
            "type": "request_submitted",
            "title": "Có yêu cầu tham gia mới 📋",
            "message": "Một nhân viên muốn xin tham gia công việc trong phòng ban của bạn.",
            "reference_id": None,
            "reference_type": "task_request",
            "is_read": False,
            "created_at": now - timedelta(hours=random.randint(1, 24)),
        })
    if sample_notifs:
        await db.notifications.insert_many(sample_notifs)

    print(f"Seeding completed: 1 Admin, {len(director_ids)} Directors, {len(leader_ids)} Leaders, {len(emp_ids)} Staff, {len(proj_ids)} Projects, {len(tasks)} Tasks, {len(sample_requests)} Requests")

if __name__ == "__main__":
    asyncio.run(run_seed())
