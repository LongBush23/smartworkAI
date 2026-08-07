from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.config import ALLOW_DEMO_ACCOUNTS
from backend.database import db
from backend.security import verify_password, create_access_token, get_current_user, get_password_hash
from backend.models.schemas import UserCreate, UserResponse, PasswordChange, ProfileUpdate
from backend.services.audit_service import log_action
from pydantic import BaseModel

router = APIRouter()

def fix_id(doc):
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.post("/register")
async def register(user: UserCreate):
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Thư điện tử đã được sử dụng")
    
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "hashed_password": hashed_password,
        "name": user.name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "department_id": user.department_id,
        "position": user.position,
        "rank": user.rank,
        "bio": user.bio,
        "is_admin": user.role == "admin",
        # Lãnh đạo, chỉ huy → KPI tính theo 04 tiêu chí (có thêm điểm D)
        "is_commander": user.role in ("director", "leader"),
    }
    await db.users.insert_one(new_user)
    return {"message": "User created successfully"}

# Mật khẩu mặc định của dữ liệu mẫu. Xem backend/config.py để biết vì sao
# các mật khẩu này bị chặn khi không bật cờ ALLOW_DEMO_ACCOUNTS.
MAT_KHAU_MAU = {"admin123", "123456", "password", "12345678"}


@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Chặn mật khẩu mặc định của dữ liệu mẫu trên môi trường thật.
    # Kiểm tra SAU khi đã xác thực đúng, để không tiết lộ tài khoản nào tồn tại.
    if form_data.password in MAT_KHAU_MAU and not ALLOW_DEMO_ACCOUNTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Tài khoản đang dùng mật khẩu mặc định của dữ liệu mẫu nên bị từ chối "
                "trên môi trường này. Quản trị hệ thống cần đổi mật khẩu, hoặc bật biến "
                "môi trường ALLOW_DEMO_ACCOUNTS nếu đây là bản chạy thử có kiểm soát."
            ),
        )
    from datetime import timedelta
    from backend.security import ACCESS_TOKEN_EXPIRE_MINUTES
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    from backend.security import create_refresh_token
    refresh_token = create_refresh_token(data={"sub": user["username"]})

    # Store refresh token in DB for logout/blacklist
    from bson import ObjectId
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"active_refresh_token": refresh_token}}
    )

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_access_token(data: RefreshTokenRequest):
    from jose import JWTError, jwt
    from backend.security import SECRET_KEY, ALGORITHM
    from backend.security import create_access_token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if token is still active (not logged out)
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    stored_token = user.get("active_refresh_token")
    if stored_token and stored_token != data.refresh_token:
        raise credentials_exception  # Token was invalidated by logout
        
    new_access_token = create_access_token(data={"sub": username})
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Invalidate refresh token on the server side."""
    from bson import ObjectId
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$unset": {"active_refresh_token": ""}}
    )
    await log_action(current_user["_id"], current_user.get("name", ""), "user.logout", "user", current_user["_id"])
    return {"message": "Đăng xuất thành công"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return fix_id(current_user)

@router.post("/change-password")
async def change_password(data: PasswordChange, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"username": current_user["username"]})
    if not user or not verify_password(data.old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không chính xác")
        
    new_hashed = get_password_hash(data.new_password)
    from bson import ObjectId
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {"hashed_password": new_hashed}}
    )
    await log_action(current_user["_id"], current_user.get("name", ""), "user.change_password", "user", current_user["_id"])
    return {"message": "Đổi mật khẩu thành công"}

@router.put("/profile")
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    update_data = {"name": data.name, "email": data.email}
    for field in ("position", "rank", "bio", "avatar"):
        value = getattr(data, field, None)
        if value is not None:
            update_data[field] = value


    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": update_data}
    )
    await log_action(current_user["_id"], current_user.get("name", ""), "user.update_profile", "user", current_user["_id"])
    return {"message": "Cập nhật thông tin cá nhân thành công"}
