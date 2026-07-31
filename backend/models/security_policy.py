"""
Chính sách tiếp cận nhiệm vụ có độ mật.

════════════════════════════════════════════════════════════════════════════
GIỚI HẠN CỦA HỆ THỐNG — ĐỌC KỸ TRƯỚC KHI TRIỂN KHAI
════════════════════════════════════════════════════════════════════════════

Hệ thống này KHÔNG phải hệ thống xử lý bí mật nhà nước và KHÔNG được dùng để
lưu trữ nội dung thuộc danh mục bí mật nhà nước.

Lý do:
  - Cơ sở dữ liệu đặt trên hạ tầng điện toán đám mây dùng chung.
  - Không sử dụng sản phẩm mật mã của Ban Cơ yếu Chính phủ.
  - Không chạy trên mạng máy tính nội bộ tách biệt.

Theo Luật Bảo vệ bí mật nhà nước 2018, tài liệu, vật chứa bí mật nhà nước phải
được quản lý, lưu giữ theo chế độ riêng. Vì vậy, với nhiệm vụ có độ mật, hệ
thống chỉ lưu phần THÔNG TIN QUẢN LÝ phục vụ tính điểm KPI:

    mã hiệu · tên gọi quy ước · độ mật · điểm được giao · thời hạn
    · số lần chỉnh sửa · số lần nhắc nhở · số hiệu hồ sơ gốc · nơi lưu

Toàn bộ nội dung nghiệp vụ nằm ở hồ sơ gốc, ngoài hệ thống. Điều này KHÔNG làm
mất tính năng nào: công thức tính điểm A, B, C, D theo Hướng dẫn 20-HD/ĐUCA
không sử dụng đến nội dung nhiệm vụ.

Cơ chế bảo vệ ở đây là PHÂN QUYỀN TIẾP CẬN + GHI NHẬT KÝ, được thực thi ở tầng
máy chủ (trường nhạy cảm không được đưa vào phản hồi API), không phải che bằng
giao diện. Đây là biện pháp quản lý nội bộ, không thay thế được yêu cầu pháp lý
về bảo vệ bí mật nhà nước.
════════════════════════════════════════════════════════════════════════════
"""
from typing import Any, Dict, Optional

from backend.models.schemas import ClassificationEnum

# Thứ bậc độ mật. Cán bộ chỉ tiếp cận được nhiệm vụ có độ mật ≤ cấp độ của mình.
CLASSIFICATION_RANK: Dict[str, int] = {
    ClassificationEnum.THUONG.value: 0,
    ClassificationEnum.MAT.value: 1,
    ClassificationEnum.TOI_MAT.value: 2,
    ClassificationEnum.TUYET_MAT.value: 3,
}

CLASSIFICATION_LABELS: Dict[str, str] = {
    ClassificationEnum.THUONG.value: "Thường",
    ClassificationEnum.MAT.value: "Mật",
    ClassificationEnum.TOI_MAT.value: "Tối mật",
    ClassificationEnum.TUYET_MAT.value: "Tuyệt mật",
}

# Những trường chỉ người đủ cấp độ tiếp cận mới được nhận trong phản hồi API.
# Máy chủ LOẠI BỎ hẳn các trường này, không gửi về trình duyệt.
RESTRICTED_FIELDS = ("description", "file_reference", "file_location", "attachments")


def clearance_of(user: dict) -> int:
    """Cấp độ tiếp cận của cán bộ. Mặc định 0 (chỉ tài liệu thường)."""
    return int(user.get("clearance_level", 0) or 0)


def rank_of(classification: Optional[str]) -> int:
    return CLASSIFICATION_RANK.get(classification or ClassificationEnum.THUONG.value, 0)


def can_access(user: dict, task: dict) -> bool:
    """
    Cán bộ tiếp cận được nhiệm vụ khi:
      - nhiệm vụ không có độ mật, HOẶC
      - cấp độ tiếp cận của cán bộ ≥ độ mật của nhiệm vụ, HOẶC
      - cán bộ là người trực tiếp thực hiện / phối hợp thực hiện nhiệm vụ đó.
    """
    task_rank = rank_of(task.get("classification"))
    if task_rank == 0:
        return True
    if clearance_of(user) >= task_rank:
        return True

    uid = str(user.get("_id", ""))
    if task.get("assigned_to") == uid:
        return True
    return uid in (task.get("co_assignees") or [])


def redact(task: dict, user: dict) -> dict:
    """
    Trả về bản sao nhiệm vụ đã loại bỏ trường nhạy cảm nếu cán bộ không đủ
    cấp độ tiếp cận. Mã hiệu, độ mật, điểm và thời hạn vẫn giữ để bảo đảm
    tính minh bạch của việc chấm điểm KPI.
    """
    if can_access(user, task):
        task["is_redacted"] = False
        return task

    for field in RESTRICTED_FIELDS:
        task.pop(field, None)

    # Thay tên gọi bằng mã hiệu để không lộ thông tin qua tiêu đề
    task["title"] = task.get("code") or "Nhiệm vụ có độ mật"
    task["is_redacted"] = True
    return task


def assert_no_classified_content(payload: Dict[str, Any]) -> None:
    """
    Chặn việc ghi nội dung tự do vào nhiệm vụ có độ mật.

    Gọi khi tạo/sửa nhiệm vụ. Nếu độ mật khác "thường" mà vẫn có mô tả hoặc
    tệp đính kèm thì từ chối — nội dung phải nằm ở hồ sơ gốc.
    """
    from fastapi import HTTPException

    classification = payload.get("classification")
    if rank_of(classification) == 0:
        return

    if payload.get("description"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Nhiệm vụ có độ mật không được lưu nội dung diễn giải trong hệ thống. "
                "Vui lòng ghi số hiệu hồ sơ gốc vào trường 'Hồ sơ gốc'."
            ),
        )
    if payload.get("attachments"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Không đính kèm tệp vào nhiệm vụ có độ mật. "
                "Tài liệu mật phải được quản lý theo chế độ riêng tại đơn vị."
            ),
        )
