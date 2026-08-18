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

def test_danh_sach_chan_van_giu_cac_mat_khau_pho_bien():
    """
    Danh sách chặn phải luôn có các mật khẩu mặc định phổ biến, để không ai vô
    tình đặt lại chúng rồi mở toang cửa cho bản triển khai công khai.
    """
    from backend.routers.auth import MAT_KHAU_MAU

    for mk in ("admin123", "123456", "password", "12345678"):
        assert mk in MAT_KHAU_MAU, f"Thiếu {mk!r} trong danh sách chặn"


def test_mat_khau_cua_du_lieu_mau_la_lua_chon_co_chu_y():
    """
    Dữ liệu mẫu CỐ Ý dùng mật khẩu nằm ngoài danh sách chặn, để bản demo đăng
    nhập được mà không phải bật ALLOW_DEMO_ACCOUNTS.

    Đây là ĐÁNH ĐỔI đã cân nhắc, không phải sơ suất: cơ chế chặn khi đó không
    còn bảo vệ các tài khoản mẫu nữa. Test này ghi lại quyết định đó, đồng thời
    ràng buộc mật khẩu mẫu phải đủ dài để không quá dễ đoán.
    """
    from backend.routers.auth import MAT_KHAU_MAU
    from backend.services.seeder import MAT_KHAU_MAU_DEMO

    assert MAT_KHAU_MAU_DEMO not in MAT_KHAU_MAU, (
        "Mật khẩu của dữ liệu mẫu đang nằm trong danh sách chặn — "
        "chạy seeder xong sẽ không tài khoản nào đăng nhập được"
    )
    assert len(MAT_KHAU_MAU_DEMO) >= 10


def test_seeder_dung_dung_mot_mat_khau_duy_nhat():
    """Mọi tài khoản mẫu phải dùng chung hằng số, không rải mật khẩu ghi cứng."""
    import inspect
    import re
    from backend.services import seeder

    source = inspect.getsource(seeder)
    ghi_cung = re.findall(r'get_password_hash\("([^"]+)"\)', source)
    assert not ghi_cung, f"Seeder còn ghi cứng mật khẩu: {set(ghi_cung)}"
    assert 'get_password_hash(MAT_KHAU_MAU_DEMO)' in source


def test_co_allow_demo_mac_dinh_tat():
    """Mặc định phải TẮT — an toàn khi ai đó quên đặt biến môi trường."""
    from backend.config import _flag
    assert _flag("BIEN_KHONG_TON_TAI_XYZ", default=False) is False
    assert _flag("BIEN_KHONG_TON_TAI_XYZ", default=True) is True


# ---------------------------------------------------------------------------
# CORS — nguồn được phép gọi API
#
# Đây là lỗi đã hai lần làm bản triển khai không đăng nhập được: quên đặt
# CORS_ORIGINS trên Render thì trình duyệt chặn mọi lời gọi, mà giao diện chỉ
# báo "CORS policy" chung chung. Khoá lại bằng test.
# ---------------------------------------------------------------------------

@pytest.fixture
def moi_truong_sach(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ORIGIN_REGEX", raising=False)
    return monkeypatch


def _duoc_phep(nguon: str, danh_sach: list, regex: str) -> bool:
    """Mô phỏng cách CORSMiddleware của Starlette quyết định."""
    import re
    return nguon in danh_sach or bool(re.fullmatch(regex, nguon))


def test_ban_trien_khai_vercel_duoc_phep_du_khong_dat_bien_moi_truong(moi_truong_sach):
    """Không đặt CORS_ORIGINS thì giao diện đã triển khai VẪN phải gọi được API."""
    from backend.config import nguon_cors

    danh_sach, regex = nguon_cors()
    assert _duoc_phep("https://smartwork-ai-3u7e.vercel.app", danh_sach, regex)


def test_ten_mien_xem_truoc_cua_vercel_cung_duoc_phep(moi_truong_sach):
    """Mỗi lần đẩy mã Vercel sinh một tên miền mới — không thể liệt kê từng cái."""
    from backend.config import nguon_cors

    danh_sach, regex = nguon_cors()
    for ten_mien in (
        "https://smartwork-ai.vercel.app",
        "https://smartwork-ai-git-main-longbush23.vercel.app",
        "https://smartwork-ai-3u7e.vercel.app",
    ):
        assert _duoc_phep(ten_mien, danh_sach, regex), ten_mien


def test_trang_web_la_khong_duoc_phep(moi_truong_sach):
    """Mở cho Vercel của dự án, KHÔNG mở cho cả thiên hạ."""
    from backend.config import nguon_cors

    danh_sach, regex = nguon_cors()
    for ten_mien in (
        "https://ke-gian.com",
        "https://smartwork-ai.vercel.app.ke-gian.com",  # hậu tố giả mạo
        "http://smartwork-ai.vercel.app",               # không phải https
        "https://vercel.app",
    ):
        assert not _duoc_phep(ten_mien, danh_sach, regex), ten_mien


def test_may_cuc_bo_luon_duoc_phep_ke_ca_khi_da_dat_ten_mien_that(moi_truong_sach):
    """
    CORS_ORIGINS bổ sung chứ không thay thế: đặt tên miền thật rồi mà
    `npm run dev` ở máy lại hỏng thì rất mất thời gian mới tìm ra.
    """
    from backend.config import nguon_cors

    moi_truong_sach.setenv("CORS_ORIGINS", "https://kpi.bocongan.gov.vn")
    danh_sach, regex = nguon_cors()
    assert "https://kpi.bocongan.gov.vn" in danh_sach
    assert "http://localhost:5173" in danh_sach


def test_cors_origins_nhan_nhieu_dia_chi_cach_nhau_dau_phay(moi_truong_sach):
    from backend.config import nguon_cors

    moi_truong_sach.setenv("CORS_ORIGINS", " https://a.gov.vn , https://b.gov.vn ")
    danh_sach, _ = nguon_cors()
    assert "https://a.gov.vn" in danh_sach and "https://b.gov.vn" in danh_sach


def test_khong_dung_allow_credentials_cung_voi_cors_mo_rong():
    """
    Mở CORS theo mẫu mà bật allow_credentials là để lộ phiên đăng nhập.
    Hệ thống dùng thẻ Bearer nên phải giữ allow_credentials=False.
    """
    import inspect
    from backend import main

    source = inspect.getsource(main)
    assert "allow_credentials=False" in source
    assert "allow_credentials=True" not in source


# ---------------------------------------------------------------------------
# Hiệu năng — mọi truy vấn nhiều bản ghi phải có projection
#
# Một bản ghi kpi_evaluations nặng ~17 KB vì kèm chi tiết từng nhiệm vụ. Lấy
# nguyên 390 bản ghi là tải 6,8 MB qua mạng mỗi lần gọi API. Đo được: endpoint
# cảnh báo sớm mất 5,4 giây, trong đó 5,17 giây là chờ socket — không phải tính
# toán. Thêm projection đưa xuống 0,4 giây.
#
# Test này chặn việc bỏ projection, vì hậu quả không hiện ra khi chạy máy cục bộ
# với cơ sở dữ liệu ở cùng máy — chỉ lộ ra trên bản triển khai dùng Atlas.
# ---------------------------------------------------------------------------

def _cac_loi_goi_find_khong_projection(path):
    """Trả về [(dòng, biểu thức)] cho mỗi .find(...) nhiều bản ghi thiếu projection."""
    import ast

    tree = ast.parse(path.read_text())
    thieu = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        # Chỉ xét .find() — find_one() trả về 1 bản ghi nên không đáng lo
        if node.func.attr != "find":
            continue
        if len(node.args) < 2:
            thieu.append((node.lineno, ast.unparse(node.func)))
    return thieu


def test_moi_truy_van_trong_goi_ai_deu_co_projection():
    import pathlib

    goi_ai = pathlib.Path(__file__).parent / "services" / "ai"
    loi = []
    for f in sorted(goi_ai.glob("*.py")):
        for dong, bieu_thuc in _cac_loi_goi_find_khong_projection(f):
            loi.append(f"{f.name}:{dong} — {bieu_thuc}.find() thiếu projection")

    assert not loi, (
        "Truy vấn thiếu projection sẽ tải nguyên bản ghi 17 KB qua mạng:\n  "
        + "\n  ".join(loi)
        + "\n\nDùng hằng số trong backend/services/ai/projections.py."
    )


def test_projection_kpi_du_cac_truong_ma_mo_hinh_thuc_su_doc():
    """
    Projection thiếu trường thì không báo lỗi — chỉ âm thầm cho ra số sai.
    Khoá lại danh sách trường tối thiểu.
    """
    from backend.services.ai.projections import KPI_RA_SOAT, KPI_TOI_THIEU

    for truong in ("target_id", "period_month", "period_year",
                   "approval.kpi_score", "approval.kpi_group"):
        assert KPI_TOI_THIEU.get(truong) == 1, f"Thiếu {truong}"

    # Rà soát chấm điểm hình thức cần thêm điểm E và mức tự nhận
    for truong in ("general_criteria.total_E", "self_evaluation.proposed_rating"):
        assert KPI_RA_SOAT.get(truong) == 1, f"Thiếu {truong}"


# ---------------------------------------------------------------------------
# Giao diện — nhiệm vụ có độ mật phải luôn có dấu hiệu nhận biết
#
# Máy chủ che dữ liệu đúng, nhưng trang chủ từng in thẳng {t.title} nên nhiệm vụ
# TUYỆT MẬT hiện lên y hệt nhiệm vụ thường: không ổ khoá, không huy hiệu. Người
# xem không hề biết mình đang nhìn tài liệu mật.
#
# Gốc rễ là mỗi trang tự vẽ lấy. Nay gom về components/TaskTitle.tsx, và test
# này chặn việc một trang mới lại vẽ tay rồi quên độ mật.
# ---------------------------------------------------------------------------

def _thu_muc_frontend():
    import pathlib
    return pathlib.Path(__file__).resolve().parent.parent / "frontend" / "src"


def test_moi_trang_hien_ten_nhiem_vu_deu_dung_component_chung():
    import re

    src = _thu_muc_frontend()
    if not src.exists():
        pytest.skip("Không có mã nguồn giao diện")

    loi = []
    for f in sorted(src.rglob("*.tsx")):
        if f.name == "TaskTitle.tsx":
            continue
        noi_dung = f.read_text()
        # Chỉ xét component thực sự làm việc với đối tượng Task
        lam_viec_voi_task = "type { Task }" in noi_dung or "Task[]" in noi_dung
        if not lam_viec_voi_task:
            continue
        # Có in tên nhiệm vụ ra JSX không? (bỏ qua thuộc tính như title={...})
        in_ten = re.search(r"\{\s*\w+\.title\s*\}", noi_dung)
        if in_ten and "TaskTitle" not in noi_dung:
            loi.append(f"{f.relative_to(src)} in thẳng .title mà không dùng TaskTitle")

    assert not loi, (
        "Nhiệm vụ có độ mật sẽ hiện như nhiệm vụ thường:\n  " + "\n  ".join(loi)
        + "\n\nDùng <TaskTitle> trong components/TaskTitle.tsx."
    )


def test_component_ten_nhiem_vu_co_du_dau_hieu_do_mat():
    """TaskTitle phải có ổ khoá, huy hiệu độ mật và cảnh báo chưa đủ cấp độ."""
    src = _thu_muc_frontend()
    if not src.exists():
        pytest.skip("Không có mã nguồn giao diện")

    noi_dung = (src / "components" / "TaskTitle.tsx").read_text()
    for phai_co, mo_ta in [
        ("Lock", "biểu tượng ổ khoá"),
        ("CLASSIFICATION_LABELS", "nhãn độ mật"),
        ("isRedacted", "trạng thái bị che"),
        ("chưa đủ cấp độ tiếp cận", "cảnh báo thiếu cấp độ tiếp cận"),
    ]:
        assert phai_co in noi_dung, f"TaskTitle thiếu {mo_ta}"


def test_projection_nhiem_vu_khong_lay_truong_bi_che():
    """
    Các trường bị che theo cấp độ tiếp cận không được nằm trong projection của
    mô hình: mô hình chỉ dùng số liệu, không cần nội dung nhiệm vụ.
    """
    from backend.models.security_policy import RESTRICTED_FIELDS
    from backend.services.ai.projections import NHIEM_VU_DAC_TRUNG

    for truong in RESTRICTED_FIELDS:
        assert truong not in NHIEM_VU_DAC_TRUNG, (
            f"{truong!r} là trường bị che theo cấp độ tiếp cận, "
            "không được đưa vào projection của mô hình"
        )


# ---------------------------------------------------------------------------
# Sổ đăng ký mô hình — nguồn duy nhất cho trang "Mô hình hỗ trợ ra quyết định"
#
# Trang đó là chỗ người thẩm định đọc để biết hệ thống dùng mô hình gì. Nếu mô tả
# ở đó trôi khỏi mã nguồn thì tệ hơn là không có trang nào: người đọc tin vào một
# thứ không còn đúng. Các test dưới đây khoá lại mối nối giữa ba nơi — sổ đăng ký,
# hằng số của từng mô hình, và nhãn dấu vết AI trong giao diện.
# ---------------------------------------------------------------------------

def test_so_dang_ky_khai_du_thong_tin_cho_tung_mo_hinh():
    from backend.services.so_dang_ky_mo_hinh import MO_HINH

    assert len(MO_HINH) >= 6, "Sổ đăng ký thiếu mô hình"

    ma_da_gap = set()
    for m in MO_HINH:
        for truong in ("ma", "so", "ten", "muc_dich", "thuat_toan", "vi_sao",
                       "noi_chay", "ma_nguon", "dung_o"):
            assert m.get(truong), f"Mô hình {m.get('ma')} thiếu {truong}"

        assert m["ma"] not in ma_da_gap, f"Mã {m['ma']} bị trùng"
        ma_da_gap.add(m["ma"])

        assert m["noi_chay"] in ("tai_cho", "goi_ra_ngoai")
        # Lý do chọn thuật toán là phần bắt buộc, không được viết cho có
        assert len(m["vi_sao"]) > 80, f"Mô hình {m['ma']} chưa nêu rõ lý do chọn thuật toán"
        for d in m["dung_o"]:
            assert d.get("nhan") and d.get("duong_dan", "").startswith("/")


def test_dung_mot_mo_hinh_duoc_goi_ra_ngoai():
    """
    Ranh giới bán được của hệ thống: chỉ trợ lý hội thoại gọi ra ngoài. Nếu có
    mô hình thứ hai được đánh dấu như vậy thì hoặc là gắn nhãn sai, hoặc ranh
    giới đã bị phá — cả hai đều phải biết ngay.
    """
    from backend.services.so_dang_ky_mo_hinh import MO_HINH

    goi_ra_ngoai = [m["ma"] for m in MO_HINH if m["noi_chay"] == "goi_ra_ngoai"]
    assert goi_ra_ngoai == ["tro_ly_hoi_thoai"], (
        f"Chỉ trợ lý hội thoại được gọi ra ngoài, nhưng sổ đăng ký ghi: {goi_ra_ngoai}"
    )


def test_goi_ai_khong_tham_chieu_goi_tro_ly():
    """
    `services/ai` cam kết không gọi mạng. Nó mà import `services/tro_ly` — gói có
    httpx — thì cam kết đó mất nghĩa dù test quét thư viện vẫn xanh. Đó cũng là lý
    do sổ đăng ký đặt ở `services/`, không đặt trong `services/ai`.
    """
    import pathlib

    goi_ai = pathlib.Path(__file__).parent / "services" / "ai"
    for path in goi_ai.glob("*.py"):
        source = path.read_text()
        assert "services.tro_ly" not in source, (
            f"{path.name} tham chiếu tới services/tro_ly — gói này phải độc lập"
        )


def test_moi_mo_hinh_deu_neu_duoc_tham_so_dang_dung():
    from backend.services.so_dang_ky_mo_hinh import MO_HINH, _tham_so

    for m in MO_HINH:
        ts = _tham_so(m["ma"])
        assert ts, f"Mô hình {m['ma']} không nêu được tham số nào"
        for d in ts:
            assert d["nhan"] and d["gia_tri"]


def test_tham_so_goi_y_phan_cong_lay_dung_trong_so_dang_chay():
    """Trọng số in ra trang phải là trọng số mô hình thực sự dùng, không phải số gõ tay."""
    from backend.services.ai import assignment
    from backend.services.so_dang_ky_mo_hinh import _tham_so

    ts = _tham_so("goi_y_phan_cong")
    for k, v in assignment.TRONG_SO.items():
        assert any(f"{v:.0%}" == d["gia_tri"] for d in ts), (
            f"Không thấy trọng số {k} = {v:.0%} trên trang"
        )


def test_bao_cao_chat_luong_sap_dac_trung_theo_muc_anh_huong():
    """
    Bảng hệ số phải đưa đặc trưng nặng nhất lên đầu và kèm mô tả bằng lời — bảng
    chỉ có tên biến thì người thẩm định phải mở mã nguồn mới đọc được.
    """
    from backend.services.ai import risk

    bao_cao = risk._bao_cao({
        "usable": True, "auc": 0.83, "n_samples": 120, "n_positive": 30,
        "confusion": {"tn": 15, "fp": 3, "fn": 2, "tp": 4},
        "coefficients": {"so_viec_qua_han": 0.4, "xu_the_kpi": -1.2, "tai_viec": 0.9},
        "trained_at": "2026-08-17T00:00:00",
    })

    assert [d["ten"] for d in bao_cao["dac_trung"]] == [
        "xu_the_kpi", "tai_viec", "so_viec_qua_han",
    ]
    assert bao_cao["dac_trung"][0]["khi_cao"] == "KPI đang đi lên"
    assert "model" not in bao_cao and "scaler" not in bao_cao


def test_nhan_dau_vet_ai_khop_so_dang_ky():
    """
    Nhãn dấu vết AI trong giao diện phải khớp số hiệu và tên của sổ đăng ký.
    Lệch thì nhãn dẫn người xem sang một thẻ mô hình khác — sai mà không báo lỗi.
    """
    import re

    from backend.services.so_dang_ky_mo_hinh import MO_HINH

    src = _thu_muc_frontend()
    if not src.exists():
        pytest.skip("Không có mã nguồn giao diện")

    noi_dung = (src / "lib" / "dau-vet-ai.ts").read_text()
    khoi = re.search(r"MO_HINH_DA_GAN[^=]*=\s*\{(.*?)\n\};", noi_dung, re.S)
    assert khoi, "Không tìm thấy MO_HINH_DA_GAN trong lib/dau-vet-ai.ts"

    trong_giao_dien = {
        ma: (int(so), ten)
        for ma, so, ten in re.findall(
            r"(\w+):\s*\{\s*so:\s*(\d+),\s*ten:\s*'([^']*)'", khoi.group(1)
        )
    }
    trong_so_dang_ky = {m["ma"]: (m["so"], m["ten"]) for m in MO_HINH}

    assert trong_giao_dien == trong_so_dang_ky, (
        "Nhãn dấu vết AI lệch khỏi sổ đăng ký mô hình:\n"
        f"  giao diện:  {trong_giao_dien}\n"
        f"  sổ đăng ký: {trong_so_dang_ky}"
    )


def test_nhan_thanh_phan_khop_khoa_trong_so_cua_mo_hinh_phan_cong():
    """
    Thanh 5 thành phần trong hộp nhiệm vụ vẽ theo khoá của TRONG_SO. Đổi tên một
    khoá ở backend mà quên giao diện thì thanh lặng lẽ mất một cột.
    """
    import re

    from backend.services.ai.assignment import TRONG_SO

    src = _thu_muc_frontend()
    if not src.exists():
        pytest.skip("Không có mã nguồn giao diện")

    noi_dung = (src / "lib" / "ai-api.ts").read_text()
    khoi = re.search(r"NHAN_THANH_PHAN[^=]*=\s*\{(.*?)\n\};", noi_dung, re.S)
    assert khoi, "Không tìm thấy NHAN_THANH_PHAN trong lib/ai-api.ts"

    khoa_giao_dien = set(re.findall(r"^\s*(\w+):", khoi.group(1), re.M))
    assert khoa_giao_dien == set(TRONG_SO), (
        f"Nhãn thành phần lệch: giao diện {sorted(khoa_giao_dien)} "
        f"vs backend {sorted(TRONG_SO)}"
    )
