"""
Projection MongoDB dùng chung cho các mô hình.

VÌ SAO CẦN
----------
Một bản ghi `kpi_evaluations` nặng khoảng **17 KB** vì lưu kèm toàn bộ danh sách
nhiệm vụ, mức chất lượng, tiến độ của từng việc trong kỳ. Các mô hình chỉ cần
vài con số: mã cán bộ, kỳ, điểm KPI, nhóm xếp loại.

Lấy nguyên bản ghi cho 390 kỳ đã duyệt nghĩa là tải **6,8 MB** từ cơ sở dữ liệu
về mỗi lần gọi API. Đo trên bản triển khai dùng MongoDB Atlas (cơ sở dữ liệu ở
xa): endpoint cảnh báo sớm mất **5,4 giây**, trong đó **5,17 giây là nằm chờ
socket đọc dữ liệu** — không có giây nào là tính toán mô hình.

Thêm projection đưa cùng truy vấn đó từ 2,49 giây xuống 0,195 giây.

QUY TẮC
-------
Mọi truy vấn `.find()` trả về nhiều bản ghi trong `backend/services/ai/` PHẢI có
projection. Không có ngoại lệ: cơ sở dữ liệu ở xa nên khối lượng truyền tải là
thứ quyết định tốc độ, không phải thuật toán.
"""

# Đủ để dựng lịch sử KPI và nhãn Nhóm 3
KPI_TOI_THIEU = {
    "target_id": 1,
    "department_id": 1,
    "period_month": 1,
    "period_year": 1,
    "approval.kpi_score": 1,
    "approval.kpi_group": 1,
}

# Thêm những trường mà việc rà soát chấm điểm hình thức cần
KPI_RA_SOAT = {
    **KPI_TOI_THIEU,
    "target_name": 1,
    "general_criteria.total_E": 1,
    "self_evaluation.proposed_rating": 1,
}

# Đặc trưng của nhiệm vụ. Cố ý KHÔNG lấy description, file_reference,
# file_location — vừa nặng, vừa là trường bị che theo cấp độ tiếp cận.
NHIEM_VU_DAC_TRUNG = {
    "assigned_to": 1,
    "department_id": 1,
    "period_month": 1,
    "period_year": 1,
    "status": 1,
    "deadline": 1,
    "kpi_point": 1,
    "complexity_group": 1,
    "quantity_assigned": 1,
    "quantity_completed": 1,
    "revision_count": 1,
    "reminder_count": 1,
    "actual_end": 1,
    "classification": 1,
}
