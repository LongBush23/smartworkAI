"""
Kiểm thử các mô hình hỗ trợ ra quyết định.

Chạy:  pytest backend/test_ai.py -v

Không cần cơ sở dữ liệu thật — dùng CSDL giả trong bộ nhớ để dựng đúng tình
huống cần kiểm tra.
"""
from datetime import datetime, timedelta

import pytest

from backend.services.ai import anomaly, guideline


# ================= CSDL GIẢ =================

class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *a, **kw):
        return self

    async def to_list(self, length=None):
        return list(self._docs)


def _matches(doc, query):
    for key, cond in (query or {}).items():
        val = doc.get(key)
        if isinstance(cond, dict):
            if "$in" in cond and val not in cond["$in"]:
                return False
            if "$ne" in cond and val == cond["$ne"]:
                return False
        elif val != cond:
            return False
    return True


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find(self, query=None, projection=None):
        return FakeCursor([d for d in self.docs if _matches(d, query)])


class FakeDB:
    def __init__(self, **collections):
        for name, docs in collections.items():
            setattr(self, name, FakeCollection(docs))

    def __getattr__(self, name):
        return FakeCollection([])


def make_eval(target_id, name, dept, month, kpi, group, total_e=25.0,
              proposed=None, year=2026):
    return {
        "target_id": target_id,
        "target_name": name,
        "department_id": dept,
        "evaluation_type": "individual",
        "period_type": "monthly",
        "period_month": month,
        "period_year": year,
        "overall_status": "approved",
        "approval": {"kpi_score": kpi, "kpi_group": group},
        "general_criteria": {"total_E": total_e},
        **({"self_evaluation": {"proposed_rating": proposed}} if proposed else {}),
    }


# ================= MÁY QUY TẮC TRA CỨU HƯỚNG DẪN =================

@pytest.mark.parametrize("question,expected", [
    ("Sửa 3 lần thì được bao nhiêu phần trăm?", 50),
    ("chinh sua 1 lan tinh bao nhieu %", 75),
    ("Chỉnh sửa 2 lần", 50),
    ("Chỉnh sửa 4 lần", 50),
    ("Chỉnh sửa 5 lần", 25),
    ("Chỉnh sửa 6 lần?", 25),
    ("Phải sửa 8 lần thì sao", 0),
    ("Không phải sửa lần nào", 100),
    ("Nhắc nhở 1 lần", 75),
    ("Nhắc nhở 2 lần được bao nhiêu điểm?", 50),
    ("Nhắc nhở 3 lần", 25),
    ("Nhắc nhở 4 lần", 0),
    ("nhac nho 7 lan", 0),
    ("Không bị nhắc nhở", 100),
    ("đúng hạn thì tính bao nhiêu", 100),
])
def test_may_quy_tac_tra_dung_muc_diem(question, expected):
    """Câu trả lời phải khớp đúng bảng mức trong Hướng dẫn."""
    result = guideline.try_rule_engine(question)
    assert result is not None, f"Không nhận diện được: {question}"
    assert result["value_percent"] == expected


@pytest.mark.parametrize("kpi,expected_group", [
    (100, "Nhóm 1"), (85, "Nhóm 1"), (70, "Nhóm 1"),
    (69, "Nhóm 2"), (62, "Nhóm 2"), (50, "Nhóm 2"),
    (49, "Nhóm 3"), (40, "Nhóm 3"), (0, "Nhóm 3"),
])
def test_may_quy_tac_phan_nhom(kpi, expected_group):
    result = guideline.try_rule_engine(f"KPI {kpi} thuộc nhóm mấy")
    assert result is not None
    assert expected_group in result["answer"]


def test_cau_tra_loi_khop_hang_so_cua_bo_may_cham_diem():
    """
    Điểm mấu chốt: câu trả lời tra cứu phải lấy từ CÙNG hằng số mà hệ thống
    dùng để chấm điểm, không phải bảng chép tay riêng.
    """
    from backend.services.kpi_service import get_quality_percent, get_timeline_percent

    for n, tier in [(0, "good"), (1, "fair_1"), (3, "fair_2_4"), (5, "poor_5_6"), (9, "fail_7")]:
        answer = guideline.try_rule_engine(f"sửa {n} lần")
        assert answer["value_percent"] == get_quality_percent(tier) * 100

    for n, tier in [(0, "on_time"), (1, "late_1"), (2, "late_2"), (3, "late_3"), (6, "fail_4")]:
        answer = guideline.try_rule_engine(f"nhắc nhở {n} lần")
        assert answer["value_percent"] == get_timeline_percent(tier) * 100


def test_tim_dieu_khoan_tra_ve_dung_muc():
    assert any(c["id"] == "cong_thuc_kpi"
               for c in guideline.search_clauses("công thức tính KPI lãnh đạo"))
    assert any(c["id"] == "phan_nhom"
               for c in guideline.search_clauses("ngưỡng xếp loại nhóm 1 2 3"))
    assert any(c["id"] == "quy_trinh"
               for c in guideline.search_clauses("quy trình ba bước thẩm định"))


def test_khong_nhan_dien_thi_van_tra_dieu_khoan():
    result = guideline.answer("tiêu chí chung gồm những gì")
    assert result["rule_answer"] is None
    assert len(result["clauses"]) > 0


# ================= PHÁT HIỆN CHẤM ĐIỂM HÌNH THỨC =================

@pytest.mark.asyncio
async def test_bat_duoc_diem_E_dong_loat_toi_da(monkeypatch):
    """Cả đơn vị đều 30/30 điểm tiêu chí chung → phải bật cờ mức cao."""
    evals = [
        make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 70 + i * 5, "group_1", total_e=30.0)
        for i in range(6)
    ]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=evals,
        departments=[{"_id": "d1", "name": "Phòng Thử nghiệm"}],
    ))
    result = await anomaly.detect(8, 2026)
    codes = [f["code"] for f in result["flags"]]
    assert "diem_E_dong_loat_toi_da" in codes

    flag = next(f for f in result["flags"] if f["code"] == "diem_E_dong_loat_toi_da")
    assert flag["severity"] == "cao"
    assert "6/6" in flag["evidence"]


@pytest.mark.asyncio
async def test_bat_duoc_kpi_qua_dong_deu(monkeypatch):
    """Điểm KPI gần như giống hệt nhau trong đơn vị → bật cờ."""
    evals = [
        make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 80.0 + (i % 2) * 0.5, "group_1", total_e=22.0)
        for i in range(8)
    ]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=evals,
        departments=[{"_id": "d1", "name": "Phòng Thử nghiệm"}],
    ))
    result = await anomaly.detect(8, 2026)
    assert "kpi_qua_dong_deu" in [f["code"] for f in result["flags"]]


@pytest.mark.asyncio
async def test_bat_duoc_tu_danh_gia_lech_xa(monkeypatch):
    """Tự nhận Nhóm 1 nhưng kết quả là Nhóm 3 → lệch 2 nhóm, phải bật cờ."""
    evals = [
        make_eval("u1", "Cán bộ A", "d1", 8, 35.0, "group_3", total_e=20.0, proposed="group_1"),
        *[make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 60.0 + i * 4, "group_2", total_e=20.0)
          for i in range(2, 6)],
    ]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=evals,
        departments=[{"_id": "d1", "name": "Phòng Thử nghiệm"}],
    ))
    result = await anomaly.detect(8, 2026)
    flags = [f for f in result["flags"] if f["code"] == "tu_danh_gia_lech_xa"]
    assert len(flags) == 1
    assert flags[0]["target"] == "Cán bộ A"


@pytest.mark.asyncio
async def test_bat_duoc_kpi_nhay_vot(monkeypatch):
    """Điểm ổn định quanh 55 rồi vọt lên 95 → phải bật cờ."""
    history = [make_eval("u1", "Cán bộ A", "d1", m, 55.0 + m * 0.3, "group_2") for m in (5, 6, 7)]
    current = [make_eval("u1", "Cán bộ A", "d1", 8, 95.0, "group_1")]
    others = [make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 60.0 + i * 5, "group_2") for i in range(2, 6)]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=history + current + others,
        departments=[{"_id": "d1", "name": "Phòng Thử nghiệm"}],
    ))
    result = await anomaly.detect(8, 2026)
    flags = [f for f in result["flags"] if f["code"] == "kpi_nhay_vot"]
    assert len(flags) == 1
    assert "95.0" in flags[0]["evidence"]


@pytest.mark.asyncio
async def test_khong_bao_dong_gia_khi_thay_doi_nho(monkeypatch):
    """
    Chênh 2 điểm trên thang 100 là dao động bình thường, KHÔNG được báo động
    dù cán bộ đó có điểm rất ổn định (độ lệch chuẩn gần 0).
    """
    history = [make_eval("u1", "Cán bộ A", "d1", m, 80.0, "group_1") for m in (5, 6, 7)]
    current = [make_eval("u1", "Cán bộ A", "d1", 8, 82.0, "group_1")]
    others = [make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 55.0 + i * 9, "group_2") for i in range(2, 6)]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=history + current + others,
        departments=[{"_id": "d1", "name": "Phòng Thử nghiệm"}],
    ))
    result = await anomaly.detect(8, 2026)
    assert "kpi_nhay_vot" not in [f["code"] for f in result["flags"]]


@pytest.mark.asyncio
async def test_bat_duoc_mau_thuan_qua_han_va_xep_loai(monkeypatch):
    """Quá nửa nhiệm vụ quá hạn nhưng không ai Nhóm 3 → mâu thuẫn, bật cờ cao."""
    evals = [
        make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 75.0 + i * 3, "group_1", total_e=22.0)
        for i in range(6)
    ]
    qua_han = datetime(2026, 8, 5)
    tasks = [
        {"department_id": "d1", "period_month": 8, "period_year": 2026,
         "status": "in_progress", "actual_end": None, "deadline": qua_han}
        for _ in range(7)
    ] + [
        {"department_id": "d1", "period_month": 8, "period_year": 2026,
         "status": "done", "actual_end": qua_han, "deadline": qua_han}
        for _ in range(3)
    ]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=evals,
        departments=[{"_id": "d1", "name": "Phòng Thử nghiệm"}],
        tasks=tasks,
    ))
    result = await anomaly.detect(8, 2026)
    flags = [f for f in result["flags"] if f["code"] == "mau_thuan_qua_han_xep_loai"]
    assert len(flags) == 1
    assert flags[0]["severity"] == "cao"


@pytest.mark.asyncio
async def test_bo_qua_don_vi_qua_it_can_bo(monkeypatch):
    """Dưới 4 cán bộ thì thống kê vô nghĩa, không được báo động."""
    evals = [make_eval(f"u{i}", f"Cán bộ {i}", "d1", 8, 90.0, "group_1", total_e=30.0)
             for i in range(3)]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=evals,
        departments=[{"_id": "d1", "name": "Phòng Nhỏ"}],
    ))
    result = await anomaly.detect(8, 2026)
    dept_codes = {"diem_E_dong_loat_toi_da", "kpi_qua_dong_deu", "mau_thuan_qua_han_xep_loai"}
    assert not (dept_codes & {f["code"] for f in result["flags"]})


@pytest.mark.asyncio
async def test_khong_bao_dong_khi_du_lieu_binh_thuong(monkeypatch):
    """Đơn vị có điểm phân tán tự nhiên, điểm E khác nhau → không cờ nào."""
    evals = [
        make_eval("u1", "A", "d1", 8, 92.0, "group_1", total_e=30.0),
        make_eval("u2", "B", "d1", 8, 78.0, "group_1", total_e=26.0),
        make_eval("u3", "C", "d1", 8, 64.0, "group_2", total_e=24.0),
        make_eval("u4", "D", "d1", 8, 45.0, "group_3", total_e=20.0),
        make_eval("u5", "E", "d1", 8, 71.0, "group_1", total_e=28.0),
    ]
    monkeypatch.setattr(anomaly, "db", FakeDB(
        kpi_evaluations=evals,
        departments=[{"_id": "d1", "name": "Phòng Bình thường"}],
    ))
    result = await anomaly.detect(8, 2026)
    assert result["flags"] == []


# ================= RÀNG BUỘC: KHÔNG GỌI MẠNG =================

def test_khong_module_ai_nao_goi_mang():
    """
    Ràng buộc cốt lõi: không một byte dữ liệu nào rời hệ thống.
    Quét mã nguồn để chắc không có thư viện gọi mạng nào được import.
    """
    import pathlib

    cam = ("requests", "httpx", "urllib.request", "aiohttp",
           "openai", "anthropic", "google.generativeai", "socket")
    ai_dir = pathlib.Path(__file__).parent / "services" / "ai"

    for path in ai_dir.glob("*.py"):
        source = path.read_text()
        for lib in cam:
            assert f"import {lib}" not in source, f"{path.name} import {lib}"
            assert f"from {lib}" not in source, f"{path.name} import từ {lib}"


# ================= CHẶN MẬT KHẨU MẶC ĐỊNH TRÊN MÔI TRƯỜNG THẬT =================

def test_danh_sach_mat_khau_mau_bao_gom_mat_khau_cua_seeder():
    """
    Mọi mật khẩu mà seeder đặt phải nằm trong danh sách bị chặn, nếu không thì
    cơ chế bảo vệ có lỗ hổng.
    """
    from backend.routers.auth import MAT_KHAU_MAU
    from backend.services import seeder
    import inspect

    source = inspect.getsource(seeder)
    # Seeder dùng get_password_hash("...") — rút các chuỗi đó ra
    import re
    used = set(re.findall(r'get_password_hash\("([^"]+)"\)', source))
    assert used, "Không tìm thấy mật khẩu nào trong seeder — kiểm tra lại biểu thức"
    thieu = used - MAT_KHAU_MAU
    assert not thieu, f"Seeder dùng mật khẩu chưa bị chặn: {thieu}"


def test_co_allow_demo_mac_dinh_tat():
    """Mặc định phải TẮT — an toàn khi ai đó quên đặt biến môi trường."""
    from backend.config import _flag
    assert _flag("BIEN_KHONG_TON_TAI_XYZ", default=False) is False
    assert _flag("BIEN_KHONG_TON_TAI_XYZ", default=True) is True
