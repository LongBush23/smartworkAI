"""
Các endpoint hỗ trợ ra quyết định.

Mọi mô hình chạy TẠI CHỖ, không gọi ra ngoài. Xem ràng buộc đầy đủ ở
`backend/services/ai/__init__.py`.

Không endpoint nào ở đây được ghi vào `kpi_evaluations.approval` — điểm KPI chỉ
do cấp có thẩm quyền xác định theo công thức của Hướng dẫn 20-HD/ĐUCA.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import require_leader_or_above, require_director_or_above, require_admin
from backend.security import get_current_user
from backend.services import so_dang_ky_mo_hinh
from backend.services.ai import anomaly, assignment, guideline, risk

router = APIRouter()


# ================= SỔ ĐĂNG KÝ MÔ HÌNH =================

@router.get("/models")
async def models(current_user: dict = Depends(require_leader_or_above)):
    """
    Toàn bộ mô hình của hệ thống: mục đích, thuật toán, lý do chọn thuật toán,
    tham số đang dùng, và chất lượng thực tế của hai mô hình hồi quy.

    CHỈ ĐỌC. Khác `POST /retrain`, endpoint này không huấn luyện lại mô hình mà
    cả đơn vị đang dùng — mở trang xem không được làm đổi thứ đang chạy.
    """
    return await so_dang_ky_mo_hinh.danh_sach()


@router.get("/tom-tat")
async def tom_tat(current_user: dict = Depends(get_current_user)):
    """
    Dải "AI đang hỗ trợ đồng chí" trên Trang chủ.

    Mọi cán bộ đã đăng nhập đều gọi được; số thẻ trả về thay đổi theo chức vụ,
    đúng bằng phạm vi của các endpoint sinh ra từng con số.
    """
    return await so_dang_ky_mo_hinh.tom_tat_ho_tro(current_user)


def _scope_department(current_user: dict, department_id: Optional[str]) -> Optional[str]:
    """
    Giới hạn phạm vi xem theo chức vụ, giống quy tắc ở trang Nhiệm vụ:
    lãnh đạo, chỉ huy chỉ thấy đơn vị mình; quản trị hệ thống thấy toàn bộ.
    """
    if current_user.get("role") == "admin":
        return department_id
    return department_id or current_user.get("department_id")


# ================= MÔ HÌNH 1: GỢI Ý PHÂN CÔNG =================

@router.get("/suggest-assignee")
async def suggest_assignee(
    classification: str = Query("thuong", description="Độ mật của nhiệm vụ sắp giao"),
    complexity_group: Optional[int] = Query(None, ge=1, le=3),
    product: Optional[str] = None,
    department_id: Optional[str] = None,
    period_month: Optional[int] = Query(None, ge=1, le=12),
    period_year: Optional[int] = None,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(require_leader_or_above),
):
    """Gợi ý cán bộ phù hợp để giao một nhiệm vụ. Chỉ tham khảo, không quyết định."""
    # Khác các endpoint cảnh báo: gợi ý phân công luôn gắn với MỘT đơn vị cụ thể,
    # nên kể cả quản trị hệ thống cũng phải có đơn vị để xét.
    dept = department_id or current_user.get("department_id")
    if not dept:
        raise HTTPException(
            status_code=400,
            detail="Cần chỉ rõ đơn vị để gợi ý cán bộ (tham số department_id)",
        )

    return await assignment.suggest(
        department_id=dept,
        classification=classification,
        complexity_group=complexity_group,
        product=product,
        period_month=period_month,
        period_year=period_year,
        limit=limit,
    )


# ================= MÔ HÌNH 2: CẢNH BÁO SỚM =================

@router.get("/risk/officers")
async def risk_officers(
    department_id: Optional[str] = None,
    period_month: Optional[int] = Query(None, ge=1, le=12),
    period_year: Optional[int] = None,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    current_user: dict = Depends(require_leader_or_above),
):
    """Cán bộ có nguy cơ rơi Nhóm 3 khi kết thúc kỳ."""
    return await risk.predict_officer_risk(
        department_id=_scope_department(current_user, department_id),
        period_month=period_month,
        period_year=period_year,
        threshold=threshold,
    )


@router.get("/risk/tasks")
async def risk_tasks(
    department_id: Optional[str] = None,
    period_month: Optional[int] = Query(None, ge=1, le=12),
    period_year: Optional[int] = None,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    current_user: dict = Depends(require_leader_or_above),
):
    """Nhiệm vụ đang mở có nguy cơ trễ hạn."""
    return await risk.predict_task_risk(
        department_id=_scope_department(current_user, department_id),
        period_month=period_month,
        period_year=period_year,
        threshold=threshold,
    )


@router.post("/retrain")
async def retrain(current_user: dict = Depends(require_admin)):
    """
    Huấn luyện lại các mô hình dự báo.

    Trả về AUC và ma trận nhầm lẫn để người quản trị tự thẩm định chất lượng,
    thay vì tin vào một con số đẹp.
    """
    return await risk.retrain_all()


# ================= MÔ HÌNH 3: PHÁT HIỆN CHẤM HÌNH THỨC =================

@router.get("/anomalies")
async def anomalies(
    period_month: int = Query(..., ge=1, le=12),
    period_year: int = Query(...),
    department_id: Optional[str] = None,
    current_user: dict = Depends(require_director_or_above),
):
    """
    Dấu hiệu chấm điểm hình thức cần rà soát.

    Chỉ dành cho lãnh đạo đơn vị trở lên. Đây là dấu hiệu để xem lại,
    không phải kết luận vi phạm.
    """
    return await anomaly.detect(
        period_month=period_month,
        period_year=period_year,
        department_id=_scope_department(current_user, department_id),
    )


# ================= MÔ HÌNH 4: TRA CỨU HƯỚNG DẪN =================

@router.get("/guideline/search")
async def guideline_search(
    q: str = Query(..., min_length=2, description="Câu hỏi về cách tính điểm"),
    current_user: dict = Depends(get_current_user),
):
    """
    Tra cứu Hướng dẫn 20-HD/ĐUCA.

    Mọi cán bộ đều dùng được. Câu trả lời về số lấy trực tiếp từ hằng số của bộ
    máy chấm điểm nên luôn khớp với điều hệ thống thực sự tính.
    """
    return guideline.answer(q)


@router.get("/guideline/clauses")
async def guideline_clauses(current_user: dict = Depends(get_current_user)):
    """Toàn bộ điều khoản đã lập chỉ mục, để hiển thị danh sách tra cứu."""
    return [
        {k: v for k, v in c.items() if k != "keywords"}
        for c in guideline.CLAUSES
    ]
