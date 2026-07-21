from backend.database import db
from bson import ObjectId
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import random

async def predict_project_deadline(project_id: str):
    """
    AI 1: Deadline Predictor (Monte Carlo Simulation)
    Dự báo xác suất hoàn thành đúng hạn bằng cách chạy mô phỏng 1000 kịch bản tương lai
    dựa trên tiến độ hiện tại, số lượng task, và độ khó dự kiến.
    """
    pipeline = [
        {"$match": {"_id": ObjectId(project_id)}},
        {"$addFields": {"id_str": {"$toString": "$_id"}}},
        {"$lookup": {
            "from": "tasks",
            "localField": "id_str",
            "foreignField": "project_id",
            "as": "tasks"
        }}
    ]
    cursor = db.projects.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        return None
        
    project = result[0]
    tasks = project.get("tasks", [])
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get("status") == "done"])
    
    end_date = project.get("end_date")
    if not end_date:
        return None
    days_left = (end_date - datetime.utcnow()).days
    
    if total_tasks == 0:
        probability = 100
    elif completed_tasks == total_tasks:
        probability = 100
    elif days_left <= 0:
        probability = 0
    else:
        # MONTE CARLO SIMULATION
        # Tính toán vận tốc (Burn rate) lịch sử
        # Giả sử trung bình mỗi ngày team làm được X task.
        historical_velocity = project.get("historical_score", 50) / 100.0 # Factor từ 0 -> 1
        base_daily_capacity = 1.0 + historical_velocity # Team làm được 1 - 2 task/ngày tùy điểm
        
        remaining_tasks = total_tasks - completed_tasks
        
        simulations = 1000
        success_count = 0
        
        for _ in range(simulations):
            # Biến động năng suất hàng ngày (Variance)
            # Dùng phân phối chuẩn (Normal Distribution) để giả lập sự cố (ốm đau, review chậm...)
            simulated_days = 0
            tasks_to_do = remaining_tasks
            
            while tasks_to_do > 0:
                # Năng suất ngày hôm nay (có thể bằng 0 nếu xui xẻo)
                daily_work = max(0, np.random.normal(base_daily_capacity, 0.5))
                tasks_to_do -= daily_work
                simulated_days += 1
                
                # Cắt sớm để tối ưu nếu đã vượt quá số ngày còn lại
                if simulated_days > days_left:
                    break
            
            if simulated_days <= days_left:
                success_count += 1
                
        probability = (success_count / simulations) * 100

    project["_id"] = str(project["_id"])
    return {
        "name": project["name"],
        "progress": project["progress"],
        "days_left": days_left,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_probability": probability
    }

async def optimize_resources(task_id: str):
    """
    AI 2: Resource Optimizer (NLP - TF-IDF & Cosine Similarity)
    Gợi ý nhân sự bằng cách "đọc hiểu" mô tả công việc và khớp với kỹ năng nhân viên.
    """
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        return []

    # Nội dung công việc để đem đi so sánh
    task_text = f"{task.get('title', '')} {task.get('description', '')}"

    # Lấy toàn bộ nhân viên (role: staff)
    cursor = db.users.find({"role": "staff"})
    employees = await cursor.to_list(length=100)
    
    if not employees or not task_text.strip():
        return {"task_id": task_id, "top_candidates": []}

    # Gom kỹ năng của từng nhân viên thành các đoạn văn bản (documents)
    employee_docs = []
    for emp in employees:
        skills = emp.get("skills", [])
        parsed_skills = []
        if isinstance(skills, list):
            for s in skills:
                if isinstance(s, dict):
                    parsed_skills.append(s.get("skill_name", ""))
                else:
                    parsed_skills.append(str(s))
        else:
            parsed_skills.append(str(skills))
            
        skills_text = " ".join(parsed_skills)
        employee_docs.append(skills_text)
        # Ghi đè lại field skills thành dạng string array để frontend dễ hiển thị
        emp["parsed_skills"] = parsed_skills
        
    # Tạo Model Vector hóa từ vựng (NLP)
    # Fit cả task_text và employee_docs để xây bộ từ vựng chung
    vectorizer = TfidfVectorizer()
    all_texts = [task_text] + employee_docs
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        # Vector của task nằm ở index 0
        task_vector = tfidf_matrix[0:1]
        # Vectors của nhân viên nằm từ index 1 trở đi
        employee_vectors = tfidf_matrix[1:]
        
        # Tính toán độ tương đồng Cosine (Cosine Similarity)
        similarities = cosine_similarity(task_vector, employee_vectors).flatten()
    except ValueError:
        # Lỗi khi không có từ nào có nghĩa (vd: text rỗng hoặc toàn dấu cách)
        similarities = np.zeros(len(employees))

    # Tính điểm Fit Score cuối cùng = (NLP Similarity * 100) - (Khối lượng task đang ôm * 5)
    candidates = []
    for idx, emp in enumerate(employees):
        nlp_score = similarities[idx] * 100
        current_workload = emp.get("current_workload", 0)
        
        # Kết hợp thuật toán ML và logic nghiệp vụ
        fit_score = nlp_score - (current_workload * 5)
        
        candidates.append({
            "_id": str(emp["_id"]),
            "name": emp.get("name"),
            "skills": emp.get("parsed_skills", []),
            "current_workload": current_workload,
            "nlp_similarity": nlp_score,
            "fit_score": fit_score
        })
        
    # Sắp xếp từ cao xuống thấp
    candidates.sort(key=lambda x: x["fit_score"], reverse=True)
    
    # Lấy Top 3
    return {"task_id": task_id, "top_candidates": candidates[:3]}

async def analyze_performance():
    """
    AI 3: Performance Analyzer (Unsupervised Learning - K-Means Clustering)
    Phân tích điểm hiệu suất và tự động gom cụm nhân sự thành 3 nhóm (K-Means)
    """
    # Bước 1: Tính toán các chỉ số cơ bản từ DB
    pipeline = [
        {"$match": {"role": "staff"}},
        {"$addFields": {"id_str": {"$toString": "$_id"}}},
        {"$lookup": {
            "from": "performance_logs",
            "localField": "id_str",
            "foreignField": "employee_id",
            "as": "logs"
        }}
    ]
    cursor = db.users.aggregate(pipeline)
    employees = await cursor.to_list(length=100)
    
    if not employees:
        return []
        
    data_points = []
    for emp in employees:
        logs = emp.get("logs", [])
        total_logs = len(logs)
        if total_logs > 0:
            on_time_count = sum(1 for log in logs if log.get("on_time", False))
            on_time_rate = on_time_count / total_logs
            avg_quality = sum(log.get("quality", 0) for log in logs) / total_logs
        else:
            # Nếu chưa có log nào, lấy điểm mặc định
            on_time_rate = 0.5
            avg_quality = emp.get("quality_score", 50)
            
        # Feature vector 3 chiều: [Tỷ lệ đúng hạn, Điểm chất lượng, Số lượng hoàn thành]
        features = [on_time_rate * 100, avg_quality, total_logs * 10] 
        data_points.append(features)
        
        # Gắn tạm features vào obj để xài sau
        emp["ml_features"] = features
        emp["performance_score"] = (on_time_rate * 40) + (avg_quality * 0.6)

    # Bước 2: Chạy thuật toán K-Means Clustering (Phân thành 3 cụm)
    # Phải có ít nhất 3 người để chia 3 cụm
    n_clusters = min(3, len(data_points))
    
    if n_clusters > 1:
        X = np.array(data_points)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(X)
        labels = kmeans.labels_
        
        # Xác định ý nghĩa của từng cụm dựa vào điểm trung bình (centroid)
        # Sắp xếp các cụm theo tổng điểm từ cao xuống thấp để gán nhãn Giỏi/Khá/Kém
        centroids = kmeans.cluster_centers_
        cluster_scores = [sum(centroid) for centroid in centroids]
        
        # Tạo mapping từ label gốc sang rank (0: cao nhất, 1: nhì, 2: bét)
        sorted_indices = np.argsort(cluster_scores)[::-1]
        rank_mapping = {original_label: rank for rank, original_label in enumerate(sorted_indices)}
        
        cluster_names = ["Giỏi", "Khá", "Kém"]
        
        for idx, emp in enumerate(employees):
            original_label = labels[idx]
            rank = rank_mapping[original_label]
            emp["cluster"] = cluster_names[rank] if rank < len(cluster_names) else "Khác"
    else:
        # Fallback nếu công ty có < 3 người
        for emp in employees:
            emp["cluster"] = "Khá"
            
    # Format lại kết quả đầu ra
    results = []
    for emp in employees:
        results.append({
            "_id": str(emp["_id"]),
            "name": emp["name"],
            "performance_score": emp["performance_score"],
            "cluster": emp["cluster"],
            "total_logs": emp["ml_features"][2] / 10 # Trả lại scale gốc
        })
        
    # Sort theo điểm
    results.sort(key=lambda x: x["performance_score"], reverse=True)
    return results

async def workload_analysis():
    """
    Phân tích Workload hiện tại của toàn bộ nhân viên.
    Trả về danh sách nhân viên cùng với số giờ làm việc, và dự đoán Burnout (Quá tải).
    """
    cursor = db.users.find({"role": "staff"})
    employees = await cursor.to_list(length=100)
    
    results = []
    for emp in employees:
        ai_metrics = emp.get("ai_metrics", {})
        capacity = ai_metrics.get("capacity_hours_per_week", 40)
        current = ai_metrics.get("current_workload_hours", 0)
        
        # Burnout risk calculation
        workload_ratio = current / capacity if capacity > 0 else 1
        burnout_risk = "Thấp"
        risk_score = workload_ratio * 100
        
        if risk_score > 120:
            burnout_risk = "Nguy hiểm (Quá tải nghiêm trọng)"
        elif risk_score > 90:
            burnout_risk = "Cao (Cần giảm tải)"
        elif risk_score < 40:
            burnout_risk = "Rảnh rỗi (Có thể nhận thêm)"
            
        results.append({
            "_id": str(emp["_id"]),
            "name": emp["name"],
            "capacity": capacity,
            "current_workload": current,
            "utilization_percent": round(risk_score, 1),
            "burnout_risk": burnout_risk
        })
        
    results.sort(key=lambda x: x["utilization_percent"], reverse=True)
    return results
