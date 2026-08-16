"""
Nạp cấu hình từ biến môi trường, có hỗ trợ file backend/.env.

Import module này TRƯỚC khi đọc os.getenv ở bất kỳ đâu trong backend.
Biến môi trường thật (do hệ thống hoặc nền tảng triển khai đặt) luôn được
ưu tiên hơn giá trị trong file .env.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/.env — nằm cạnh file này
_ENV_PATH = Path(__file__).resolve().parent / ".env"

# override=False: không ghi đè biến môi trường đã có sẵn
load_dotenv(dotenv_path=_ENV_PATH, override=False)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "smartwork")
SECRET_KEY = os.getenv("SECRET_KEY", "smartwork_super_secret_key")

# Trợ lý hội thoại. Đây là chỗ DUY NHẤT hệ thống gọi ra dịch vụ bên ngoài —
# xem rào chắn ở backend/services/tro_ly/__init__.py.
# Bỏ trống khoá thì trợ lý tự lui về máy tra cứu tại chỗ, không hỏng gì.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
# Chọn model theo hai bài học đã trả giá:
#   1. KHÔNG ghim phiên bản cố định. `gemini-2.5-flash` từng chạy tốt, nay trả
#      404 "no longer available to new users". Bí danh `-latest` tự theo bản mới.
#   2. Bản `flash-lite` có hạn mức miễn phí rộng hơn hẳn. `gemini-3.7-flash` chỉ
#      cho 20 lượt/ngày (GenerateRequestsPerDayPerProjectPerModel-FreeTier) —
#      mỗi câu hỏi có gọi công cụ tốn 2-3 lượt nên chỉ đủ ~7 câu rồi tắt.
# Đổi bằng biến GEMINI_MODEL nếu nâng gói trả phí.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on", "co", "có")


# Cho phép đăng nhập bằng các mật khẩu mặc định của dữ liệu mẫu
# (admin123, 123456...). MẶC ĐỊNH TẮT.
#
# Dữ liệu mẫu tạo 64 tài khoản dùng mật khẩu chung, trong đó có tài khoản quản
# trị. Nếu bản triển khai công khai vẫn nhận các mật khẩu này thì bất kỳ ai tìm
# ra địa chỉ đều vào được với quyền cao nhất. Chỉ bật cờ này khi chạy demo trong
# môi trường có kiểm soát.
ALLOW_DEMO_ACCOUNTS = _flag("ALLOW_DEMO_ACCOUNTS", default=False)


# --------------------------------------------------------------------------
# CORS — nguồn được phép gọi API
# --------------------------------------------------------------------------
# Máy cục bộ, luôn được phép để chạy `npm run dev` không phải cấu hình gì thêm.
NGUON_CUC_BO = ["http://localhost:5173", "http://localhost:5199", "http://127.0.0.1:5173"]

# Bản triển khai giao diện của dự án này trên Vercel. Mỗi lần đẩy mã, Vercel
# sinh thêm một tên miền xem trước dạng smartwork-ai-git-<nhánh>-<tài khoản>,
# nên phải khớp bằng biểu thức chính quy thay vì liệt kê từng cái.
#
# Vì sao mở sẵn mà vẫn an toàn: hệ thống xác thực bằng thẻ Bearer lưu trong
# localStorage, KHÔNG dùng cookie phiên, và allow_credentials=False. Một trang
# web lạ không đọc được localStorage của tên miền khác, nên dù được phép gọi
# API nó vẫn không có thẻ để gọi endpoint cần đăng nhập.
NGUON_TRIEN_KHAI_REGEX = r"^https://smartwork-ai[a-z0-9-]*\.vercel\.app$"


def _danh_sach(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    return [x.strip() for x in raw.split(",") if x.strip()]


def nguon_cors() -> tuple[list[str], str]:
    """
    Trả về (danh sách nguồn, biểu thức chính quy) cho CORSMiddleware.

    CORS_ORIGINS **bổ sung** vào danh sách mặc định chứ không thay thế, để đặt
    tên miền thật không vô tình làm hỏng môi trường phát triển cục bộ.
    CORS_ORIGIN_REGEX ghi đè biểu thức mặc định nếu được đặt.
    """
    nguon = list(NGUON_CUC_BO)
    for o in _danh_sach("CORS_ORIGINS"):
        if o not in nguon:
            nguon.append(o)
    regex = os.getenv("CORS_ORIGIN_REGEX", "").strip() or NGUON_TRIEN_KHAI_REGEX
    return nguon, regex


def describe() -> str:
    """Mô tả cấu hình đang dùng, che kín thông tin bí mật."""
    if not MONGO_URI:
        source = "CHƯA ĐẶT — sẽ kết nối mongodb://localhost:27017"
    elif "@" in MONGO_URI:
        # mongodb+srv://user:pass@cluster.../  → chỉ hiện phần host
        source = MONGO_URI.split("@", 1)[1].split("/", 1)[0]
    else:
        source = MONGO_URI
    return f"MONGO_URI host={source} · DB_NAME={DB_NAME} · .env={'có' if _ENV_PATH.exists() else 'không'}"
