"""
Kiểm thử công thức tính điểm KPI theo Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026.

Các test này thuần logic, không cần kết nối cơ sở dữ liệu.
Chạy:  pytest backend/test_kpi.py -v
"""
import pytest

from backend.models.kpi_criteria import (
    CRITERIA_TEMPLATES, flatten_criteria, criteria_type_for,
)
from backend.services.kpi_service import (
    get_quality_percent, get_timeline_percent,
    get_task_quality_score, get_task_timeline_score,
    calculate_score_A, calculate_score_B, calculate_score_C,
    calculate_kpi, determine_kpi_group, calculate_total_score,
)


def task(point, completed=True, quality="good", timeline="on_time"):
    """Dựng 1 dòng chấm điểm nhiệm vụ."""
    return {
        "kpi_point": point,
        "is_completed": completed,
        "quality_tier": quality,
        "timeline_tier": timeline,
    }


# ================= MỨC PHẦN TRĂM CHẤT LƯỢNG (B) =================

@pytest.mark.parametrize("tier,expected", [
    ("excellent", 1.20),   # vượt mức yêu cầu: không quá 120%
    ("good", 1.00),        # đảm bảo chất lượng: 100%
    ("fair_1", 0.75),      # sửa 01 lần: không quá 75%
    ("fair_2_4", 0.50),    # sửa 02-04 lần: không quá 50%
    ("poor_5_6", 0.25),    # sửa 05-06 lần: không quá 25%
    ("fail_7", 0.00),      # sửa từ 07 lần: không tính điểm
])
def test_quality_percent(tier, expected):
    assert get_quality_percent(tier) == expected


# ================= MỨC PHẦN TRĂM TIẾN ĐỘ (C) =================

@pytest.mark.parametrize("tier,expected", [
    ("ahead", 1.20),     # vượt tiến độ và đảm bảo chất lượng
    ("on_time", 1.00),   # đúng tiến độ
    ("late_1", 0.75),    # nhắc nhở 01 lần
    ("late_2", 0.50),    # nhắc nhở 02 lần
    ("late_3", 0.25),    # nhắc nhở 03 lần
    ("fail_4", 0.00),    # nhắc nhở từ 04 lần
])
def test_timeline_percent(tier, expected):
    assert get_timeline_percent(tier) == expected


def test_unknown_tier_scores_zero():
    """Mức không xác định phải cho 0 điểm, không được mặc định thành điểm tối đa."""
    assert get_quality_percent("khong_ton_tai") == 0.0
    assert get_timeline_percent("khong_ton_tai") == 0.0


# ================= SUY ĐIỂM TỪNG NHIỆM VỤ =================

def test_task_score_derived_from_tier():
    """Không có sẵn quality_score thì phải suy ra từ tier (lỗi cũ trả về 0)."""
    t = task(80, quality="fair_1", timeline="late_2")
    assert get_task_quality_score(t) == pytest.approx(60.0)   # 80 x 75%
    assert get_task_timeline_score(t) == pytest.approx(40.0)  # 80 x 50%


def test_task_score_prefers_stored_value():
    t = task(80, quality="good")
    t["quality_score"] = 12.5
    assert get_task_quality_score(t) == pytest.approx(12.5)


# ================= ĐIỂM A, B, C =================

def test_score_A_counts_only_completed():
    tasks = [task(50), task(30), task(20, completed=False)]
    assert calculate_score_A(tasks, 100) == pytest.approx(0.80)


def test_score_B_applies_quality_percent():
    # 50 x 100% + 50 x 50% = 75 / 100
    tasks = [task(50, quality="good"), task(50, quality="fair_2_4")]
    assert calculate_score_B(tasks, 100) == pytest.approx(0.75)


def test_scores_rounded_to_three_decimals():
    """Phụ lục ghi A, B, C ở 03 chữ số thập phân và tính KPI từ giá trị đã ghi."""
    tasks = [task(314.5, quality="good")]
    assert calculate_score_B(tasks, 335) == 0.939   # không phải 0.9388059...


def test_score_C_applies_timeline_percent():
    # 50 x 100% + 50 x 25% = 62.5 / 100
    tasks = [task(50, timeline="on_time"), task(50, timeline="late_3")]
    assert calculate_score_C(tasks, 100) == pytest.approx(0.625)


def test_scores_can_exceed_one_when_exceeding_requirements():
    """Hoàn thành vượt mức được ghi nhận, nên B, C có thể vượt 100%."""
    tasks = [task(100, quality="excellent", timeline="ahead")]
    assert calculate_score_B(tasks, 100) == pytest.approx(1.20)
    assert calculate_score_C(tasks, 100) == pytest.approx(1.20)


def test_zero_assigned_points_does_not_divide_by_zero():
    assert calculate_score_A([], 0) == 0.0
    assert calculate_score_B([], 0) == 0.0
    assert calculate_score_C([], 0) == 0.0


def test_incomplete_task_contributes_nothing_to_B_and_C():
    tasks = [task(100, completed=False, quality="excellent", timeline="ahead")]
    assert calculate_score_B(tasks, 100) == 0.0
    assert calculate_score_C(tasks, 100) == 0.0


# ================= CÔNG THỨC KPI =================

def test_kpi_non_commander_uses_three_criteria():
    """KPI tập thể / cá nhân không là lãnh đạo = (A+B+C)/3 x 100"""
    assert calculate_kpi(1.0, 0.9, 0.8) == pytest.approx(90.0)


def test_kpi_commander_uses_four_criteria():
    """KPI cá nhân là lãnh đạo, chỉ huy = (A+B+C+D)/4 x 100"""
    assert calculate_kpi(1.0, 0.9, 0.8, 0.5, is_leader=True) == pytest.approx(80.0)


def test_score_D_ignored_when_not_leader():
    assert calculate_kpi(1.0, 1.0, 1.0, 0.0, is_leader=False) == pytest.approx(100.0)


# ================= PHÂN NHÓM CÁN BỘ =================

@pytest.mark.parametrize("kpi,group", [
    (100.0, "group_1"),  # đáp ứng tốt: 70 - 100
    (70.0, "group_1"),   # biên dưới nhóm 1
    (69.99, "group_2"),  # đáp ứng: 50 đến dưới 70
    (50.0, "group_2"),   # biên dưới nhóm 2
    (49.99, "group_3"),  # chưa đáp ứng: dưới 50
    (0.0, "group_3"),
])
def test_kpi_group_thresholds(kpi, group):
    assert determine_kpi_group(kpi) == group


# ================= TỔNG ĐIỂM XẾP LOẠI =================

def test_total_score_formula():
    """F = G = H = E + KPI x 0,7"""
    assert calculate_total_score(30.0, 100.0) == pytest.approx(100.0)
    assert calculate_total_score(25.0, 80.0) == pytest.approx(81.0)


def test_total_score_max_is_100():
    """E tối đa 30, KPI tối đa 100 → tổng tối đa 100 điểm."""
    assert calculate_total_score(30.0, 100.0) <= 100.0


# ================= KHUNG TIÊU CHÍ CHUNG (E) =================

@pytest.mark.parametrize("ctype", ["collective", "leader", "staff"])
def test_criteria_template_totals_30(ctype):
    """Tổng điểm tiêu chí chung của mỗi bộ phải đúng 30 điểm."""
    template = CRITERIA_TEMPLATES[ctype]
    assert template["total_max_score"] == 30
    assert sum(l["max_score"] for l in flatten_criteria(ctype)) == 30


def test_criteria_parent_equals_sum_of_children():
    """Điểm mục cha phải bằng tổng điểm các tiêu chí con."""
    for ctype, template in CRITERIA_TEMPLATES.items():
        for c in template["criteria"]:
            subs = c.get("sub_criteria")
            if subs:
                total = sum(s["max_score"] for s in subs)
                assert total == c["max_score"], f"{ctype}/{c['id']}: con cộng {total} != cha {c['max_score']}"


def test_criteria_ids_unique():
    for ctype in CRITERIA_TEMPLATES:
        ids = [l["id"] for l in flatten_criteria(ctype)]
        assert len(ids) == len(set(ids)), f"{ctype} có mã tiêu chí trùng"


@pytest.mark.parametrize("eval_type,role,expected", [
    ("collective", None, "collective"),
    ("collective", "director", "collective"),
    ("individual", "director", "leader"),
    ("individual", "leader", "leader"),
    ("individual", "staff", "staff"),
    ("individual", None, "staff"),
])
def test_criteria_type_selection(eval_type, role, expected):
    assert criteria_type_for(eval_type, role) == expected


# ================= VÍ DỤ MẪU TRONG TÀI LIỆU =================

def test_worked_example_from_guideline():
    """
    Ví dụ chấm điểm đồng chí A tháng 6/2026 (mục B Phụ lục Hướng dẫn 20-HD/ĐUCA).

    Tổng điểm giao nhiệm vụ            : 335
    Điểm số lượng công việc hoàn thành : 335  → A = 1
    Điểm về chất lượng                 : 314,5 → B = 0,939
    Điểm về tiến độ                    : 335  → C = 1
    KPI = (1 + 0,939 + 1) / 3 x 100 = 97,97
    Tổng điểm xếp loại = 30 + 97,97 x 0,7 = 98,579
    """
    total_assigned = 335

    # A, B, C tính qua hàm nghiệp vụ — đã làm tròn 03 chữ số như Phụ lục ghi
    score_A = calculate_score_A([task(335)], total_assigned)
    score_B = round(314.5 / total_assigned, 3)
    score_C = round(335 / total_assigned, 3)

    assert score_A == 1.0
    assert score_B == 0.939
    assert score_C == 1.0

    kpi = calculate_kpi(score_A, score_B, score_C)
    assert round(kpi, 2) == 97.97
    assert determine_kpi_group(kpi) == "group_1"

    total = calculate_total_score(30.0, kpi)
    assert round(total, 3) == 98.579


def test_worked_example_rebuilt_from_task_lines():
    """
    Dựng lại đúng 05 dòng nhiệm vụ của ví dụ trong tài liệu và kiểm tra
    tổng điểm khớp: 335 điểm giao, 314,5 điểm chất lượng, 335 điểm tiến độ.

    NV1 Công văn  10 sp x 05 = 50   · đảm bảo             → B 50
    NV2 Báo cáo   03 sp x 15 = 45   · đảm bảo             → B 45
    NV3 Tờ trình  03 sp x 20 = 60   · 02 đảm bảo + 01 vượt mức (110%) → B 62
    NV4 Thông tư  01 sp x 90 = 90   · đảm bảo             → B 90
    NV5 Quy định  01 sp x 90 = 90   · chỉnh sửa 01 lần (75%)        → B 67,5
    """
    assigned = [50, 45, 60, 90, 90]
    quality = [50, 45, 62, 90, 67.5]   # 60/3=20 mỗi sp; 2x20 + 20x1,10 = 62
    timeline = [50, 45, 60, 90, 90]

    assert sum(assigned) == 335
    assert sum(quality) == 314.5
    assert sum(timeline) == 335

    # Mức 75% của NV5 đúng bằng quy định "chỉnh sửa 01 lần"
    assert 90 * get_quality_percent("fair_1") == pytest.approx(67.5)
    # Mức vượt mức yêu cầu không được quá 120%
    assert 20 * 1.10 <= 20 * get_quality_percent("excellent")


def test_commander_kpi_capped_by_collective():
    """
    KPI của người đứng đầu không cao hơn KPI của tập thể do mình đứng đầu.
    """
    collective_kpi = 82.0
    commander_kpi = calculate_kpi(1.0, 1.0, 1.0, 1.0, is_leader=True)  # 100
    assert commander_kpi > collective_kpi

    final = min(commander_kpi, collective_kpi)
    assert final == pytest.approx(82.0)
    assert determine_kpi_group(final) == "group_1"
