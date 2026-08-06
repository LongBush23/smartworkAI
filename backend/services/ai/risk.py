"""
Cảnh báo sớm nguy cơ, để lãnh đạo can thiệp GIỮA kỳ thay vì biết khi đã hết kỳ.

Hai mô hình, đều là hồi quy logistic:
  2a. Nguy cơ cán bộ rơi Nhóm 3 khi kết thúc kỳ
  2b. Nguy cơ một nhiệm vụ hoàn thành trễ hạn

VÌ SAO CHỌN HỒI QUY LOGISTIC
----------------------------
Cần giải thích được. Với hồi quy logistic, đóng góp của từng đặc trưng vào kết
quả là `hệ số × giá trị`, in ra thành lời được. Mô hình phức tạp hơn có thể
chính xác hơn vài phần trăm nhưng không nói được vì sao — cơ quan nhà nước
không dùng được thứ đó để ra quyết định về con người.

Mô hình chỉ CẢNH BÁO. Không sửa điểm của ai, không ghi vào `approval`.
"""
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from backend.database import db

# Dưới ngưỡng này thì mô hình không đáng tin, không được đưa ra dùng
AUC_TOI_THIEU = 0.70
SO_MAU_TOI_THIEU = 80

# CÁCH ĐỌC CHỈ SỐ AUC TRÊN DỮ LIỆU MẪU
# -------------------------------------
# Trên dữ liệu mẫu do seeder sinh ra, AUC rất cao (khoảng 0,99) vì nhiệm vụ và
# kỳ đánh giá đều bắt nguồn từ cùng một mức năng lực theo tháng — mô hình gần
# như khôi phục lại đúng quy tắc sinh dữ liệu.
#
# ĐÂY KHÔNG PHẢI DỰ BÁO VỀ HIỆU QUẢ THỰC TẾ. Với dữ liệu thật, con người không
# hành xử theo quy tắc cố định, nên AUC sẽ thấp hơn đáng kể. Chỉ số đáng tin duy
# nhất là chỉ số đo trên dữ liệu vận hành thật sau vài kỳ.
# Vì vậy endpoint /api/ai/retrain luôn trả về AUC và ma trận nhầm lẫn để người
# quản trị tự thẩm định, thay vì giấu đi sau một con số đẹp.

# Bộ nhớ đệm mô hình trong tiến trình. Huấn luyện lại bằng POST /api/ai/retrain
_cache: Dict[str, Any] = {}


# ================= 2b. NGUY CƠ NHIỆM VỤ TRỄ HẠN =================

DAC_TRUNG_TRE_HAN = [
    "so_lan_nhac", "so_lan_sua", "ty_le_hoan_thanh",
    "diem_nhiem_vu", "nhom_do_phuc_tap", "tong_so_ngay",
]


def _features_task_late(task: dict, now: datetime) -> Optional[List[float]]:
    deadline = task.get("deadline")
    assigned_at = task.get("assigned_at")
    if not deadline:
        return None

    qty_assigned = task.get("quantity_assigned", 1) or 1
    total_days = (deadline - assigned_at).days if assigned_at else 20

    return [
        float(min(task.get("reminder_count", 0), 6)),
        float(min(task.get("revision_count", 0), 8)),
        float(task.get("quantity_completed", 0) or 0) / qty_assigned,
        float(task.get("kpi_point", 0)) / 100.0,
        float(task.get("complexity_group") or 2),
        float(max(total_days, 1)),
    ]


async def train_task_late_model() -> Dict[str, Any]:
    """Huấn luyện từ các nhiệm vụ đã kết thúc, nhãn là hoàn thành trễ hay không."""
    now = datetime.utcnow()
    # Chỉ lấy đúng trường cần dùng — kéo cả tài liệu về sẽ rất nặng khi cơ sở
    # dữ liệu lớn dần, và endpoint này chạy trên kết nối từ xa
    tasks = await db.tasks.find(
        {"status": "done"},
        {
            "deadline": 1, "actual_end": 1, "assigned_at": 1, "reminder_count": 1,
            "revision_count": 1, "quantity_assigned": 1, "quantity_completed": 1,
            "kpi_point": 1, "complexity_group": 1,
        },
    ).to_list(20000)

    X, y = [], []
    for t in tasks:
        if not t.get("actual_end") or not t.get("deadline"):
            continue
        f = _features_task_late(t, now)
        if f is None:
            continue
        X.append(f)
        y.append(1 if t["actual_end"] > t["deadline"] else 0)

    result = _fit_and_evaluate(X, y, DAC_TRUNG_TRE_HAN, "nhiệm vụ trễ hạn")
    _cache["task_late"] = result
    return result


# ================= 2a. NGUY CƠ RƠI NHÓM 3 =================

DAC_TRUNG_NHOM_3 = [
    "ty_le_diem_hoan_thanh", "ty_le_viec_xong", "so_lan_sua_tich_luy",
    "so_lan_nhac_tich_luy", "so_viec_qua_han", "kpi_binh_quan_truoc",
    "xu_the_kpi", "tai_viec",
]


def _features_officer(
    tasks: List[dict], capacity: int, past_kpi: List[float], now: datetime,
) -> List[float]:
    total_points = sum(t.get("kpi_point", 0) * (t.get("quantity_assigned", 1) or 1) for t in tasks)
    done = [t for t in tasks if t.get("status") == "done"]
    done_points = sum(t.get("kpi_point", 0) * (t.get("quantity_completed", 0) or 0) for t in done)

    overdue = sum(
        1 for t in tasks
        if t.get("status") != "done" and t.get("deadline") and t["deadline"] < now
    )
    open_points = total_points - done_points

    if len(past_kpi) >= 2:
        trend = past_kpi[-1] - past_kpi[0]
    else:
        trend = 0.0

    return [
        done_points / total_points if total_points else 0.0,
        len(done) / len(tasks) if tasks else 0.0,
        float(sum(t.get("revision_count", 0) for t in tasks)),
        float(sum(t.get("reminder_count", 0) for t in tasks)),
        float(overdue),
        float(sum(past_kpi) / len(past_kpi)) if past_kpi else 70.0,
        float(trend),
        open_points / capacity if capacity else 0.0,
    ]


async def train_group3_model() -> Dict[str, Any]:
    """
    Huấn luyện từ các kỳ đã duyệt: dùng nhiệm vụ của kỳ đó để dựng đặc trưng,
    nhãn là cán bộ có rơi Nhóm 3 hay không.
    """
    now = datetime.utcnow()
    evaluations = await db.kpi_evaluations.find({
        "evaluation_type": "individual",
        "period_type": "monthly",
        "overall_status": "approved",
    }).to_list(20000)

    users = {
        str(u["_id"]): u
        for u in await db.users.find({}, {"capacity_points": 1}).to_list(2000)
    }
    all_tasks = await db.tasks.find(
        {},
        {
            "assigned_to": 1, "period_month": 1, "period_year": 1, "status": 1,
            "deadline": 1, "kpi_point": 1, "quantity_assigned": 1,
            "quantity_completed": 1, "revision_count": 1, "reminder_count": 1,
        },
    ).to_list(30000)

    tasks_index: Dict[Tuple[str, int, int], List[dict]] = {}
    for t in all_tasks:
        key = (t.get("assigned_to"), t.get("period_month"), t.get("period_year"))
        tasks_index.setdefault(key, []).append(t)

    # Lịch sử KPI theo cán bộ, sắp theo thời gian
    history: Dict[str, List[Tuple[Tuple[int, int], float]]] = {}
    for e in evaluations:
        score = (e.get("approval") or {}).get("kpi_score")
        if score is None:
            continue
        history.setdefault(e["target_id"], []).append(
            ((e.get("period_year"), e.get("period_month")), score)
        )
    for uid in history:
        history[uid].sort()

    X, y = [], []
    for e in evaluations:
        uid = e["target_id"]
        group = (e.get("approval") or {}).get("kpi_group")
        if not group:
            continue

        period = (e.get("period_year"), e.get("period_month"))
        tasks = tasks_index.get((uid, e.get("period_month"), e.get("period_year")), [])
        if not tasks:
            continue

        past = [s for p, s in history.get(uid, []) if p < period][-3:]
        capacity = int(users.get(uid, {}).get("capacity_points", 300) or 300)

        X.append(_features_officer(tasks, capacity, past, now))
        y.append(1 if group == "group_3" else 0)

    result = _fit_and_evaluate(X, y, DAC_TRUNG_NHOM_3, "rơi Nhóm 3")
    _cache["group3"] = result
    return result


# ================= HUẤN LUYỆN VÀ ĐÁNH GIÁ =================

def _fit_and_evaluate(
    X: List[List[float]], y: List[int], feature_names: List[str], label: str,
) -> Dict[str, Any]:
    """
    Huấn luyện và đánh giá trung thực trên tập kiểm tra tách riêng.

    Nếu AUC dưới ngưỡng thì đánh dấu KHÔNG DÙNG ĐƯỢC — thà không có cảnh báo
    còn hơn cảnh báo sai làm lãnh đạo mất niềm tin vào cả hệ thống.
    """
    n = len(X)
    positives = sum(y)

    if n < SO_MAU_TOI_THIEU or positives < 10 or positives == n:
        return {
            "usable": False,
            "reason": (
                f"Không đủ dữ liệu để huấn luyện mô hình {label}: "
                f"{n} mẫu, {positives} trường hợp dương"
            ),
            "n_samples": n, "n_positive": positives,
        }

    Xa, ya = np.array(X, dtype=float), np.array(y, dtype=int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        Xa, ya, test_size=0.2, random_state=42, stratify=ya
    )

    scaler = StandardScaler().fit(X_tr)
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(scaler.transform(X_tr), y_tr)

    proba = model.predict_proba(scaler.transform(X_te))[:, 1]
    auc = float(roc_auc_score(y_te, proba))
    pred = (proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_te, pred, labels=[0, 1]).ravel()

    usable = auc >= AUC_TOI_THIEU
    return {
        "usable": usable,
        "reason": None if usable else (
            f"AUC {auc:.3f} dưới ngưỡng {AUC_TOI_THIEU} — mô hình {label} chưa đáng tin, "
            "không đưa ra sử dụng"
        ),
        "model": model, "scaler": scaler, "feature_names": feature_names,
        "auc": round(auc, 3),
        "n_samples": n, "n_positive": positives,
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "coefficients": {
            name: round(float(c), 3)
            for name, c in zip(feature_names, model.coef_[0])
        },
        "trained_at": datetime.utcnow().isoformat(),
    }


# Tên đặc trưng và cách mô tả khi giá trị CAO hơn / THẤP hơn mức trung bình.
# Nói thẳng điều quan sát được thay vì "yếu tố X làm tăng nguy cơ" — câu đó
# mơ hồ, người đọc không biết là do giá trị cao hay thấp.
_MO_TA_DAC_TRUNG = {
    "so_lan_nhac":           ("bị nhắc nhở nhiều lần", "hầu như không bị nhắc nhở"),
    "so_lan_sua":            ("phải chỉnh sửa nhiều lần", "hầu như không phải chỉnh sửa"),
    "ty_le_hoan_thanh":      ("đã hoàn thành phần lớn số lượng", "mới hoàn thành được ít"),
    "diem_nhiem_vu":         ("nhiệm vụ có điểm cao", "nhiệm vụ có điểm thấp"),
    "nhom_do_phuc_tap":      ("thuộc nhóm phức tạp cao", "thuộc nhóm ít phức tạp"),
    "tong_so_ngay":          ("thời gian thực hiện dài", "thời gian thực hiện ngắn"),
    "ty_le_diem_hoan_thanh": ("đã đạt phần lớn số điểm được giao", "mới đạt được ít điểm"),
    "ty_le_viec_xong":       ("đã xong phần lớn số việc", "còn nhiều việc chưa xong"),
    "so_lan_sua_tich_luy":   ("phải chỉnh sửa nhiều lần trong kỳ", "ít phải chỉnh sửa"),
    "so_lan_nhac_tich_luy":  ("bị nhắc nhở nhiều lần trong kỳ", "ít bị nhắc nhở"),
    "so_viec_qua_han":       ("có nhiều việc quá hạn", "không tồn việc quá hạn"),
    "kpi_binh_quan_truoc":   ("KPI các kỳ trước cao", "KPI các kỳ trước thấp"),
    "xu_the_kpi":            ("KPI đang đi lên", "KPI đang đi xuống"),
    "tai_viec":              ("khối lượng còn tồn lớn", "khối lượng còn tồn ít"),
}


def _explain(bundle: Dict[str, Any], features: List[float], top: int = 3) -> List[str]:
    """
    Nêu các yếu tố đóng góp nhiều nhất vào xác suất.

    Mỗi yếu tố nói rõ hai điều: quan sát được gì (giá trị cao hay thấp so với
    mức trung bình) và điều đó đẩy nguy cơ lên hay xuống.
    """
    scaled = bundle["scaler"].transform([features])[0]
    rows = [
        (name, float(val), float(coef) * float(val))
        for name, coef, val in zip(
            bundle["feature_names"], bundle["model"].coef_[0], scaled
        )
    ]
    rows.sort(key=lambda r: -abs(r[2]))

    out = []
    for name, scaled_val, contrib in rows[:top]:
        cao, thap = _MO_TA_DAC_TRUNG.get(name, (name, name))
        quan_sat = cao if scaled_val >= 0 else thap
        huong = "tăng nguy cơ" if contrib > 0 else "giảm nguy cơ"
        out.append(f"{quan_sat} → {huong}")
    return out


# ================= DỰ BÁO =================

async def _ensure(key: str):
    if key not in _cache:
        if key == "task_late":
            await train_task_late_model()
        else:
            await train_group3_model()
    return _cache[key]


async def predict_task_risk(
    department_id: Optional[str] = None,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """Nhiệm vụ đang mở nào có nguy cơ trễ hạn."""
    bundle = await _ensure("task_late")
    now = datetime.utcnow()
    month = period_month or now.month
    year = period_year or now.year

    if not bundle.get("usable"):
        return {"usable": False, "reason": bundle.get("reason"), "items": []}

    query: Dict[str, Any] = {
        "status": {"$ne": "done"},
        "period_month": month,
        "period_year": year,
    }
    if department_id:
        query["department_id"] = department_id

    tasks = await db.tasks.find(query).to_list(5000)
    users = {str(u["_id"]): u.get("name") for u in await db.users.find({}).to_list(2000)}

    items = []
    for t in tasks:
        f = _features_task_late(t, now)
        if f is None:
            continue
        p = float(bundle["model"].predict_proba(bundle["scaler"].transform([f]))[0, 1])
        if p < threshold:
            continue
        deadline = t.get("deadline")
        items.append({
            "task_id": str(t["_id"]),
            "code": t.get("code"),
            # Nhiệm vụ có độ mật chỉ hiện mã hiệu, không lộ tên gọi
            "title": t.get("code") if t.get("classification") != "thuong" else t.get("title"),
            "classification": t.get("classification", "thuong"),
            "assignee_name": users.get(t.get("assigned_to") or ""),
            "deadline": deadline,
            "days_left": (deadline - now).days if deadline else None,
            "reminder_count": t.get("reminder_count", 0),
            "revision_count": t.get("revision_count", 0),
            "probability": round(p, 3),
            "reasons": _explain(bundle, f),
        })

    items.sort(key=lambda x: -x["probability"])
    return {
        "usable": True,
        "auc": bundle["auc"],
        "period_month": month, "period_year": year,
        "threshold": threshold,
        "items": items,
        "explanation": (
            "Xác suất nhiệm vụ hoàn thành trễ hạn, ước lượng từ lịch sử các kỳ trước. "
            "Đây là cảnh báo để đôn đốc, không ảnh hưởng tới điểm KPI."
        ),
    }


async def predict_officer_risk(
    department_id: Optional[str] = None,
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """Cán bộ nào có nguy cơ rơi Nhóm 3 khi kết thúc kỳ."""
    bundle = await _ensure("group3")
    now = datetime.utcnow()
    month = period_month or now.month
    year = period_year or now.year

    if not bundle.get("usable"):
        return {"usable": False, "reason": bundle.get("reason"), "items": []}

    uq: Dict[str, Any] = {"role": {"$ne": "admin"}}
    if department_id:
        uq["department_id"] = department_id
    users = await db.users.find(uq).to_list(2000)

    tq: Dict[str, Any] = {"period_month": month, "period_year": year}
    if department_id:
        tq["department_id"] = department_id
    tasks = await db.tasks.find(tq).to_list(20000)

    by_user: Dict[str, List[dict]] = {}
    for t in tasks:
        if t.get("assigned_to"):
            by_user.setdefault(t["assigned_to"], []).append(t)

    evaluations = await db.kpi_evaluations.find({
        "evaluation_type": "individual", "period_type": "monthly",
        "overall_status": "approved",
    }).to_list(20000)
    history: Dict[str, List[Tuple[Tuple[int, int], float]]] = {}
    for e in evaluations:
        s = (e.get("approval") or {}).get("kpi_score")
        if s is not None:
            history.setdefault(e["target_id"], []).append(
                ((e.get("period_year"), e.get("period_month")), s)
            )
    for uid in history:
        history[uid].sort()

    items = []
    for u in users:
        uid = str(u["_id"])
        my_tasks = by_user.get(uid, [])
        if not my_tasks:
            continue

        past = [s for p, s in history.get(uid, []) if p < (year, month)][-3:]
        capacity = int(u.get("capacity_points", 300) or 300)
        f = _features_officer(my_tasks, capacity, past, now)
        p = float(bundle["model"].predict_proba(bundle["scaler"].transform([f]))[0, 1])
        if p < threshold:
            continue

        done = [t for t in my_tasks if t.get("status") == "done"]
        items.append({
            "officer_id": uid,
            "name": u.get("name"),
            "rank_position": " · ".join(x for x in (u.get("rank"), u.get("position")) if x),
            "department_id": u.get("department_id"),
            "probability": round(p, 3),
            "tasks_total": len(my_tasks),
            "tasks_done": len(done),
            "tasks_overdue": sum(
                1 for t in my_tasks
                if t.get("status") != "done" and t.get("deadline") and t["deadline"] < now
            ),
            "recent_kpi": round(sum(past) / len(past), 1) if past else None,
            "reasons": _explain(bundle, f),
        })

    items.sort(key=lambda x: -x["probability"])
    return {
        "usable": True,
        "auc": bundle["auc"],
        "period_month": month, "period_year": year,
        "threshold": threshold,
        "items": items,
        "explanation": (
            "Xác suất cán bộ rơi Nhóm 3 khi kết thúc kỳ, ước lượng từ tiến độ hiện tại và "
            "lịch sử các kỳ trước. Đây là cảnh báo để lãnh đạo đôn đốc, hỗ trợ kịp thời — "
            "KHÔNG phải kết quả đánh giá và không ảnh hưởng tới điểm KPI."
        ),
    }


async def retrain_all() -> Dict[str, Any]:
    """Huấn luyện lại cả hai mô hình, trả về chất lượng để người quản trị thẩm định."""
    _cache.clear()
    late = await train_task_late_model()
    group3 = await train_group3_model()

    def report(b):
        return {
            "usable": b.get("usable"),
            "reason": b.get("reason"),
            "auc": b.get("auc"),
            "n_samples": b.get("n_samples"),
            "n_positive": b.get("n_positive"),
            "confusion": b.get("confusion"),
            "coefficients": b.get("coefficients"),
        }

    return {
        "task_late": report(late),
        "group3": report(group3),
        "auc_threshold": AUC_TOI_THIEU,
        "note": (
            "AUC dưới ngưỡng nghĩa là mô hình chưa đáng tin và sẽ không được dùng để "
            "cảnh báo. Thà không có cảnh báo còn hơn cảnh báo sai."
        ),
    }
