"""
Kiểm thử rào chắn của trợ lý hội thoại.

Không gọi mạng, không cần cơ sở dữ liệu thật. Trọng tâm là bốn rào chắn nêu ở
backend/services/tro_ly/__init__.py — đây là phần nếu hỏng thì hậu quả nặng
nhất, nặng hơn nhiều so với việc trợ lý trả lời kém.
"""
import inspect
import pathlib

import pytest

from backend.services.tro_ly import cong_cu, gemini


# ================= RÀO 3: KHÔNG LỘ NHIỆM VỤ CÓ ĐỘ MẬT =================

def _viec(ten, do_mat="thuong"):
    return {"title": ten, "code": "NV-2026-08-0001", "classification": do_mat,
            "kpi_point": 50, "status": "done", "deadline": None}


def test_loc_bo_moi_nhiem_vu_co_do_mat():
    """Mọi độ mật khác 'thường' đều phải bị lược, chỉ còn lại con số."""
    ds = [_viec("Việc thường"), _viec("Việc mật", "mat"),
          _viec("Việc tối mật", "toi_mat"), _viec("Việc tuyệt mật", "tuyet_mat")]
    an_toan, so_mat = cong_cu.loc_mat(ds, {"role": "admin", "clearance_level": 3})
    assert so_mat == 3
    assert [t["title"] for t in an_toan] == ["Việc thường"]


def test_khong_lo_viec_mat_ke_ca_khi_du_cap_do_tiep_can():
    """
    Người hỏi xem được trên giao diện là một chuyện; đưa ra dịch vụ bên ngoài
    là chuyện khác. Quản trị hệ thống tiếp cận Tuyệt mật vẫn không được lộ tên.
    """
    quan_tri = {"role": "admin", "clearance_level": 3}
    an_toan, so_mat = cong_cu.loc_mat([_viec("Chuyên đề A1", "tuyet_mat")], quan_tri)
    assert an_toan == []
    assert so_mat == 1


def test_moi_cong_cu_tra_ve_nhiem_vu_deu_phai_loc_mat():
    """Chốt bằng mã nguồn: hàm `nhiem_vu` bắt buộc đi qua loc_mat."""
    assert "loc_mat(" in inspect.getsource(cong_cu.nhiem_vu)


# ================= RÀO 4: PHẠM VI ĐÚNG BẰNG PHÂN QUYỀN =================

@pytest.mark.parametrize("vai,mong_doi", [
    ("staff", {"assigned_to": "u1"}),
    ("leader", {"department_id": "d1"}),
    ("director", {"department_id": "d1"}),
    ("admin", {}),
])
def test_pham_vi_nhiem_vu_theo_vai(vai, mong_doi):
    nguoi = {"_id": "u1", "role": vai, "department_id": "d1"}
    assert cong_cu._pham_vi_nhiem_vu(nguoi) == mong_doi


def test_can_bo_khong_giu_chuc_vu_khong_co_department_van_bi_bo_ve_chinh_minh():
    """Thiếu department_id thì không được rơi vào phạm vi rỗng (= thấy tất cả)."""
    assert cong_cu._pham_vi_nhiem_vu({"_id": "u9", "role": "staff"}) == {"assigned_to": "u9"}
    assert cong_cu._pham_vi_nhiem_vu({"_id": "u9", "role": "leader"}) == {"assigned_to": "u9"}


@pytest.mark.asyncio
@pytest.mark.parametrize("ham", [cong_cu.tong_quan_don_vi, cong_cu.can_bo_can_luu_y])
async def test_cong_cu_toan_don_vi_tu_choi_can_bo_thuong(ham):
    kq = await ham({"_id": "u1", "role": "staff", "department_id": "d1"})
    assert "tu_choi" in kq


# ================= RÀO 1: CHỈ ĐỌC =================

def test_khong_cong_cu_nao_ghi_co_so_du_lieu():
    """Quét mã: không được có insert/update/delete trong gói trợ lý."""
    goi = pathlib.Path(cong_cu.__file__).parent
    cam = ("insert_one", "insert_many", "update_one", "update_many",
           "delete_one", "delete_many", "find_one_and_update", "replace_one")
    for f in goi.glob("*.py"):
        src = f.read_text()
        for tu in cam:
            assert tu not in src, f"{f.name} có thao tác ghi: {tu}"


# ================= RÀO 2: SỐ LIỆU LẤY TỪ BỘ MÁY CHẤM ĐIỂM =================

@pytest.mark.asyncio
async def test_tra_cuu_huong_dan_lay_so_tu_bo_may_cham_diem():
    """Con số phải khớp hằng số của kpi_service, không do mô hình tự suy."""
    from backend.services.kpi_service import get_quality_percent
    kq = await cong_cu.tra_cuu_huong_dan({"role": "staff"}, "sửa 3 lần")
    assert kq["tra_loi_chinh_xac"]["value_percent"] == get_quality_percent("fair_2_4") * 100


def test_chi_dan_nhac_lai_du_bon_rao_chan():
    """Lời nhắc gửi mô hình phải nêu đủ bốn ràng buộc, không được cắt bớt."""
    c = gemini.CHI_DAN
    assert "không bịa" in c.lower()
    assert "tra_cuu_huong_dan" in c
    assert "độ mật" in c
    assert "không chấm" in c.lower() or "không quyết định" in c.lower()


# ================= LUI VỀ MÁY TẠI CHỖ =================

def test_thieu_khoa_thi_lui_ve_tai_cho_chu_khong_hong():
    kq = gemini._lui_ve_tai_cho("nhắc nhở 2 lần được bao nhiêu điểm", "thử")
    assert kq["che_do"] == "tai_cho"
    assert "50%" in kq["tra_loi"]


# ================= GIỮ NGUYÊN RÀNG BUỘC CỦA services/ai =================

def test_goi_services_ai_van_khong_goi_mang():
    """
    Trợ lý được phép gọi ra ngoài, nhưng 04 mô hình ra quyết định thì KHÔNG.
    Test này giữ ranh giới đó khỏi bị xoá nhoà khi thêm trợ lý.
    """
    thu_muc = pathlib.Path(cong_cu.__file__).parent.parent / "ai"
    cam = ("httpx", "requests", "openai", "google.generativeai", "aiohttp")
    for f in thu_muc.glob("*.py"):
        src = f.read_text()
        for lib in cam:
            assert f"import {lib}" not in src, f"{f.name} import {lib}"
            assert f"from {lib}" not in src, f"{f.name} import từ {lib}"
