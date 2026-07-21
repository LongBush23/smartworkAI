import sqlite3
import json
import random
from datetime import datetime, timedelta, date

DB_PATH = "smartwork.db"

DEPARTMENTS = [
    {"id": 1, "name": "Phòng Hành chính - Tổng hợp", "code": "HC"},
    {"id": 2, "name": "Phòng Công nghệ thông tin", "code": "CNTT"},
    {"id": 3, "name": "Phòng Kế hoạch - Tài chính", "code": "KHTC"},
    {"id": 4, "name": "Phòng Pháp chế", "code": "PC"},
    {"id": 5, "name": "Phòng Tổ chức - Nhân sự", "code": "TCNS"},
]

SKILLS_POOL = [
    "Lập trình Python", "Lập trình JavaScript", "Cơ sở dữ liệu",
    "Quản lý dự án", "Phân tích dữ liệu", "Thiết kế UI/UX",
    "Hệ thống mạng", "Bảo mật thông tin", "Văn bản hành chính",
    "Kế toán", "Pháp lý", "Đào tạo", "Báo cáo thống kê",
    "Trí tuệ nhân tạo", "Điện toán đám mây"
]

EMPLOYEES = [
    {"id": 1,  "name": "Nguyễn Văn An",    "dept_id": 2, "position": "Trưởng phòng",  "skills": ["Lập trình Python","Trí tuệ nhân tạo","Quản lý dự án","Điện toán đám mây"], "experience": 8},
    {"id": 2,  "name": "Trần Thị Bình",    "dept_id": 2, "position": "Chuyên viên",   "skills": ["Lập trình JavaScript","Thiết kế UI/UX","Cơ sở dữ liệu"], "experience": 4},
    {"id": 3,  "name": "Lê Hoàng Cường",   "dept_id": 2, "position": "Chuyên viên",   "skills": ["Hệ thống mạng","Bảo mật thông tin","Cơ sở dữ liệu"], "experience": 5},
    {"id": 4,  "name": "Phạm Thị Dung",    "dept_id": 2, "position": "Nhân viên",     "skills": ["Lập trình Python","Phân tích dữ liệu","Trí tuệ nhân tạo"], "experience": 2},
    {"id": 5,  "name": "Hoàng Văn Em",     "dept_id": 2, "position": "Nhân viên",     "skills": ["Lập trình JavaScript","Lập trình Python"], "experience": 1},
    {"id": 6,  "name": "Võ Thị Phương",    "dept_id": 1, "position": "Trưởng phòng",  "skills": ["Văn bản hành chính","Quản lý dự án","Báo cáo thống kê"], "experience": 10},
    {"id": 7,  "name": "Đỗ Minh Giang",    "dept_id": 1, "position": "Chuyên viên",   "skills": ["Văn bản hành chính","Báo cáo thống kê","Đào tạo"], "experience": 6},
    {"id": 8,  "name": "Bùi Thị Hằng",     "dept_id": 1, "position": "Nhân viên",     "skills": ["Văn bản hành chính","Kế toán"], "experience": 3},
    {"id": 9,  "name": "Ngô Quốc Hùng",    "dept_id": 3, "position": "Trưởng phòng",  "skills": ["Kế toán","Phân tích dữ liệu","Báo cáo thống kê","Quản lý dự án"], "experience": 12},
    {"id": 10, "name": "Đinh Thị Lan",     "dept_id": 3, "position": "Chuyên viên",   "skills": ["Kế toán","Báo cáo thống kê"], "experience": 5},
    {"id": 11, "name": "Trương Văn Minh",  "dept_id": 3, "position": "Nhân viên",     "skills": ["Kế toán","Phân tích dữ liệu"], "experience": 2},
    {"id": 12, "name": "Lý Thị Nga",       "dept_id": 4, "position": "Trưởng phòng",  "skills": ["Pháp lý","Văn bản hành chính","Quản lý dự án"], "experience": 9},
    {"id": 13, "name": "Phan Văn Oanh",    "dept_id": 4, "position": "Chuyên viên",   "skills": ["Pháp lý","Văn bản hành chính"], "experience": 4},
    {"id": 14, "name": "Tạ Thị Phúc",      "dept_id": 5, "position": "Trưởng phòng",  "skills": ["Quản lý dự án","Đào tạo","Báo cáo thống kê"], "experience": 7},
    {"id": 15, "name": "Hà Văn Quân",      "dept_id": 5, "position": "Chuyên viên",   "skills": ["Đào tạo","Văn bản hành chính","Báo cáo thống kê"], "experience": 3},
]

PROJECTS = [
    {"id": 1,  "name": "Hệ thống Cổng Dịch vụ Công tỉnh Đắk Lắk",       "dept_id": 2, "priority": "Cao",    "status": "Đang thực hiện"},
    {"id": 2,  "name": "Chuyển đổi số hồ sơ hành chính",                  "dept_id": 1, "priority": "Cao",    "status": "Đang thực hiện"},
    {"id": 3,  "name": "Nâng cấp hạ tầng mạng nội bộ",                   "dept_id": 2, "priority": "Trung bình", "status": "Đang thực hiện"},
    {"id": 4,  "name": "Phần mềm quản lý tài chính – ngân sách",          "dept_id": 3, "priority": "Cao",    "status": "Hoàn thành"},
    {"id": 5,  "name": "Xây dựng quy trình ISO 9001:2015",                "dept_id": 5, "priority": "Trung bình", "status": "Đang thực hiện"},
    {"id": 6,  "name": "Hệ thống camera giám sát thông minh",             "dept_id": 2, "priority": "Cao",    "status": "Đang thực hiện"},
    {"id": 7,  "name": "Ứng dụng SmartWork AI nội bộ",                    "dept_id": 2, "priority": "Cao",    "status": "Đang thực hiện"},
    {"id": 8,  "name": "Đào tạo kỹ năng số cho cán bộ",                  "dept_id": 5, "priority": "Thấp",   "status": "Hoàn thành"},
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        dept_id INTEGER,
        position TEXT,
        skills TEXT,
        experience INTEGER DEFAULT 0,
        FOREIGN KEY(dept_id) REFERENCES departments(id)
    );

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        dept_id INTEGER,
        priority TEXT DEFAULT 'Trung bình',
        status TEXT DEFAULT 'Chưa bắt đầu',
        start_date TEXT,
        end_date TEXT,
        progress INTEGER DEFAULT 0,
        description TEXT,
        FOREIGN KEY(dept_id) REFERENCES departments(id)
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        project_id INTEGER,
        name TEXT NOT NULL,
        assignee_id INTEGER,
        status TEXT DEFAULT 'Chưa bắt đầu',
        priority TEXT DEFAULT 'Trung bình',
        start_date TEXT,
        due_date TEXT,
        completed_date TEXT,
        progress INTEGER DEFAULT 0,
        estimated_hours INTEGER DEFAULT 8,
        actual_hours INTEGER DEFAULT 0,
        skills_required TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(assignee_id) REFERENCES employees(id)
    );

    CREATE TABLE IF NOT EXISTS performance_logs (
        id INTEGER PRIMARY KEY,
        employee_id INTEGER,
        task_id INTEGER,
        on_time INTEGER DEFAULT 1,
        quality_score REAL DEFAULT 3.0,
        effort_score REAL DEFAULT 3.0,
        log_date TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    );
    """)

    conn.commit()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM departments")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    # Seed departments
    for d in DEPARTMENTS:
        cur.execute("INSERT INTO departments VALUES (?,?,?)", (d["id"], d["name"], d["code"]))

    # Seed employees
    for e in EMPLOYEES:
        cur.execute("INSERT INTO employees VALUES (?,?,?,?,?,?)",
                    (e["id"], e["name"], e["dept_id"], e["position"],
                     json.dumps(e["skills"], ensure_ascii=False), e["experience"]))

    # Seed projects with dates
    today = date.today()
    project_dates = [
        (today - timedelta(days=60), today + timedelta(days=30)),
        (today - timedelta(days=45), today + timedelta(days=15)),
        (today - timedelta(days=30), today + timedelta(days=45)),
        (today - timedelta(days=90), today - timedelta(days=5)),
        (today - timedelta(days=20), today + timedelta(days=60)),
        (today - timedelta(days=15), today + timedelta(days=75)),
        (today - timedelta(days=10), today + timedelta(days=80)),
        (today - timedelta(days=120), today - timedelta(days=30)),
    ]
    progress_values = [65, 45, 78, 100, 30, 20, 15, 100]
    descriptions = [
        "Xây dựng cổng dịch vụ công trực tuyến tích hợp với hệ thống quốc gia",
        "Số hóa toàn bộ hồ sơ giấy tờ hành chính, tích hợp chữ ký số",
        "Nâng cấp băng thông, triển khai WiFi 6 và VPN bảo mật",
        "Phần mềm kế toán và quản lý ngân sách theo chuẩn Bộ Tài chính",
        "Xây dựng và triển khai hệ thống quản lý chất lượng ISO",
        "Lắp đặt camera AI nhận diện khuôn mặt và biển số xe",
        "Phần mềm quản lý công việc nội bộ ứng dụng AI",
        "Chương trình đào tạo kỹ năng số cơ bản cho 200 cán bộ",
    ]

    for i, p in enumerate(PROJECTS):
        sd, ed = project_dates[i]
        cur.execute("""INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)""",
                    (p["id"], p["name"], p["dept_id"], p["priority"], p["status"],
                     sd.isoformat(), ed.isoformat(), progress_values[i], descriptions[i]))

    # Seed tasks
    random.seed(42)
    task_templates = [
        ("Phân tích yêu cầu", ["Quản lý dự án", "Báo cáo thống kê"]),
        ("Thiết kế kiến trúc hệ thống", ["Lập trình Python", "Cơ sở dữ liệu"]),
        ("Phát triển giao diện người dùng", ["Lập trình JavaScript", "Thiết kế UI/UX"]),
        ("Phát triển API backend", ["Lập trình Python", "Cơ sở dữ liệu"]),
        ("Kiểm thử và sửa lỗi", ["Lập trình Python", "Lập trình JavaScript"]),
        ("Viết tài liệu kỹ thuật", ["Văn bản hành chính", "Báo cáo thống kê"]),
        ("Triển khai và cấu hình", ["Hệ thống mạng", "Điện toán đám mây"]),
        ("Đào tạo người dùng", ["Đào tạo", "Văn bản hành chính"]),
    ]

    task_id = 1
    task_statuses_by_progress = {
        100: ["Hoàn thành"] * 5,
        65: ["Hoàn thành", "Hoàn thành", "Hoàn thành", "Đang thực hiện", "Chưa bắt đầu"],
        45: ["Hoàn thành", "Hoàn thành", "Đang thực hiện", "Chưa bắt đầu", "Chưa bắt đầu"],
        78: ["Hoàn thành", "Hoàn thành", "Hoàn thành", "Đang thực hiện", "Chưa bắt đầu"],
        30: ["Hoàn thành", "Đang thực hiện", "Chưa bắt đầu", "Chưa bắt đầu", "Chưa bắt đầu"],
        20: ["Hoàn thành", "Chưa bắt đầu", "Chưa bắt đầu", "Chưa bắt đầu", "Chưa bắt đầu"],
        15: ["Đang thực hiện", "Chưa bắt đầu", "Chưa bắt đầu", "Chưa bắt đầu", "Chưa bắt đầu"],
    }

    dept_employees = {}
    for e in EMPLOYEES:
        dept_employees.setdefault(e["dept_id"], []).append(e["id"])

    all_tasks = []
    for i, p in enumerate(PROJECTS):
        pv = progress_values[i]
        sd, ed = project_dates[i]
        statuses = task_statuses_by_progress.get(pv, ["Chưa bắt đầu"] * 5)
        avail_employees = dept_employees.get(p["dept_id"], [1])

        for j, (tname, skills) in enumerate(task_templates[:5]):
            status = statuses[j] if j < len(statuses) else "Chưa bắt đầu"
            task_start = sd + timedelta(days=j*7)
            task_due = task_start + timedelta(days=random.randint(5, 14))
            assignee = random.choice(avail_employees)
            prog = 100 if status == "Hoàn thành" else (random.randint(20, 80) if status == "Đang thực hiện" else 0)
            completed_date = task_due.isoformat() if status == "Hoàn thành" else None
            est_hours = random.choice([8, 16, 24, 32, 40])
            actual_hours = int(est_hours * random.uniform(0.8, 1.3)) if status != "Chưa bắt đầu" else 0

            cur.execute("""INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (task_id, p["id"], tname, assignee, status,
                         random.choice(["Cao", "Trung bình", "Thấp"]),
                         task_start.isoformat(), task_due.isoformat(), completed_date,
                         prog, est_hours, actual_hours,
                         json.dumps(skills, ensure_ascii=False)))
            all_tasks.append((task_id, assignee, status, task_due, pv))
            task_id += 1

    # Seed performance logs
    perf_id = 1
    for tid, emp_id, status, due, pv in all_tasks:
        if status == "Hoàn thành":
            on_time = 1 if pv >= 60 else random.choice([0, 1])
            quality = round(random.uniform(3.0, 5.0) if pv >= 60 else random.uniform(2.0, 4.0), 1)
            effort = round(random.uniform(3.0, 5.0), 1)
            log_date = (due - timedelta(days=random.randint(0, 3))).isoformat()
            cur.execute("INSERT INTO performance_logs VALUES (?,?,?,?,?,?,?)",
                        (perf_id, emp_id, tid, on_time, quality, effort, log_date))
            perf_id += 1

    conn.commit()
    conn.close()
    print("✅ Database initialized with Đắk Lắk seed data")

if __name__ == "__main__":
    init_db()
