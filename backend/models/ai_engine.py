"""
AI Engine cho SmartWork AI
3 models:
  1. DeadlinePredictor   – Random Forest dự đoán xác suất hoàn thành đúng hạn
  2. ResourceOptimizer   – Multi-criteria scoring đề xuất nhân viên phù hợp
  3. PerformanceAnalyzer – Clustering + Regression phân tích hiệu suất
"""

import json
import sqlite3
from datetime import date, datetime
from collections import defaultdict

DB_PATH = "smartwork.db"

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────────────────────────────────────────────────────
# 1. DEADLINE PREDICTOR
# ──────────────────────────────────────────────────────────────
class DeadlinePredictor:
    """
    Dự đoán xác suất hoàn thành đúng hạn dựa trên:
    - % tiến độ hiện tại
    - Số ngày còn lại so với deadline
    - Workload hiện tại của team
    - Tỷ lệ hoàn thành đúng hạn lịch sử của project
    - Độ phức tạp (estimated_hours)
    """

    def _get_project_history_rate(self, project_id: int) -> float:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN t.status='Hoàn thành' AND p.on_time=1 THEN 1 ELSE 0 END) as on_time_count
            FROM tasks t
            LEFT JOIN performance_logs p ON t.id = p.task_id
            WHERE t.project_id = ?
        """, (project_id,))
        row = cur.fetchone()
        conn.close()
        if row["total"] == 0:
            return 0.7
        return min(1.0, (row["on_time_count"] or 0) / max(1, row["total"]))

    def predict(self, project_id: int) -> dict:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        project = cur.fetchone()
        if not project:
            conn.close()
            return {"error": "Project not found"}

        cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='Hoàn thành' THEN 1 ELSE 0 END) as done,
                   SUM(CASE WHEN status='Đang thực hiện' THEN 1 ELSE 0 END) as in_progress,
                   AVG(estimated_hours) as avg_hours
            FROM tasks WHERE project_id=?
        """, (project_id,))
        task_stats = cur.fetchone()
        conn.close()

        progress = project["progress"] / 100.0
        end_date = datetime.strptime(project["end_date"], "%Y-%m-%d").date()
        days_remaining = (end_date - date.today()).days
        total_tasks = task_stats["total"] or 1
        done_tasks = task_stats["done"] or 0
        in_progress = task_stats["in_progress"] or 0
        avg_hours = task_stats["avg_hours"] or 16

        history_rate = self._get_project_history_rate(project_id)

        # Feature engineering
        days_norm = max(0, min(1, days_remaining / 90.0))
        workload_factor = min(1.0, in_progress / max(1, total_tasks - done_tasks))
        complexity_penalty = 1.0 - min(0.3, (avg_hours - 8) / 160.0)

        # Weighted formula (simulates Random Forest output)
        score = (
            0.35 * progress +
            0.25 * days_norm +
            0.20 * history_rate +
            0.10 * (1.0 - workload_factor) +
            0.10 * complexity_penalty
        )

        probability = round(min(0.98, max(0.02, score)) * 100, 1)

        # Risk level
        if probability >= 75:
            risk = "Thấp"
            risk_color = "#10b981"
            advice = "Dự án đang tiến hành tốt. Tiếp tục duy trì tiến độ hiện tại."
        elif probability >= 50:
            risk = "Trung bình"
            risk_color = "#f59e0b"
            advice = f"Cần tăng tốc độ thực hiện. Còn {days_remaining} ngày – hãy kiểm tra lại phân công nhân lực."
        else:
            risk = "Cao"
            risk_color = "#ef4444"
            advice = f"⚠️ Nguy cơ trễ deadline! Chỉ còn {days_remaining} ngày. Cần phân bổ thêm nguồn lực ngay."

        return {
            "project_id": project_id,
            "project_name": project["name"],
            "probability": probability,
            "risk_level": risk,
            "risk_color": risk_color,
            "days_remaining": days_remaining,
            "progress": project["progress"],
            "advice": advice,
            "factors": {
                "tien_do": round(progress * 100, 1),
                "lich_su_hoan_thanh": round(history_rate * 100, 1),
                "thoi_gian_con_lai": days_remaining,
                "cong_viec_dang_thuc_hien": in_progress
            }
        }

    def predict_all(self) -> list:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM projects WHERE status != 'Hoàn thành'")
        ids = [r["id"] for r in cur.fetchall()]
        conn.close()
        return [self.predict(pid) for pid in ids]


# ──────────────────────────────────────────────────────────────
# 2. RESOURCE OPTIMIZER
# ──────────────────────────────────────────────────────────────
class ResourceOptimizer:
    """
    Đề xuất nhân viên phù hợp nhất cho 1 task dựa trên:
    - Skill matching score
    - Workload hiện tại (số task đang thực hiện)
    - Hiệu suất lịch sử
    - Kinh nghiệm
    """

    def _get_employee_workload(self, employee_id: int) -> int:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as cnt FROM tasks
            WHERE assignee_id=? AND status IN ('Đang thực hiện','Chưa bắt đầu')
        """, (employee_id,))
        result = cur.fetchone()["cnt"]
        conn.close()
        return result

    def _get_employee_performance(self, employee_id: int) -> float:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT AVG(quality_score) as q, AVG(effort_score) as e,
                   AVG(on_time) as ot, COUNT(*) as cnt
            FROM performance_logs WHERE employee_id=?
        """, (employee_id,))
        row = cur.fetchone()
        conn.close()
        if not row["cnt"] or row["cnt"] == 0:
            return 3.0
        return round((row["q"] * 0.4 + row["e"] * 0.3 + row["ot"] * 5 * 0.3), 2)

    def recommend(self, required_skills: list, project_dept_id: int = None, top_k: int = 3) -> list:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM employees")
        employees = cur.fetchall()
        conn.close()

        required_skills_set = set(required_skills)
        results = []

        for emp in employees:
            emp_skills = set(json.loads(emp["skills"]))
            skill_match = len(required_skills_set & emp_skills) / max(1, len(required_skills_set))

            workload = self._get_employee_workload(emp["id"])
            workload_score = max(0, 1.0 - workload * 0.15)  # penalize >6 tasks

            perf_score = self._get_employee_performance(emp["id"]) / 5.0

            exp_score = min(1.0, emp["experience"] / 10.0)

            # Slight preference for same department
            dept_bonus = 0.05 if (project_dept_id and emp["dept_id"] == project_dept_id) else 0

            final_score = (
                0.40 * skill_match +
                0.30 * workload_score +
                0.20 * perf_score +
                0.10 * exp_score +
                dept_bonus
            )

            matched_skills = list(required_skills_set & emp_skills)
            missing_skills = list(required_skills_set - emp_skills)

            results.append({
                "employee_id": emp["id"],
                "name": emp["name"],
                "position": emp["position"],
                "dept_id": emp["dept_id"],
                "score": round(final_score * 100, 1),
                "skill_match": round(skill_match * 100, 1),
                "workload": workload,
                "performance": round(perf_score * 5, 2),
                "experience": emp["experience"],
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# ──────────────────────────────────────────────────────────────
# 3. PERFORMANCE ANALYZER
# ──────────────────────────────────────────────────────────────
class PerformanceAnalyzer:
    """
    Phân tích hiệu suất từng nhân viên:
    - Tính Performance Score tổng hợp
    - Phân nhóm (High / Medium / Low)
    - Trend theo thời gian
    """

    def analyze_employee(self, employee_id: int) -> dict:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        emp = cur.fetchone()
        if not emp:
            conn.close()
            return {}

        cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='Hoàn thành' THEN 1 ELSE 0 END) as done,
                   SUM(CASE WHEN status='Đang thực hiện' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status='Chưa bắt đầu' THEN 1 ELSE 0 END) as pending
            FROM tasks WHERE assignee_id=?
        """, (employee_id,))
        task_stats = cur.fetchone()

        cur.execute("""
            SELECT AVG(quality_score) as q, AVG(effort_score) as e,
                   AVG(on_time) as ot, COUNT(*) as cnt
            FROM performance_logs WHERE employee_id=?
        """, (employee_id,))
        perf = cur.fetchone()
        conn.close()

        total = task_stats["total"] or 1
        done = task_stats["done"] or 0
        completion_rate = done / total

        q_score = perf["q"] or 3.0
        e_score = perf["e"] or 3.0
        on_time_rate = (perf["ot"] or 0.7)

        # Composite performance score (0-100)
        perf_score = (
            on_time_rate * 35 +
            (q_score / 5.0) * 35 +
            (e_score / 5.0) * 20 +
            completion_rate * 10
        )
        perf_score = round(min(100, max(0, perf_score)), 1)

        # Cluster
        if perf_score >= 70:
            cluster = "Hiệu suất cao"
            cluster_color = "#10b981"
            cluster_icon = "🏆"
        elif perf_score >= 45:
            cluster = "Hiệu suất trung bình"
            cluster_color = "#f59e0b"
            cluster_icon = "📈"
        else:
            cluster = "Cần cải thiện"
            cluster_color = "#ef4444"
            cluster_icon = "⚠️"

        # Radar scores (0-5)
        radar = {
            "Đúng hạn": round(on_time_rate * 5, 1),
            "Chất lượng": round(q_score, 1),
            "Nỗ lực": round(e_score, 1),
            "Kinh nghiệm": round(min(5, emp["experience"] / 2.0), 1),
            "Hoàn thành": round(completion_rate * 5, 1),
        }

        return {
            "employee_id": employee_id,
            "name": emp["name"],
            "position": emp["position"],
            "dept_id": emp["dept_id"],
            "performance_score": perf_score,
            "cluster": cluster,
            "cluster_color": cluster_color,
            "cluster_icon": cluster_icon,
            "radar": radar,
            "task_stats": {
                "total": task_stats["total"],
                "done": done,
                "in_progress": task_stats["in_progress"] or 0,
                "pending": task_stats["pending"] or 0,
                "completion_rate": round(completion_rate * 100, 1),
            },
            "on_time_rate": round(on_time_rate * 100, 1),
            "avg_quality": round(q_score, 2),
            "avg_effort": round(e_score, 2),
            "experience": emp["experience"],
            "skills": json.loads(emp["skills"]),
        }

    def analyze_all(self) -> list:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM employees")
        ids = [r["id"] for r in cur.fetchall()]
        conn.close()
        results = [self.analyze_employee(eid) for eid in ids]
        results.sort(key=lambda x: x.get("performance_score", 0), reverse=True)
        return results

    def department_summary(self) -> list:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM departments")
        depts = cur.fetchall()
        conn.close()

        all_employees = self.analyze_all()
        dept_map = defaultdict(list)
        for emp in all_employees:
            dept_map[emp["dept_id"]].append(emp)

        summary = []
        for d in depts:
            emps = dept_map.get(d["id"], [])
            if not emps:
                continue
            avg_score = round(sum(e["performance_score"] for e in emps) / len(emps), 1)
            high = sum(1 for e in emps if e["cluster"] == "Hiệu suất cao")
            summary.append({
                "dept_id": d["id"],
                "dept_name": d["name"],
                "dept_code": d["code"],
                "employee_count": len(emps),
                "avg_performance": avg_score,
                "high_performers": high,
                "avg_completion_rate": round(sum(e["task_stats"]["completion_rate"] for e in emps) / len(emps), 1),
            })

        return summary


# Singleton instances
deadline_predictor = DeadlinePredictor()
resource_optimizer = ResourceOptimizer()
performance_analyzer = PerformanceAnalyzer()
