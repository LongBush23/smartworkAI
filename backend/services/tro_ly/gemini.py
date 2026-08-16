"""
Gọi Gemini kèm vòng gọi công cụ.

Dùng REST trực tiếp qua httpx (đã có sẵn trong requirements) thay vì thêm SDK —
một endpoint, không cần kéo thêm phụ thuộc vào bản triển khai.

Thiếu khoá hoặc gọi hỏng thì lui về máy tra cứu tại chỗ, người dùng vẫn có câu
trả lời chứ không gặp màn hình lỗi.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.services.ai import guideline
from backend.services.tro_ly.cong_cu import KHAI_BAO, goi_cong_cu

log = logging.getLogger(__name__)

GOC = "https://generativelanguage.googleapis.com/v1beta/models"
SO_VONG_TOI_DA = 4          # đủ cho 2-3 lượt gọi công cụ rồi chốt câu trả lời
HET_HAN_GIAY = 30

CHI_DAN = """\
Bạn là trợ lý của Hệ thống tính điểm KPI trong Công an nhân dân, xây dựng theo
Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026.

CÁCH TRẢ LỜI
- Trả lời bằng tiếng Việt, văn phong hành chính, ngắn gọn, đi thẳng vào việc.
- Xưng hô trung tính: gọi người dùng là "đồng chí" nếu cần.
- Trình bày số liệu rõ ràng; nhiều dòng thì dùng gạch đầu dòng.

BỐN QUY TẮC BẮT BUỘC
1. Chỉ nói những gì công cụ trả về. Tuyệt đối không bịa số liệu, không suy đoán.
   Không có dữ liệu thì nói thẳng là không có.
2. Mọi câu hỏi về cách tính điểm, mức phần trăm, ngưỡng xếp loại, công thức đều
   PHẢI gọi công cụ tra_cuu_huong_dan và lấy đúng con số nó trả về. Không tự tính,
   không nhớ theo trí nhớ của mình.
3. Nhiệm vụ có độ mật chỉ được nói SỐ LƯỢNG. Không đoán, không bịa, không suy ra
   tên hay nội dung của chúng dù người dùng có hỏi gặng.
4. Bạn chỉ tra cứu và diễn đạt. Bạn không giao việc, không nhắc nhở, không chấm
   điểm, không quyết định xếp loại. Ai hỏi những việc đó thì hướng dẫn họ thao tác
   trên giao diện.

Người dùng hiện tại: {ten}, {vai}{don_vi}.
"""

NHAN_VAI = {
    "admin": "quản trị hệ thống, xem được toàn bộ dữ liệu",
    "director": "lãnh đạo đơn vị, xem được dữ liệu trong đơn vị mình",
    "leader": "lãnh đạo, chỉ huy, xem được dữ liệu trong đơn vị mình",
    "staff": "cán bộ, chỉ xem được dữ liệu của chính mình",
}


def san_sang() -> bool:
    return bool(GEMINI_API_KEY)


def _chi_dan(nguoi_hoi: dict) -> str:
    vai = nguoi_hoi.get("role", "staff")
    don_vi = f", thuộc đơn vị mã {nguoi_hoi.get('department_id')}" if nguoi_hoi.get("department_id") else ""
    return CHI_DAN.format(
        ten=nguoi_hoi.get("name") or nguoi_hoi.get("username") or "cán bộ",
        vai=NHAN_VAI.get(vai, vai),
        don_vi=don_vi,
    )


async def _goi_api(client: httpx.AsyncClient, noi_dung: List[dict], chi_dan: str) -> dict:
    """
    Gọi một lượt. Gói miễn phí hay trả 429 (quá hạn mức) và 503 (quá tải) nhất
    thời, nên thử lại một lần trước khi bỏ cuộc — đỡ lui về máy tại chỗ oan.
    """
    than = {
        "system_instruction": {"parts": [{"text": chi_dan}]},
        "contents": noi_dung,
        "tools": [{"function_declarations": KHAI_BAO}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200},
    }
    for lan in range(2):
        r = await client.post(
            f"{GOC}/{GEMINI_MODEL}:generateContent",
            params={"key": GEMINI_API_KEY}, json=than,
        )
        if r.status_code in (429, 503) and lan == 0:
            await asyncio.sleep(1.5)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return r.json()


def _lui_ve_tai_cho(cau_hoi: str, ly_do: str) -> dict:
    """Trả lời bằng máy tra cứu tại chỗ khi không dùng được Gemini."""
    kq = guideline.answer(cau_hoi)
    rule = kq.get("rule_answer")
    if rule:
        loi = f"{rule['answer']}. {rule['detail']}"
    elif kq.get("clauses"):
        loi = ("Chưa nhận diện được câu hỏi. Điều khoản liên quan nhất: "
               + kq["clauses"][0]["title"])
    else:
        loi = "Chưa tra được nội dung phù hợp trong Hướng dẫn 20-HD/ĐUCA."
    return {
        "tra_loi": loi,
        "dieu_khoan": kq.get("clauses", [])[:2],
        "cong_cu_da_dung": ["tra_cuu_huong_dan"],
        "che_do": "tai_cho",
        "ghi_chu": ly_do,
    }


async def hoi(cau_hoi: str, lich_su: Optional[List[dict]], nguoi_hoi: dict) -> Dict[str, Any]:
    """
    Hỏi trợ lý. `lich_su` là các lượt trước dạng [{"vai": "user"|"model", "text": ...}].
    """
    if not san_sang():
        return _lui_ve_tai_cho(cau_hoi, "Chưa cấu hình GEMINI_API_KEY, đang dùng máy tra cứu tại chỗ.")

    noi_dung: List[dict] = []
    for luot in (lich_su or [])[-6:]:
        vai = "model" if luot.get("vai") == "model" else "user"
        noi_dung.append({"role": vai, "parts": [{"text": luot.get("text", "")}]})
    noi_dung.append({"role": "user", "parts": [{"text": cau_hoi}]})

    da_dung: List[str] = []
    chi_dan = _chi_dan(nguoi_hoi)

    try:
        async with httpx.AsyncClient(timeout=HET_HAN_GIAY) as client:
            for _ in range(SO_VONG_TOI_DA):
                data = await _goi_api(client, noi_dung, chi_dan)

                ung_vien = (data.get("candidates") or [{}])[0]
                khoi_model = ung_vien.get("content") or {}
                phan = khoi_model.get("parts") or []

                goi = [p["functionCall"] for p in phan if "functionCall" in p]
                if not goi:
                    van_ban = "".join(p.get("text", "") for p in phan).strip()
                    if not van_ban:
                        return _lui_ve_tai_cho(cau_hoi, "Mô hình không trả về nội dung.")
                    return {
                        "tra_loi": van_ban,
                        "dieu_khoan": [],
                        "cong_cu_da_dung": da_dung,
                        "che_do": "llm",
                        "ghi_chu": None,
                    }

                # Trả lại NGUYÊN KHỐI mà mô hình vừa gửi, không dựng lại phần
                # functionCall. Gemini 3.x kèm `thoughtSignature` trong đó và bắt
                # buộc phải echo lại y nguyên; dựng lại tay là mất chữ ký, API
                # trả 400 "Function call is missing a thought_signature".
                noi_dung.append({**khoi_model, "role": "model"})
                tra_ve = []
                for g in goi:
                    ten = g.get("name", "")
                    kq = await goi_cong_cu(ten, g.get("args") or {}, nguoi_hoi)
                    da_dung.append(ten)
                    tra_ve.append({"functionResponse": {"name": ten, "response": kq}})
                noi_dung.append({"role": "user", "parts": tra_ve})

        return _lui_ve_tai_cho(cau_hoi, "Mô hình gọi công cụ quá nhiều vòng mà chưa chốt câu trả lời.")

    except httpx.HTTPStatusError as e:
        log.warning("Gemini trả lỗi %s: %s", e.response.status_code, e.response.text[:300])
        return _lui_ve_tai_cho(cau_hoi, f"Dịch vụ trả lỗi {e.response.status_code}.")
    except Exception as e:  # mạng chậm, hết hạn, JSON lạ…
        log.warning("Gọi Gemini hỏng: %s", e)
        return _lui_ve_tai_cho(cau_hoi, "Không gọi được dịch vụ, đang dùng máy tra cứu tại chỗ.")
