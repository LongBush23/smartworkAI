"""
Mô phỏng cán bộ đi làm — đẩy dữ liệu mẫu tiến lên theo từng ngày làm việc.

VÌ SAO CẦN
----------
Dữ liệu mẫu do seeder sinh ra đứng yên tại thời điểm chạy. Sau vài ngày, bản
demo trông như cả đơn vị nghỉ làm: nhiệm vụ quá hạn chồng chất mà không ai
đụng tới, không có nhắc nhở, không ý kiến trao đổi, kỳ đánh giá đứng nguyên
một chỗ.

Script này KHÔNG sinh lại dữ liệu (khác hẳn seeder — seeder xoá sạch rồi tạo
mới). Nó đọc dữ liệu đang có và mô phỏng đúng những việc cán bộ làm mỗi ngày:
nhận việc, làm dần, trình lãnh đạo, bị yêu cầu chỉnh sửa, bị nhắc nhở tiến độ,
trao đổi ý kiến, và đi tiếp quy trình đánh giá 03 bước.

NGUYÊN TẮC GIỮ ĐÚNG NGHIỆP VỤ
-----------------------------
  * Số lần chỉnh sửa và số lần nhắc nhở chỉ tăng qua đúng hai thao tác của
    lãnh đạo, giống hệt endpoint thật, nên điểm B và C vẫn suy ra từ dữ liệu
    có thật.
  * Khi xác định điểm KPI, script gọi thẳng process_evaluation_approval của
    kpi_service — cùng một hàm mà máy chủ dùng — nên số liệu luôn khớp công
    thức của Hướng dẫn 20-HD/ĐUCA.
  * Mức chất lượng, tiến độ suy từ số lần sửa / nhắc theo đúng bảng mức, dùng
    lại hàm ánh xạ của mô-đun tra cứu văn bản thay vì chép tay bảng mức.
  * Luôn chừa lại ít nhất 2 hồ sơ ở mỗi trạng thái quy trình, để bản demo
    không bị trôi hết về "đã xác định điểm KPI" và mất độ phủ.

CÁCH CHẠY
---------
    python -m backend.scripts.mo_phong_cong_tac              # chạy tới hôm nay
    python -m backend.scripts.mo_phong_cong_tac --ngay 5     # ép mô phỏng 5 ngày làm việc
    python -m backend.scripts.mo_phong_cong_tac --thu        # chỉ xem, không ghi

Script ghi lại ngày đã mô phỏng vào collection `demo_state`, nên chạy lại
nhiều lần cũng không nhân đôi dữ liệu.
"""
import argparse
import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database import db
from backend.models.kpi_criteria import criteria_type_for, flatten_criteria
from backend.services.kpi_service import process_evaluation_approval
# Ánh xạ số lần sửa / nhắc sang mức điểm — dùng lại của mô-đun tra cứu Hướng dẫn
# để không chép tay bảng mức ra thêm một chỗ nữa.
from backend.services.ai.guideline import _quality_tier_for, _timeline_tier_for

# ================= THAM SỐ MÔ PHỎNG =================

# Xác suất mỗi ngày, đặt tập trung ở đây để dễ chỉnh
XS = {
    "bat_dau_viec":      0.45,   # cán bộ bắt đầu một việc đang chờ
    "lam_tiep":          0.55,   # làm tiếp một việc đang thực hiện
    "lanh_dao_duyet":    0.70,   # lãnh đạo duyệt việc đã trình
    "yeu_cau_sua":       0.28,   # lãnh đạo yêu cầu hoàn thiện, chỉnh sửa
    "nhac_nho":          0.30,   # nhắc nhở một việc quá hạn
    "trao_doi":          0.22,   # để lại ý kiến trao đổi
    "viec_dot_xuat":     0.30,   # đơn vị phát sinh nhiệm vụ đột xuất
}

# Trần để dữ liệu không phi lý: quá các mốc này thì mức điểm đã bằng 0 rồi
TRAN_NHAC_NHO = 4
TRAN_CHINH_SUA = 7

# Hạn mức mỗi ngày. Không có mấy con số này thì lãnh đạo "duyệt sạch" hàng đợi
# ngay ngày đầu — cả trăm nhiệm vụ hoàn thành cùng lúc, nhìn là biết máy sinh.
MOI_NGAY_DUYET = 6       # mỗi đơn vị xem xét tối đa bấy nhiêu việc đã trình
MOI_NGAY_NHAC = 4        # mỗi đơn vị nhắc nhở tối đa bấy nhiêu việc quá hạn
MOI_NGAY_Y_KIEN = 12     # số ý kiến trao đổi toàn hệ thống

# Mỗi ngày đẩy tối đa bấy nhiêu hồ sơ đánh giá đi tiếp một bước
MOI_NGAY_TOI_DA_HO_SO = 2
# Luôn chừa lại tối thiểu bấy nhiêu hồ sơ ở mỗi trạng thái
GIU_LAI_MOI_TRANG_THAI = 2

GIO_LAM = (8, 17)

Y_KIEN = [
    "Đề nghị đồng chí bổ sung căn cứ pháp lý trong dự thảo.",
    "Sản phẩm đã đảm bảo yêu cầu, đề nghị trình lãnh đạo phê duyệt.",
    "Cần đẩy nhanh tiến độ, đã sát thời hạn theo kế hoạch.",
    "Nội dung còn thiếu sót, đề nghị hoàn thiện và trình lại.",
    "Đã đối chiếu với Danh mục nhiệm vụ công tác, số liệu phù hợp.",
    "Nhất trí với đề xuất; đề nghị phối hợp với đơn vị liên quan.",
    "Đề nghị rà soát lại số liệu tại mục 2 trước khi trình.",
    "Đã tiếp thu ý kiến, đang hoàn thiện để trình lại trong tuần.",
]

CAN_CU_GIAO = [
    "Kế hoạch công tác tháng của đơn vị",
    "Chỉ đạo trực tiếp của lãnh đạo đơn vị",
    "Công văn chỉ đạo của cấp trên",
    "Nhiệm vụ đột xuất theo yêu cầu nghiệp vụ",
]


class Dem:
    """Đếm việc đã làm để báo cáo lại cuối lượt chạy."""

    def __init__(self):
        self.so = {}

    def cong(self, khoa: str, n: int = 1):
        self.so[khoa] = self.so.get(khoa, 0) + n

    def in_ra(self):
        if not self.so:
            print("  (không có thay đổi nào)")
            return
        nhan = {
            "bat_dau": "Bắt đầu thực hiện nhiệm vụ",
            "lam_tiep": "Cập nhật khối lượng đã hoàn thành",
            "trinh": "Trình lãnh đạo xem xét",
            "hoan_thanh": "Hoàn thành nhiệm vụ",
            "yeu_cau_sua": "Yêu cầu hoàn thiện, chỉnh sửa (→ điểm B)",
            "nhac_nho": "Nhắc nhở tiến độ (→ điểm C)",
            "y_kien": "Ý kiến trao đổi",
            "viec_moi": "Nhiệm vụ đột xuất được giao",
            "viec_ky_moi": "Nhiệm vụ giao đầu kỳ mới",
            "tu_danh_gia": "Bước 1 — tự đánh giá",
            "tham_dinh": "Bước 2 — thẩm định",
            "xac_dinh_kpi": "Bước 3 — xác định điểm KPI",
            "ky_moi": "Mở kỳ đánh giá tháng mới",
        }
        for k, v in self.so.items():
            print(f"  {nhan.get(k, k):45} {v:>5}")


# ================= TIỆN ÍCH =================

def ngay_lam_viec(d: datetime) -> bool:
    """Thứ Bảy, Chủ nhật thì cán bộ không đi làm."""
    return d.weekday() < 5


def gio_ngau_nhien(d: datetime, rng: random.Random) -> datetime:
    return d.replace(
        hour=rng.randint(*GIO_LAM), minute=rng.randint(0, 59),
        second=rng.randint(0, 59), microsecond=0,
    )


async def ghi_nhat_ky(user_id, user_name, action, target_type, target_id, details, luc):
    await db.audit_logs.insert_one({
        "user_id": str(user_id), "user_name": user_name,
        "action": action, "target_type": target_type,
        "target_id": str(target_id), "details": details,
        "created_at": luc,
    })


async def gui_thong_bao(user_id, loai, tieu_de, noi_dung, ref_id, luc, rng):
    await db.notifications.insert_one({
        "user_id": str(user_id), "type": loai,
        "title": tieu_de, "message": noi_dung,
        "reference_id": str(ref_id), "reference_type": "task",
        "is_read": rng.random() < 0.35,
        "created_at": luc,
    })


# ================= MỘT NGÀY LÀM VIỆC =================

async def mot_ngay(d: datetime, rng: random.Random, dem: Dem, that: bool):
    users = await db.users.find({"role": {"$ne": "admin"}}).to_list(None)
    theo_don_vi: Dict[str, List[dict]] = {}
    for u in users:
        if u.get("department_id"):
            theo_don_vi.setdefault(u["department_id"], []).append(u)

    ten = {str(u["_id"]): u.get("name", "") for u in users}

    # ---------- 1. Cán bộ thực hiện nhiệm vụ ----------
    for u in users:
        uid = str(u["_id"])
        viec = await db.tasks.find({
            "assigned_to": uid,
            "status": {"$in": ["assigned", "in_progress"]},
        }).sort("deadline", 1).to_list(60)
        if not viec:
            continue

        # bắt đầu một việc đang chờ
        cho = [t for t in viec if t.get("status") == "assigned"]
        if cho and rng.random() < XS["bat_dau_viec"]:
            t = cho[0]
            luc = gio_ngau_nhien(d, rng)
            if that:
                await db.tasks.update_one({"_id": t["_id"]}, {"$set": {"status": "in_progress"}})
                await ghi_nhat_ky(uid, ten[uid], "task.updated", "task", t["_id"],
                                  "Bắt đầu thực hiện", luc)
            dem.cong("bat_dau")

        # làm tiếp một việc đang thực hiện
        dang_lam = [t for t in viec if t.get("status") == "in_progress"]
        if dang_lam and rng.random() < XS["lam_tiep"]:
            t = rng.choice(dang_lam)
            giao = t.get("quantity_assigned", 1) or 1
            xong = t.get("quantity_completed", 0) or 0
            luc = gio_ngau_nhien(d, rng)

            if xong + 1 >= giao:
                # xong khối lượng → trình lãnh đạo xem xét
                if that:
                    await db.tasks.update_one({"_id": t["_id"]}, {"$set": {
                        "quantity_completed": giao, "status": "review",
                    }})
                    await ghi_nhat_ky(uid, ten[uid], "task.updated", "task", t["_id"],
                                      "Trình lãnh đạo xem xét", luc)
                dem.cong("trinh")
            else:
                if that:
                    await db.tasks.update_one({"_id": t["_id"]},
                                              {"$inc": {"quantity_completed": 1}})
                dem.cong("lam_tiep")

    # ---------- 2. Lãnh đạo xem xét, nhắc nhở ----------
    for dept_id, ds in theo_don_vi.items():
        chi_huy = [u for u in ds if u.get("role") in ("leader", "director")]
        if not chi_huy:
            continue
        sep = rng.choice(chi_huy)
        sid, sten = str(sep["_id"]), sep.get("name", "")

        # 2a. việc đã trình — mỗi ngày chỉ xem xét được một số việc
        da_trinh = await db.tasks.find({
            "department_id": dept_id, "status": "review",
        }).to_list(200)
        rng.shuffle(da_trinh)

        for t in da_trinh[:MOI_NGAY_DUYET]:
            nguoi_lam = t.get("assigned_to")
            if not nguoi_lam or nguoi_lam == sid:
                continue
            luc = gio_ngau_nhien(d, rng)

            if rng.random() < XS["yeu_cau_sua"] and t.get("revision_count", 0) < TRAN_CHINH_SUA:
                lan = t.get("revision_count", 0) + 1
                if that:
                    await db.tasks.update_one({"_id": t["_id"]},
                                              {"$inc": {"revision_count": 1}})
                    await gui_thong_bao(
                        nguoi_lam, "task_revision",
                        f"Yêu cầu hoàn thiện, chỉnh sửa (lần {lan}) 📝",
                        f"Nhiệm vụ \"{t.get('code') or t.get('title')}\" cần hoàn thiện, "
                        f"chỉnh sửa. Đây là lần thứ {lan}.",
                        t["_id"], luc, rng)
                    await ghi_nhat_ky(sid, sten, "task.revision_requested", "task",
                                      t["_id"], f"Lần thứ {lan}", luc)
                dem.cong("yeu_cau_sua")

            elif rng.random() < XS["lanh_dao_duyet"]:
                if that:
                    await db.tasks.update_one({"_id": t["_id"]}, {"$set": {
                        "status": "done",
                        "actual_end": luc,
                        "quantity_completed": t.get("quantity_assigned", 1) or 1,
                    }})
                    await gui_thong_bao(
                        nguoi_lam, "task_completed", "Nhiệm vụ đã được ghi nhận hoàn thành ✅",
                        f"Nhiệm vụ \"{t.get('code') or t.get('title')}\" đã được lãnh đạo "
                        f"ghi nhận hoàn thành.", t["_id"], luc, rng)
                    await ghi_nhat_ky(sid, sten, "task.updated", "task", t["_id"],
                                      "Ghi nhận hoàn thành", luc)
                dem.cong("hoan_thanh")

        # 2b. việc quá hạn → nhắc nhở tiến độ
        qua_han = await db.tasks.find({
            "department_id": dept_id,
            "status": {"$ne": "done"},
            "deadline": {"$lt": d},
            "reminder_count": {"$lt": TRAN_NHAC_NHO},
        }).to_list(300)
        # ưu tiên nhắc việc quá hạn lâu nhất, giống cách lãnh đạo rà việc tồn
        qua_han.sort(key=lambda x: x.get("deadline") or d)

        da_nhac = 0
        for t in qua_han:
            if da_nhac >= MOI_NGAY_NHAC:
                break
            if rng.random() >= XS["nhac_nho"]:
                continue
            nguoi_lam = t.get("assigned_to")
            if not nguoi_lam or nguoi_lam == sid:
                continue
            lan = t.get("reminder_count", 0) + 1
            luc = gio_ngau_nhien(d, rng)
            if that:
                await db.tasks.update_one({"_id": t["_id"]}, {"$inc": {"reminder_count": 1}})
                await gui_thong_bao(
                    nguoi_lam, "task_reminded", f"Nhắc nhở tiến độ (lần {lan}) ⏰",
                    f"Nhiệm vụ \"{t.get('code') or t.get('title')}\" chưa đảm bảo tiến độ. "
                    f"Đây là lần nhắc nhở thứ {lan}.", t["_id"], luc, rng)
                await ghi_nhat_ky(sid, sten, "task.reminded", "task", t["_id"],
                                  f"Lần thứ {lan}", luc)
            dem.cong("nhac_nho")
            da_nhac += 1

        # 2c. nhiệm vụ đột xuất phát sinh
        if rng.random() < XS["viec_dot_xuat"]:
            n = await giao_viec_dot_xuat(dept_id, ds, sep, d, rng, that)
            dem.cong("viec_moi", n)

    # ---------- 3. Ý kiến trao đổi ----------
    dang_mo = await db.tasks.find({"status": {"$in": ["in_progress", "review"]}}).to_list(400)
    rng.shuffle(dang_mo)
    for t in dang_mo[:MOI_NGAY_Y_KIEN]:
        if rng.random() >= XS["trao_doi"]:
            continue
        nguoi = rng.choice(users)
        luc = gio_ngau_nhien(d, rng)
        if that:
            await db.comments.insert_one({
                "task_id": str(t["_id"]),
                "user_id": str(nguoi["_id"]),
                "user_name": nguoi.get("name", ""),
                "content": rng.choice(Y_KIEN),
                "created_at": luc,
            })
        dem.cong("y_kien")

    # ---------- 4. Quy trình đánh giá đi tiếp ----------
    await day_ho_so(d, rng, dem, that)


async def giao_viec_dot_xuat(dept_id, ds, sep, d, rng, that) -> int:
    """Giao 1 nhiệm vụ đột xuất, lấy đầu việc từ Danh mục đã duyệt của đơn vị."""
    dm = await db.kpi_task_catalog.find_one({"department_id": dept_id, "status": "approved"})
    if not dm or not dm.get("items"):
        return 0
    can_bo = [u for u in ds if u.get("role") == "staff"]
    if not can_bo:
        return 0

    muc = rng.choice(dm["items"])
    nguoi = rng.choice(can_bo)
    sl = rng.randint(1, 2)
    prefix = f"NV-{d.year}-{d.month:02d}-"
    stt = await db.tasks.count_documents({"code": {"$regex": f"^{prefix}"}}) + 1

    doc = {
        "code": f"{prefix}{stt:04d}",
        "title": muc["task_name"],
        "description": muc.get("description"),
        "task_type": "dot_xuat",
        "classification": "thuong",
        "catalog_item_id": muc.get("id"),
        "complexity_group": muc.get("complexity_group"),
        "product": muc.get("category", "khac"),
        "kpi_point": muc.get("kpi_point", 0),
        "quantity_assigned": sl,
        "quantity_completed": 0,
        "assigned_to": str(nguoi["_id"]),
        "co_assignees": [],
        "assigned_by": str(sep["_id"]),
        "assigned_at": gio_ngau_nhien(d, rng),
        "assigned_basis": rng.choice(CAN_CU_GIAO),
        "department_id": dept_id,
        "support_department_ids": [],
        "status": "assigned",
        "deadline": (d + timedelta(days=rng.randint(4, 16))).replace(hour=17, minute=0,
                                                                    second=0, microsecond=0),
        "actual_end": None,
        "revision_count": 0,
        "reminder_count": 0,
        "period_month": d.month,
        "period_year": d.year,
        "attachments": [],
    }
    if that:
        kq = await db.tasks.insert_one(doc)
        luc = doc["assigned_at"]
        await gui_thong_bao(
            doc["assigned_to"], "task_assigned", "Bạn được giao nhiệm vụ công tác mới 📋",
            f"\"{doc['title']}\" đã được gán cho bạn bởi {sep.get('name','')}.",
            kq.inserted_id, luc, rng)
        await ghi_nhat_ky(sep["_id"], sep.get("name", ""), "task.created", "task",
                          kq.inserted_id, f"Title: {doc['title']}", luc)
    return 1


# ================= QUY TRÌNH ĐÁNH GIÁ =================

async def dung_bang_cham_diem(ho_so: dict, rng: random.Random) -> List[dict]:
    """
    Dựng bảng chấm điểm từng nhiệm vụ THẬT của cán bộ trong kỳ.

    Mức chất lượng suy từ số lần chỉnh sửa, mức tiến độ suy từ số lần nhắc nhở —
    đúng bảng mức của Hướng dẫn, nên điểm B và C tính ra có căn cứ.
    """
    viec = await db.tasks.find({
        "assigned_to": ho_so["target_id"],
        "period_month": ho_so.get("period_month"),
        "period_year": ho_so.get("period_year"),
    }).to_list(200)

    bang = []
    for t in viec:
        xong = t.get("status") == "done"
        muc_cl = _quality_tier_for(t.get("revision_count", 0))
        muc_td = _timeline_tier_for(t.get("reminder_count", 0))

        # Hoàn thành sớm hạn mà không phải sửa lần nào thì được ghi nhận vượt mức
        if xong and t.get("actual_end") and t.get("deadline") \
                and t["actual_end"] < t["deadline"] and t.get("revision_count", 0) == 0 \
                and rng.random() < 0.25:
            muc_td = "ahead"
            if rng.random() < 0.5:
                muc_cl = "excellent"

        bang.append({
            "task_id": str(t["_id"]),
            "catalog_item_id": t.get("catalog_item_id"),
            "task_name": t.get("code") or t.get("title"),
            "kpi_point": t.get("kpi_point", 0),
            "is_completed": xong,
            "quality_tier": muc_cl,
            "timeline_tier": muc_td,
            "note": None,
        })
    return bang


async def day_ho_so(d: datetime, rng: random.Random, dem: Dem, that: bool):
    """
    Đẩy một vài hồ sơ đánh giá đi tiếp một bước.

    Phân biệt kỳ đang mở và kỳ đã khép sổ, vì đây là chỗ dễ làm sai nhất:
      * Kỳ ĐANG MỞ (tháng hiện tại) chỉ đi tới bước thẩm định. Chốt điểm giữa
        tháng là sai nghiệp vụ — phần lớn nhiệm vụ chưa hoàn thành nên điểm A,
        B, C sẽ thấp giả tạo, cả đơn vị rơi Nhóm 3 một cách vô lý.
      * Kỳ ĐÃ KHÉP SỔ (tháng trước trở về trước) mới được xác định điểm KPI,
        lúc đó nhiệm vụ đã kết thúc nên điểm phản ánh đúng kết quả công tác.
    """
    da_day = 0

    # ---- 1. Kỳ đã khép sổ: chốt nốt các hồ sơ còn treo ----
    khep_so = {
        "period_type": "monthly",
        "overall_status": {"$in": ["self_evaluating", "reviewing"]},
        "$or": [
            {"period_year": {"$lt": d.year}},
            {"period_year": d.year, "period_month": {"$lt": d.month}},
        ],
    }
    while da_day < MOI_NGAY_TOI_DA_HO_SO:
        ho_so = await db.kpi_evaluations.find_one(khep_so)
        if not ho_so:
            break
        tu = ho_so["overall_status"]
        den = "reviewing" if tu == "self_evaluating" else "approved"
        if not await mot_buoc(ho_so, den, d, rng, dem, that):
            break
        da_day += 1

    # ---- 2. Kỳ đang mở: chỉ đi tới bước thẩm định ----
    loc = {"period_month": d.month, "period_year": d.year, "period_type": "monthly"}

    async def con_lai(trang_thai: str) -> int:
        return await db.kpi_evaluations.count_documents({**loc, "overall_status": trang_thai})

    for tu, den in (("self_evaluating", "reviewing"),
                    ("draft", "self_evaluating")):
        if da_day >= MOI_NGAY_TOI_DA_HO_SO:
            break
        # giữ độ phủ trạng thái cho bản demo
        if await con_lai(tu) <= GIU_LAI_MOI_TRANG_THAI:
            continue

        ho_so = await db.kpi_evaluations.find_one({**loc, "overall_status": tu})
        if not ho_so:
            continue
        if await mot_buoc(ho_so, den, d, rng, dem, that):
            da_day += 1


async def mot_buoc(ho_so: dict, den: str, d: datetime,
                   rng: random.Random, dem: Dem, that: bool) -> bool:
    """Đẩy một hồ sơ đi đúng một bước. Trả về False nếu không đi được."""
    luc = gio_ngau_nhien(d, rng)
    eid = ho_so["_id"]

    if den == "self_evaluating":
        bang = await dung_bang_cham_diem(ho_so, rng)
        if not bang:
            return False
        if that:
            await db.kpi_evaluations.update_one({"_id": eid}, {"$set": {
                "self_evaluation": {
                    "status": "submitted", "submitted_at": luc,
                    "task_scores": bang,
                    "proposed_rating": rng.choice(["group_1", "group_1", "group_2"]),
                },
                "overall_status": "self_evaluating", "updated_at": luc,
            }})
        dem.cong("tu_danh_gia")
        return True

    if den == "reviewing":
        bang = (ho_so.get("self_evaluation") or {}).get("task_scores") or []
        if not bang:
            return False
        nguoi_tham_dinh = await nguoi_co_tham_quyen(ho_so, ("leader", "director"))
        if that:
            await db.kpi_evaluations.update_one({"_id": eid}, {"$set": {
                "review": {
                    "status": "reviewed",
                    "reviewed_by": nguoi_tham_dinh,
                    "reviewed_at": luc,
                    "task_scores": bang,
                    "review_note": rng.choice([
                        "Nhất trí với kết quả tự đánh giá của đồng chí.",
                        "Đã đối chiếu Danh mục nhiệm vụ công tác, số liệu phù hợp.",
                        "Đề nghị tiếp tục phát huy, khắc phục hạn chế về tiến độ.",
                    ]),
                },
                "overall_status": "reviewing", "updated_at": luc,
            }})
        dem.cong("tham_dinh")
        return True

    # → approved
    nguoi_duyet = await nguoi_co_tham_quyen(ho_so, ("director",))
    if that:
        # gọi đúng hàm nghiệp vụ của máy chủ → số liệu khớp công thức
        await process_evaluation_approval(str(eid), nguoi_duyet or "")
        await db.kpi_evaluations.update_one({"_id": eid}, {"$set": {"updated_at": luc}})
        await cham_tieu_chi_chung(eid, rng, luc)
    dem.cong("xac_dinh_kpi")
    return True


async def nguoi_co_tham_quyen(ho_so: dict, vai: tuple) -> Optional[str]:
    u = await db.users.find_one({
        "department_id": ho_so.get("department_id"),
        "role": {"$in": list(vai)},
    })
    if u:
        return str(u["_id"])
    admin = await db.users.find_one({"role": "admin"})
    return str(admin["_id"]) if admin else None


async def cham_tieu_chi_chung(eid, rng: random.Random, luc: datetime):
    """Chấm 30 điểm tiêu chí chung ngay sau khi đã xác định điểm KPI."""
    ho_so = await db.kpi_evaluations.find_one({"_id": eid})
    if not ho_so:
        return
    kpi = (ho_so.get("approval") or {}).get("kpi_score", 0) or 0
    loai = criteria_type_for(ho_so.get("evaluation_type", "individual"), ho_so.get("target_role"))
    la = flatten_criteria(loai)

    truot = set()
    if kpi < 85:
        truot = set(rng.sample([x["id"] for x in la], k=rng.choice([1, 1, 2])))

    diem = []
    for x in la:
        ok = x["id"] not in truot
        diem.append({
            "criteria_id": x["id"], "criteria_name": x["name"],
            "max_score": x["max_score"],
            "rating": "dam_bao" if ok else "khong_dam_bao",
            "actual_score": x["max_score"] if ok else 0,
            "note": None if ok else "Cần khắc phục trong kỳ tiếp theo",
        })

    tong_e = sum(x["actual_score"] for x in diem)
    await db.kpi_evaluations.update_one({"_id": eid}, {"$set": {"general_criteria": {
        "criteria_type": loai, "scores": diem, "total_E": tong_e,
        "total_kpi_weighted": round(kpi * 0.7, 2),
        "total_final_score": round(tong_e + kpi * 0.7, 2),
        "scored_at": luc,
    }}})


# ================= SANG THÁNG MỚI =================

async def mo_ky_moi(d: datetime, rng: random.Random, dem: Dem, that: bool):
    """Sang tháng mới: giao nhiệm vụ của kỳ mới và mở hồ sơ đánh giá."""
    da_co = await db.tasks.count_documents({"period_month": d.month, "period_year": d.year})
    if da_co:
        return

    don_vi = await db.departments.find({}).to_list(None)
    for dv in don_vi:
        dept_id = str(dv["_id"])
        dm = await db.kpi_task_catalog.find_one({"department_id": dept_id, "status": "approved"})
        if not dm or not dm.get("items"):
            continue
        ds = await db.users.find({"department_id": dept_id, "role": {"$ne": "admin"}}).to_list(None)
        if not ds:
            continue
        chi_huy = [u for u in ds if u.get("role") in ("leader", "director")]
        giao_boi = str(rng.choice(chi_huy)["_id"]) if chi_huy else None

        for u in ds:
            for muc in rng.sample(dm["items"], k=min(len(dm["items"]), rng.randint(4, 7))):
                prefix = f"NV-{d.year}-{d.month:02d}-"
                stt = await db.tasks.count_documents({"code": {"$regex": f"^{prefix}"}}) + 1
                sl = rng.randint(1, 3)
                doc = {
                    "code": f"{prefix}{stt:04d}",
                    "title": muc["task_name"], "description": muc.get("description"),
                    "task_type": rng.choice(["thuong_xuyen", "thuong_xuyen", "chuyen_de"]),
                    "classification": "thuong",
                    "catalog_item_id": muc.get("id"),
                    "complexity_group": muc.get("complexity_group"),
                    "product": muc.get("category", "khac"),
                    "kpi_point": muc.get("kpi_point", 0),
                    "quantity_assigned": sl, "quantity_completed": 0,
                    "assigned_to": str(u["_id"]), "co_assignees": [],
                    "assigned_by": giao_boi,
                    "assigned_at": gio_ngau_nhien(d, rng),
                    "assigned_basis": rng.choice(CAN_CU_GIAO),
                    "department_id": dept_id, "support_department_ids": [],
                    "status": "assigned",
                    "deadline": (d + timedelta(days=rng.randint(5, 25))).replace(
                        hour=17, minute=0, second=0, microsecond=0),
                    "actual_end": None,
                    "revision_count": 0, "reminder_count": 0,
                    "period_month": d.month, "period_year": d.year,
                    "attachments": [],
                }
                if that:
                    await db.tasks.insert_one(doc)
                dem.cong("viec_ky_moi")

        # hồ sơ đánh giá kỳ mới: tập thể + từng cán bộ
        ho_so = [{
            "evaluation_type": "collective", "target_id": dept_id,
            "target_name": dv.get("name"), "target_role": None,
            "department_id": dept_id, "period_type": "monthly",
            "period_month": d.month, "period_year": d.year,
            "overall_status": "draft", "created_at": d, "updated_at": d,
        }]
        for u in ds:
            ho_so.append({
                "evaluation_type": "individual", "target_id": str(u["_id"]),
                "target_name": u.get("name"), "target_role": u.get("role"),
                "department_id": dept_id, "period_type": "monthly",
                "period_month": d.month, "period_year": d.year,
                "overall_status": "draft", "created_at": d, "updated_at": d,
            })
        if that:
            await db.kpi_evaluations.insert_many(ho_so)
        dem.cong("ky_moi", len(ho_so))


# ================= ĐIỀU KHIỂN =================

async def moc_da_mo_phong() -> Optional[datetime]:
    st = await db.demo_state.find_one({"_id": "mo_phong"})
    return st.get("last_date") if st else None


async def chay(so_ngay: Optional[int], that: bool):
    hom_nay = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rng = random.Random()
    dem = Dem()

    moc = await moc_da_mo_phong()
    if so_ngay is not None:
        bat_dau = hom_nay - timedelta(days=so_ngay)
    elif moc:
        bat_dau = moc
    else:
        # lần đầu: lấy mốc từ nhiệm vụ mới nhất đã giao
        t = await db.tasks.find({}).sort("assigned_at", -1).limit(1).to_list(1)
        goc = (t[0].get("assigned_at") if t else None) or (hom_nay - timedelta(days=3))
        bat_dau = goc.replace(hour=0, minute=0, second=0, microsecond=0)

    if bat_dau >= hom_nay:
        print("Dữ liệu đã cập nhật tới hôm nay, không cần mô phỏng thêm.")
        return

    print(f"Mô phỏng công tác từ {bat_dau:%d/%m/%Y} đến {hom_nay:%d/%m/%Y}"
          + ("" if that else "  [CHẾ ĐỘ THỬ — không ghi]"))

    d = bat_dau + timedelta(days=1)
    thang_truoc = bat_dau.month
    so_ngay_lam = 0
    while d <= hom_nay:
        if d.month != thang_truoc:
            await mo_ky_moi(d, rng, dem, that)
            thang_truoc = d.month
        if ngay_lam_viec(d):
            await mot_ngay(d, rng, dem, that)
            so_ngay_lam += 1
        d += timedelta(days=1)

    if that:
        await db.demo_state.update_one(
            {"_id": "mo_phong"},
            {"$set": {"last_date": hom_nay, "updated_at": datetime.utcnow()}},
            upsert=True,
        )

    print(f"\nĐã mô phỏng {so_ngay_lam} ngày làm việc (bỏ thứ Bảy, Chủ nhật):")
    dem.in_ra()

    con = await db.tasks.count_documents({})
    xong = await db.tasks.count_documents({"status": "done"})
    qh = await db.tasks.count_documents({"status": {"$ne": "done"}, "deadline": {"$lt": hom_nay}})
    print(f"\nHiện trạng: {con} nhiệm vụ · {xong} đã hoàn thành · {qh} đang quá hạn")


def main():
    ap = argparse.ArgumentParser(
        description="Mô phỏng cán bộ đi làm để dữ liệu mẫu không bị đứng yên.")
    ap.add_argument("--ngay", type=int, default=None,
                    help="Ép mô phỏng lùi lại bấy nhiêu ngày, bỏ qua mốc đã lưu")
    ap.add_argument("--thu", action="store_true",
                    help="Chỉ xem sẽ thay đổi những gì, không ghi vào cơ sở dữ liệu")
    a = ap.parse_args()
    asyncio.run(chay(a.ngay, that=not a.thu))


if __name__ == "__main__":
    main()
