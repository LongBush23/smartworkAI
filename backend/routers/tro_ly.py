"""
Endpoint trợ lý hội thoại.

Chỉ đọc dữ liệu, phạm vi đúng bằng phân quyền người hỏi. Xem rào chắn đầy đủ ở
backend/services/tro_ly/__init__.py.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.security import get_current_user
from backend.services.tro_ly import gemini

router = APIRouter()


class LuotTruoc(BaseModel):
    vai: str = Field(description="'user' hoặc 'model'")
    text: str


class CauHoi(BaseModel):
    cau_hoi: str = Field(min_length=1, max_length=1000)
    lich_su: Optional[List[LuotTruoc]] = None


@router.post("/hoi")
async def hoi_tro_ly(body: CauHoi, current_user: dict = Depends(get_current_user)):
    """
    Hỏi trợ lý. Mọi cán bộ đã đăng nhập đều dùng được; dữ liệu trả về giới hạn
    đúng theo phân quyền của chính người hỏi.
    """
    return await gemini.hoi(
        cau_hoi=body.cau_hoi,
        lich_su=[l.model_dump() for l in (body.lich_su or [])],
        nguoi_hoi=current_user,
    )


@router.get("/trang-thai")
async def trang_thai(current_user: dict = Depends(get_current_user)):
    """Cho giao diện biết đang chạy chế độ nào để hiển thị cho trung thực."""
    return {
        "che_do": "llm" if gemini.san_sang() else "tai_cho",
        "mo_ta": (
            "Trợ lý hội thoại có kết nối mô hình ngôn ngữ"
            if gemini.san_sang()
            else "Chưa cấu hình khoá — đang dùng máy tra cứu tại chỗ"
        ),
    }
