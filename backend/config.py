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
