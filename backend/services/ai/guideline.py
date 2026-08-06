"""
Tra cứu Hướng dẫn số 20-HD/ĐUCA — chạy hoàn toàn tại chỗ, không dùng LLM.

VÌ SAO KHÔNG DÙNG LLM Ở ĐÂY
---------------------------
Đây là văn bản pháp quy. Cán bộ cần NGUYÊN VĂN điều khoản để trích dẫn, không
cần bản diễn giải có thể sai lệch. Quan trọng hơn: mọi câu trả lời về con số
đều lấy TRỰC TIẾP từ hằng số của bộ máy chấm điểm (`kpi_service`), nên câu trả
lời LUÔN khớp với điều hệ thống thực sự tính. Một mô hình sinh văn bản không
bảo đảm được điều đó.

Gồm hai phần:
  1. Máy quy tắc — nhận diện câu hỏi về số ("sửa 3 lần?") và trả lời chính xác
  2. Tìm kiếm điều khoản — so khớp từ khoá tiếng Việt đã chuẩn hoá bỏ dấu
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional

from backend.models.kpi_criteria import CRITERIA_TEMPLATES
from backend.services.kpi_service import (
    get_quality_percent, get_timeline_percent,
    determine_kpi_group, KPI_PRECISION, SCORE_PRECISION,
)

# ================= CHUẨN HOÁ TIẾNG VIỆT =================

def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp không phụ thuộc cách gõ."""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(text.lower())).strip()


# ================= CHỈ MỤC ĐIỀU KHOẢN =================
# Mỗi mục: id, tiêu đề, trích dẫn nguyên văn, từ khoá, nguồn trong văn bản

CLAUSES: List[Dict[str, Any]] = [
    {
        "id": "diem_A",
        "title": "Điểm về số lượng kết quả thực hiện nhiệm vụ (A)",
        "source": "Mục 3.a — Nguyên tắc tính điểm KPI",
        "text": (
            "Điểm về số lượng kết quả thực hiện nhiệm vụ (A) được xác định bằng tỷ lệ giữa "
            "Điểm số lượng công việc đã hoàn thành và Điểm công việc được giao theo Danh mục "
            "nhiệm vụ công tác theo KPI."
        ),
        "keywords": "diem a so luong cong viec hoan thanh cong thuc",
    },
    {
        "id": "diem_B",
        "title": "Điểm về chất lượng kết quả thực hiện nhiệm vụ (B)",
        "source": "Mục 3.a — Nguyên tắc tính điểm KPI",
        "text": (
            "Điểm về chất lượng kết quả thực hiện nhiệm vụ (B) được xác định bằng tỷ lệ giữa "
            "Điểm về chất lượng của công việc đã hoàn thành và Điểm công việc được giao."
        ),
        "keywords": "diem b chat luong cong thuc",
    },
    {
        "id": "muc_chat_luong",
        "title": "Các mức điểm chất lượng theo số lần hoàn thiện, chỉnh sửa",
        "source": "Mục 3.a — Điểm về chất lượng (B)",
        "text": (
            "Công việc có chất lượng được đánh giá vượt mức yêu cầu, được tính không quá 120% "
            "số điểm của công việc đó.\n"
            "Công việc đảm bảo về chất lượng, được tính bằng 100% số điểm.\n"
            "Công việc được đánh giá cơ bản đảm bảo về chất lượng, còn phải hoàn thiện, chỉnh sửa "
            "01 lần trước khi được cấp có thẩm quyền đánh giá là đảm bảo chất lượng, được tính "
            "không quá 75% số điểm.\n"
            "Công việc được đánh giá còn thiếu sót, còn phải hoàn thiện, chỉnh sửa từ 02 - 04 lần, "
            "được tính không quá 50% số điểm.\n"
            "Công việc được đánh giá thiếu sót, phải hoàn thiện, chỉnh sửa từ 05 - 06 lần, "
            "được tính không quá 25% số điểm.\n"
            "Công việc phải hoàn thiện, chỉnh sửa từ 07 lần trở lên thì không được tính điểm."
        ),
        "keywords": "chat luong sua chinh sua hoan thien bao nhieu phan tram muc diem lan",
    },
    {
        "id": "diem_C",
        "title": "Điểm về tiến độ thực hiện nhiệm vụ (C)",
        "source": "Mục 3.a — Nguyên tắc tính điểm KPI",
        "text": (
            "Điểm về tiến độ thực hiện nhiệm vụ (C) được xác định bằng tỷ lệ giữa Điểm về tiến độ "
            "của công việc hoàn thành và Điểm công việc được giao."
        ),
        "keywords": "diem c tien do cong thuc",
    },
    {
        "id": "muc_tien_do",
        "title": "Các mức điểm tiến độ theo số lần bị nhắc nhở",
        "source": "Mục 3.a — Điểm về tiến độ (C)",
        "text": (
            "Công việc vượt tiến độ và được đánh giá là đảm bảo về chất lượng, được tính không quá "
            "120% số điểm của công việc đó.\n"
            "Công việc được đánh giá là đảm bảo về tiến độ và chất lượng, được tính bằng 100% số điểm.\n"
            "Công việc hoàn thành nhưng chưa đảm bảo tiến độ, đã bị nhắc nhở 01 lần, được tính "
            "không quá 75% số điểm.\n"
            "Công việc hoàn thành nhưng chưa đảm bảo tiến độ, đã bị nhắc nhở 02 lần, được tính "
            "không quá 50% số điểm.\n"
            "Công việc hoàn thành nhưng chưa đảm bảo tiến độ, đã bị nhắc nhở 03 lần, được tính "
            "không quá 25% số điểm.\n"
            "Công việc hoàn thành nhưng chưa đảm bảo tiến độ, đã bị nhắc nhở từ 04 lần trở lên "
            "thì không tính điểm."
        ),
        "keywords": "tien do nhac nho tre han bao nhieu phan tram muc diem lan cham",
    },
    {
        "id": "diem_D",
        "title": "Điểm về kết quả lãnh đạo, chỉ đạo (D)",
        "source": "Mục 3.a — Nguyên tắc tính điểm KPI",
        "text": (
            "Điểm về kết quả lãnh đạo, chỉ đạo tập thể, cá nhân thuộc thẩm quyền quản lý đối với "
            "cán bộ là lãnh đạo, chỉ huy (D) từ 0 - 01 và được xác định bằng tỷ lệ số tập thể, "
            "cá nhân thuộc thẩm quyền quản lý được đánh giá hoàn thành nhiệm vụ trở lên so với "
            "số tập thể, cá nhân được đánh giá."
        ),
        "keywords": "diem d lanh dao chi huy chi dao thuoc quyen quan ly",
    },
    {
        "id": "cong_thuc_kpi",
        "title": "Công thức tính điểm KPI",
        "source": "Mục 3.b, 3.c, 3.d",
        "text": (
            "KPI tập thể = (A + B + C) / 3 × 100\n"
            "KPI đối với cá nhân không giữ chức vụ lãnh đạo, chỉ huy = (A + B + C) / 3 × 100\n"
            "KPI đối với cá nhân là lãnh đạo, chỉ huy = (A + B + C + D) / 4 × 100\n\n"
            "KPI của người đứng đầu không cao hơn KPI của tập thể, đơn vị do mình đứng đầu."
        ),
        "keywords": "cong thuc kpi tinh diem tap the ca nhan lanh dao chia 3 chia 4 nguoi dung dau",
    },
    {
        "id": "phan_nhom",
        "title": "Phân nhóm cán bộ theo điểm KPI",
        "source": "Mục 5.1 — Sử dụng kết quả",
        "text": (
            "Cán bộ thuộc nhóm đáp ứng tốt yêu cầu nhiệm vụ trở lên (nhóm 1) là cán bộ có điểm KPI "
            "đạt 70 - 100 điểm.\n"
            "Cán bộ thuộc nhóm đáp ứng yêu cầu nhiệm vụ (nhóm 2) là cán bộ có điểm KPI đạt từ 50 "
            "đến dưới 70 điểm.\n"
            "Cán bộ thuộc nhóm chưa đáp ứng yêu cầu nhiệm vụ (nhóm 3) là cán bộ có điểm KPI đạt "
            "dưới 50 điểm."
        ),
        "keywords": "phan nhom xep loai nhom 1 2 3 dap ung yeu cau nguong 70 50",
    },
    {
        "id": "nhom_do_phuc_tap",
        "title": "Nhóm điểm theo mức độ phức tạp của công việc",
        "source": "Mục 2 — Xây dựng Danh mục nhiệm vụ công tác",
        "text": (
            "Điểm đối với từng công việc được xác định trên thang 100 điểm; trong đó, theo tính "
            "chất, mức độ phức tạp của nhiệm vụ, được chia thành 03 nhóm điểm: "
            "Nhóm 1 (0 đến dưới 50 điểm), Nhóm 2 (50 đến dưới 70 điểm), Nhóm 3 (70 đến 100 điểm)."
        ),
        "keywords": "nhom do phuc tap thang 100 diem danh muc cong viec nhom 1 2 3",
    },
    {
        "id": "tong_diem",
        "title": "Tổng điểm dùng trong đánh giá, xếp loại",
        "source": "Mục 5.3 — Sử dụng điểm KPI",
        "text": (
            "Điểm đạt được theo nhóm tiêu chí chung (E): Tối đa 30 điểm.\n"
            "Điểm đạt được theo nhóm tiêu chí về kết quả thực hiện nhiệm vụ: Tối đa 70 điểm, "
            "được xác định bằng Điểm KPI × 0,7.\n\n"
            "Tổng điểm đánh giá đối với tập thể (F) = E + KPI tập thể × 0,7\n"
            "Tổng điểm đánh giá đối với cá nhân (G) = E + KPI cá nhân × 0,7\n"
            "Tổng điểm đánh giá đối với lãnh đạo, chỉ huy (H) = E + KPI lãnh đạo × 0,7"
        ),
        "keywords": "tong diem e f g h tieu chi chung 30 70 nhan 0.7 xep loai",
    },
    {
        "id": "kpi_quy_nam",
        "title": "Điểm KPI hằng quý, hằng năm",
        "source": "Mục 5.2",
        "text": (
            "Điểm KPI đối với tập thể, cá nhân hằng quý, hằng năm được xác định bằng bình quân "
            "điểm KPI đối với tập thể, cá nhân theo hằng tháng."
        ),
        "keywords": "kpi quy nam binh quan hang thang",
    },
    {
        "id": "quy_trinh",
        "title": "Quy trình tính điểm KPI — 03 bước",
        "source": "Mục 1 — Quy trình tính điểm và đề xuất mức xếp loại",
        "text": (
            "Bước 1: Tự đánh giá và đề xuất mức xếp loại. Cá nhân báo cáo kết quả thực hiện nhiệm "
            "vụ; tự nhận xét, đánh giá, xác định mức độ hoàn thành nhiệm vụ và tự chấm điểm kết "
            "quả thực hiện chức trách, nhiệm vụ theo KPI.\n"
            "Bước 2: Các cơ quan có liên quan thẩm định, đề xuất.\n"
            "Bước 3: Cấp có thẩm quyền xác định điểm KPI; sau đó thông báo kết quả bằng hình thức "
            "phù hợp."
        ),
        "keywords": "quy trinh ba buoc tu danh gia tham dinh xac dinh diem thu tuc",
    },
    {
        "id": "tieu_chi_chung",
        "title": "Khung tiêu chí chung (Điểm E)",
        "source": "Phụ lục — Danh mục điểm chấm tiêu chí chung",
        "text": (
            "Điểm tiêu chí chung tối đa 30 điểm, chia theo ba đối tượng:\n"
            f"Tập thể: {len(CRITERIA_TEMPLATES['collective']['criteria'])} tiêu chí, tổng 30 điểm.\n"
            "Cá nhân là lãnh đạo, chỉ huy: 18 + 04 + 08 = 30 điểm.\n"
            "Cá nhân không là lãnh đạo, chỉ huy: 20 + 08 + 02 = 30 điểm.\n"
            "Mỗi tiêu chí chấm theo hai mức: đảm bảo (đạt tối đa điểm) hoặc không đảm bảo (0 điểm)."
        ),
        "keywords": "tieu chi chung diem e 30 diem phu luc dam bao khong dam bao",
    },
    {
        "id": "nhiem_vu_phat_sinh",
        "title": "Nhiệm vụ phát sinh ngoài Khung Danh mục",
        "source": "Mục 2 — Xây dựng Danh mục nhiệm vụ công tác",
        "text": (
            "Trường hợp quá trình công tác, phát sinh nhiệm vụ chưa có trong Khung Danh mục nhiệm "
            "vụ công tác đã phê duyệt; lãnh đạo đơn vị trực tiếp giao nhiệm vụ sẽ xác định về nhóm, "
            "số điểm của nhiệm vụ mới phát sinh và giao tập thể, cá nhân thực hiện nhiệm vụ theo "
            "dõi đánh giá; đến kỳ rà soát gần nhất sẽ đề xuất bổ sung vào Khung Danh mục."
        ),
        "keywords": "nhiem vu phat sinh ngoai danh muc chua co bo sung",
    },
]

# ================= MÁY QUY TẮC CHO CÂU HỎI VỀ SỐ =================
# Lấy trực tiếp từ hằng số của bộ máy chấm điểm nên luôn khớp thực tế.

def _quality_tier_for(revisions: int) -> str:
    if revisions <= 0:
        return "good"
    if revisions == 1:
        return "fair_1"
    if revisions <= 4:
        return "fair_2_4"
    if revisions <= 6:
        return "poor_5_6"
    return "fail_7"


def _timeline_tier_for(reminders: int) -> str:
    if reminders <= 0:
        return "on_time"
    if reminders == 1:
        return "late_1"
    if reminders == 2:
        return "late_2"
    if reminders == 3:
        return "late_3"
    return "fail_4"


_QUALITY_LABEL = {
    "good": "đảm bảo chất lượng",
    "fair_1": "cơ bản đảm bảo, phải chỉnh sửa 01 lần",
    "fair_2_4": "còn thiếu sót, phải chỉnh sửa từ 02 - 04 lần",
    "poor_5_6": "thiếu sót, phải chỉnh sửa từ 05 - 06 lần",
    "fail_7": "phải chỉnh sửa từ 07 lần trở lên",
}

_TIMELINE_LABEL = {
    "on_time": "đảm bảo tiến độ",
    "late_1": "chưa đảm bảo tiến độ, đã bị nhắc nhở 01 lần",
    "late_2": "chưa đảm bảo tiến độ, đã bị nhắc nhở 02 lần",
    "late_3": "chưa đảm bảo tiến độ, đã bị nhắc nhở 03 lần",
    "fail_4": "chưa đảm bảo tiến độ, đã bị nhắc nhở từ 04 lần trở lên",
}


def _answer_revision(n: int) -> Dict[str, Any]:
    tier = _quality_tier_for(n)
    pct = get_quality_percent(tier)
    return {
        "type": "rule",
        "question_understood": f"Công việc phải hoàn thiện, chỉnh sửa {n} lần",
        "answer": (
            f"Được tính {'không quá ' if pct > 0 else ''}{pct * 100:.0f}% số điểm của công việc đó"
            if pct > 0 else "Không được tính điểm"
        ),
        "value_percent": pct * 100,
        "detail": f"Mức đánh giá: {_QUALITY_LABEL[tier]}.",
        "clause_id": "muc_chat_luong",
    }


def _answer_reminder(n: int) -> Dict[str, Any]:
    tier = _timeline_tier_for(n)
    pct = get_timeline_percent(tier)
    return {
        "type": "rule",
        "question_understood": f"Công việc hoàn thành nhưng bị nhắc nhở {n} lần",
        "answer": (
            f"Được tính {'không quá ' if pct > 0 else ''}{pct * 100:.0f}% số điểm của công việc đó"
            if pct > 0 else "Không được tính điểm"
        ),
        "value_percent": pct * 100,
        "detail": f"Mức đánh giá: {_TIMELINE_LABEL[tier]}.",
        "clause_id": "muc_tien_do",
    }


def _answer_group(kpi: float) -> Dict[str, Any]:
    group = determine_kpi_group(kpi)
    label = {
        "group_1": "Nhóm 1 — đáp ứng tốt yêu cầu nhiệm vụ trở lên",
        "group_2": "Nhóm 2 — đáp ứng yêu cầu nhiệm vụ",
        "group_3": "Nhóm 3 — chưa đáp ứng yêu cầu nhiệm vụ",
    }[group]
    return {
        "type": "rule",
        "question_understood": f"Điểm KPI đạt {kpi:g}",
        "answer": f"Xếp vào {label}",
        "value_percent": None,
        "detail": "Ngưỡng: Nhóm 1 từ 70 điểm; Nhóm 2 từ 50 đến dưới 70; Nhóm 3 dưới 50.",
        "clause_id": "phan_nhom",
    }


# Nhận diện ý định từ câu hỏi. Thứ tự quan trọng: xét cụm cụ thể trước.
_RE_NUMBER = r"(\d+)"


def try_rule_engine(question: str) -> Optional[Dict[str, Any]]:
    """
    Nhận diện câu hỏi về con số và trả lời chính xác từ hằng số của hệ thống.
    Trả về None nếu không phải câu hỏi dạng này.
    """
    q = normalize(question)
    numbers = [int(x) for x in re.findall(_RE_NUMBER, q)]

    has_revision = any(k in q for k in ("sua", "chinh sua", "hoan thien"))
    has_reminder = any(k in q for k in ("nhac", "nhac nho", "cham tien do", "tre"))
    has_group = any(k in q for k in ("nhom may", "xep loai", "thuoc nhom", "phan nhom"))

    # Cách diễn đạt không dùng chữ số: "không phải sửa lần nào", "đúng hạn"
    if not numbers:
        if any(k in q for k in ("khong phai sua", "khong sua", "khong lan nao", "dam bao chat luong")):
            return _answer_revision(0)
        if any(k in q for k in ("khong bi nhac", "dung han", "dam bao tien do", "khong nhac")):
            return _answer_reminder(0)
        # "không phải sửa lần nào" — bắt trường hợp chung có "khong" đi với sửa/nhắc
        if "khong" in q and has_revision:
            return _answer_revision(0)
        if "khong" in q and has_reminder:
            return _answer_reminder(0)

    if has_group and numbers:
        # "KPI 65 thì thuộc nhóm mấy"
        candidate = next((n for n in numbers if 0 <= n <= 120), None)
        if candidate is not None:
            return _answer_group(float(candidate))

    if has_revision and not has_reminder and numbers:
        return _answer_revision(numbers[0])

    if has_reminder and not has_revision and numbers:
        return _answer_reminder(numbers[0])

    # Câu hỏi nêu cả hai: trả lời cả hai
    if has_revision and has_reminder and len(numbers) >= 2:
        return {
            "type": "rule",
            "question_understood": f"Chỉnh sửa {numbers[0]} lần và bị nhắc nhở {numbers[1]} lần",
            "answer": (
                f"Chất lượng (B): {get_quality_percent(_quality_tier_for(numbers[0])) * 100:.0f}% · "
                f"Tiến độ (C): {get_timeline_percent(_timeline_tier_for(numbers[1])) * 100:.0f}%"
            ),
            "value_percent": None,
            "detail": "Hai tiêu chí tính độc lập, mỗi tiêu chí áp mức riêng.",
            "clause_id": "muc_chat_luong",
        }

    return None


# ================= TÌM KIẾM ĐIỀU KHOẢN =================

def _score_clause(clause: Dict[str, Any], tokens: List[str]) -> int:
    """Đếm số từ khoá khớp, ưu tiên khớp ở tiêu đề và danh sách từ khoá."""
    title_n = normalize(clause["title"])
    kw_n = clause["keywords"]
    body_n = normalize(clause["text"])

    score = 0
    for t in tokens:
        if len(t) < 2:
            continue
        if t in kw_n:
            score += 3
        if t in title_n:
            score += 2
        if t in body_n:
            score += 1
    return score


_STOPWORDS = {
    "la", "thi", "va", "co", "cua", "cho", "duoc", "bao", "nhieu", "gi", "nao",
    "the", "khi", "mot", "cac", "nhung", "voi", "trong", "ve", "o", "den",
}


def search_clauses(question: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Tìm điều khoản liên quan nhất tới câu hỏi."""
    tokens = [t for t in normalize(question).split() if t not in _STOPWORDS]
    scored = [(_score_clause(c, tokens), c) for c in CLAUSES]
    scored = [(s, c) for s, c in scored if s > 0]
    scored.sort(key=lambda x: -x[0])
    return [
        {
            "id": c["id"],
            "title": c["title"],
            "source": c["source"],
            "text": c["text"],
            "match_score": s,
        }
        for s, c in scored[:limit]
    ]


def get_clause(clause_id: str) -> Optional[Dict[str, Any]]:
    for c in CLAUSES:
        if c["id"] == clause_id:
            return {k: v for k, v in c.items() if k != "keywords"}
    return None


def answer(question: str) -> Dict[str, Any]:
    """
    Trả lời một câu hỏi về Hướng dẫn.

    Ưu tiên máy quy tắc (chính xác tuyệt đối cho câu hỏi về số), sau đó bổ sung
    các điều khoản liên quan để cán bộ đọc nguyên văn.
    """
    rule = try_rule_engine(question)
    clauses = search_clauses(question)

    # Nếu máy quy tắc trả lời được, đưa điều khoản gốc lên đầu
    if rule:
        cited = get_clause(rule["clause_id"])
        clauses = [c for c in clauses if c["id"] != rule["clause_id"]]
        if cited:
            clauses.insert(0, {**cited, "match_score": 99})

    return {
        "question": question,
        "rule_answer": rule,
        "clauses": clauses,
        "explanation": (
            "Câu trả lời về số lấy trực tiếp từ hằng số của bộ máy chấm điểm, "
            "nên luôn khớp với điều hệ thống thực sự tính. "
            "Trích dẫn là nguyên văn Hướng dẫn số 20-HD/ĐUCA."
            if rule else
            "Không nhận diện được câu hỏi về số. Dưới đây là các điều khoản liên quan nhất."
        ),
        "source_document": "Hướng dẫn số 20-HD/ĐUCA ngày 08/6/2026",
        "precision_note": (
            f"Hệ thống ghi điểm A, B, C ở {SCORE_PRECISION} chữ số thập phân "
            f"và điểm KPI ở {KPI_PRECISION} chữ số thập phân, đúng như Phụ lục."
        ),
    }
