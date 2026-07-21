from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
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
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "hashed_password": hashed_password,
        "name": user.name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "department_id": user.department_id,
        "skills": [s.model_dump() for s in user.skills] if user.skills else [],
        "preferences": user.preferences.model_dump() if user.preferences else {},
        "bio": user.bio,
        "ai_metrics": {
            "historical_quality_score": 50.0,
            "on_time_rate": 1.0,
            "capacity_hours_per_week": 40,
            "current_workload_hours": 0,
        },
        "availability": 100.0,
        "current_workload": 0,
        "quality_score": 50.0,
        "is_admin": user.role == "admin"
    }
    await db.users.insert_one(new_user)
    return {"message": "User created successfully"}

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
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
        detail="Could not validate credentials",
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
    update_data = {
        "name": data.name,
        "email": data.email,
        "skills": [s.model_dump() for s in data.skills]
    }
    if data.preferences is not None:
        update_data["preferences"] = data.preferences.model_dump()
    if data.bio is not None:
        update_data["bio"] = data.bio
    if hasattr(data, 'avatar') and data.avatar is not None:
        update_data["avatar"] = data.avatar
        
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": update_data}
    )
    await log_action(current_user["_id"], current_user.get("name", ""), "user.update_profile", "user", current_user["_id"])
    return {"message": "Cập nhật thông tin cá nhân thành công"}
