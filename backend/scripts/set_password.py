"""
Đặt mật khẩu mới cho một tài khoản, dùng khi triển khai thật.

VÌ SAO CẦN CÔNG CỤ NÀY
----------------------
Máy chủ từ chối đăng nhập bằng mật khẩu mặc định của dữ liệu mẫu khi không bật
ALLOW_DEMO_ACCOUNTS. Trên bản triển khai công khai, điều đó có nghĩa là KHÔNG
tài khoản nào vào được — vì mọi tài khoản mẫu đều dùng mật khẩu mặc định.

Chạy công cụ này để đặt mật khẩu mạnh cho một tài khoản quản trị, rồi đăng nhập
bình thường mà không phải mở cờ ALLOW_DEMO_ACCOUNTS.

CÁCH DÙNG
---------
    # Tự sinh mật khẩu mạnh và in ra
    python -m backend.scripts.set_password admin

    # Tự nhập mật khẩu (không hiện trên màn hình)
    python -m backend.scripts.set_password admin --hoi

Nhớ đặt MONGO_URI và DB_NAME trỏ đúng cơ sở dữ liệu cần sửa.
"""
import argparse
import asyncio
import getpass
import secrets
import string
import sys

from backend.config import describe
from backend.database import db
from backend.routers.auth import MAT_KHAU_MAU
from backend.security import get_password_hash

BANG_CHU = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
DO_DAI_TOI_THIEU = 12


def sinh_mat_khau(do_dai: int = 20) -> str:
    return "".join(secrets.choice(BANG_CHU) for _ in range(do_dai))


async def doi_mat_khau(username: str, mat_khau: str) -> bool:
    user = await db.users.find_one({"username": username})
    if not user:
        print(f"Không tìm thấy tài khoản {username!r}", file=sys.stderr)
        return False

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"hashed_password": get_password_hash(mat_khau)},
            # Vô hiệu hoá phiên cũ để thẻ gia hạn trước đó không dùng được nữa
            "$unset": {"active_refresh_token": ""},
        },
    )
    print(f"Đã đổi mật khẩu cho {username!r} ({user.get('name', '')})")
    return True


async def doi_mat_khau_tat_ca(mat_khau: str) -> int:
    """Đặt cùng một mật khẩu cho MỌI tài khoản. Chỉ dùng cho bản demo."""
    users = await db.users.find({}, {"username": 1}).to_list(5000)
    for u in users:
        await db.users.update_one(
            {"_id": u["_id"]},
            {
                "$set": {"hashed_password": get_password_hash(mat_khau)},
                "$unset": {"active_refresh_token": ""},
            },
        )
    print(f"Đã đặt lại mật khẩu cho {len(users)} tài khoản")
    return len(users)


async def main() -> int:
    p = argparse.ArgumentParser(description="Đặt mật khẩu mới cho một tài khoản")
    p.add_argument("username", nargs="?", help="Tên đăng nhập, ví dụ: admin")
    p.add_argument("--hoi", action="store_true", help="Tự nhập mật khẩu thay vì sinh ngẫu nhiên")
    p.add_argument(
        "--tat-ca", metavar="MAT_KHAU",
        help="Đặt CÙNG mật khẩu này cho mọi tài khoản. Chỉ dùng cho bản demo.",
    )
    args = p.parse_args()

    print(describe())

    if args.tat_ca:
        if args.tat_ca in MAT_KHAU_MAU:
            print(
                f"Mật khẩu {args.tat_ca!r} nằm trong danh sách mặc định bị chặn — "
                "đặt xong sẽ không đăng nhập được.",
                file=sys.stderr,
            )
            return 1
        so_luong = await doi_mat_khau_tat_ca(args.tat_ca)
        print(f"\n  Mọi tài khoản nay dùng mật khẩu: {args.tat_ca}")
        print(f"  Áp dụng cho {so_luong} tài khoản, kể cả quản trị hệ thống.")
        return 0

    if not args.username:
        p.error("cần nêu tên đăng nhập, hoặc dùng --tat-ca")

    if args.hoi:
        mat_khau = getpass.getpass("Mật khẩu mới: ")
        if mat_khau != getpass.getpass("Nhập lại: "):
            print("Hai lần nhập không khớp", file=sys.stderr)
            return 1
        if len(mat_khau) < DO_DAI_TOI_THIEU:
            print(f"Mật khẩu phải từ {DO_DAI_TOI_THIEU} ký tự", file=sys.stderr)
            return 1
        if mat_khau in MAT_KHAU_MAU:
            print("Mật khẩu này nằm trong danh sách mặc định bị chặn", file=sys.stderr)
            return 1
    else:
        mat_khau = sinh_mat_khau()

    if not await doi_mat_khau(args.username, mat_khau):
        return 1

    if not args.hoi:
        print()
        print("  Mật khẩu mới:", mat_khau)
        print()
        print("  Lưu lại ngay — mật khẩu không hiển thị lại lần nào nữa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
