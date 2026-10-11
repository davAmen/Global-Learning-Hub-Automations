"""Authentication API routes."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, EmailStr, Field

from src.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_current_user,
    get_current_user_optional,
    generate_verification_token,
    generate_password_reset_token,
)
from src.database import get_db
from src.config import get_settings
from src.utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


# Request/Response Models
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    email_verified: bool
    created_at: str


# Auth Routes
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, response: Response):
    """Register a new learner account."""
    db = get_db()
    settings = get_settings()
    
    # Check if email already exists
    existing = db.table("students").select("id").eq("email", request.email).limit(1).execute()
    if existing.data:
        raise HTTPException(409, "Email already registered")
    
    # Hash password
    password_hash = hash_password(request.password)
    verification_token = generate_verification_token()
    
    # Create student record
    student_data = {
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "password_hash": password_hash,
        "email_verified": False,
        "role": "learner",
        "verification_token": verification_token,
    }
    
    result = db.table("students").insert(student_data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create account")
    
    student = result.data[0]
    
    # Create tokens
    access_token = create_access_token({
        "sub": student["id"],
        "email": student["email"],
        "role": student["role"],
    })
    refresh_token = create_refresh_token({"sub": student["id"]})
    
    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    logger.info(f"New learner registered: {student['email']}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": student["id"],
            "name": student["name"],
            "email": student["email"],
            "phone": student.get("phone"),
            "role": student["role"],
            "email_verified": student["email_verified"],
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    """Login with email and password."""
    db = get_db()
    
    # Find student by email
    result = db.table("students").select("*").eq("email", request.email).limit(1).execute()
    if not result.data:
        raise HTTPException(401, "Invalid credentials")
    
    student = result.data[0]
    
    # Verify password
    if not student.get("password_hash") or not verify_password(request.password, student["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    
    # Check if account is locked
    if student.get("locked_until"):
        from datetime import datetime, timezone
        locked_until = datetime.fromisoformat(student["locked_until"].replace("Z", "+00:00"))
        if locked_until > datetime.now(timezone.utc):
            raise HTTPException(403, "Account temporarily locked")
    
    # Update last login and reset failed attempts
    db.table("students").update({
        "last_login_at": datetime.now(timezone.utc).isoformat(),
        "failed_login_attempts": 0,
        "locked_until": None,
    }).eq("id", student["id"]).execute()
    
    # Create tokens
    access_token = create_access_token({
        "sub": student["id"],
        "email": student["email"],
        "role": student["role"],
    })
    refresh_token = create_refresh_token({"sub": student["id"]})
    
    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    logger.info(f"Learner logged in: {student['email']}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": student["id"],
            "name": student["name"],
            "email": student["email"],
            "phone": student.get("phone"),
            "role": student["role"],
            "email_verified": student["email_verified"],
        }
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear cookies."""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, response: Response):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(request.refresh_token)
    except HTTPException:
        raise HTTPException(401, "Invalid or expired refresh token")
    
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")
    
    # Verify user still exists
    db = get_db()
    user_result = db.table("students").select("id, email, role").eq("id", payload["sub"]).limit(1).execute()
    if not user_result.data:
        raise HTTPException(401, "User not found")
    
    user = user_result.data[0]
    
    # Create new tokens
    access_token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
    })
    refresh_token = create_refresh_token({"sub": user["id"]})
    
    set_auth_cookies(response, access_token, refresh_token)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        }
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    db = get_db()
    result = db.table("students").select("id, name, email, phone, role, email_verified, created_at").eq("id", user["sub"]).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "User not found")
    
    student = result.data[0]
    return UserProfile(**student)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset."""
    db = get_db()
    result = db.table("students").select("id, email").eq("email", request.email).limit(1).execute()
    
    # Always return success to prevent email enumeration
    if not result.data:
        return {"message": "If the email exists, a reset link has been sent"}
    
    student = result.data[0]
    reset_token = generate_password_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token (could use a separate table or add to students)
    db.table("students").update({
        "password_reset_token": reset_token,
        "password_reset_expires": expires_at.isoformat(),
    }).eq("id", student["id"]).execute()
    
    # TODO: Send email with reset link
    # For now, log the token (in production, send via email)
    logger.info(f"Password reset token for {student['email']}: {reset_token}")
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token."""
    db = get_db()
    
    # Find user by reset token
    result = db.table("students").select("id, password_reset_token, password_reset_expires").eq("password_reset_token", request.token).limit(1).execute()
    if not result.data:
        raise HTTPException(400, "Invalid or expired reset token")
    
    student = result.data[0]
    
    # Check token expiry
    if student.get("password_reset_expires"):
        expires = datetime.fromisoformat(student["password_reset_expires"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            raise HTTPException(400, "Reset token has expired")
    
    # Update password
    new_hash = hash_password(request.new_password)
    db.table("students").update({
        "password_hash": new_hash,
        "password_reset_token": None,
        "password_reset_expires": None,
        "failed_login_attempts": 0,
        "locked_until": None,
    }).eq("id", student["id"]).execute()
    
    logger.info(f"Password reset for user: {student['id']}")
    return {"message": "Password reset successful"}


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verify email with token."""
    db = get_db()
    result = db.table("students").select("id, email_verified").eq("verification_token", request.token).limit(1).execute()
    if not result.data:
        raise HTTPException(400, "Invalid verification token")
    
    student = result.data[0]
    if student["email_verified"]:
        return {"message": "Email already verified"}
    
    db.table("students").update({
        "email_verified": True,
        "verification_token": None,
    }).eq("id", student["id"]).execute()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(user: dict = Depends(get_current_user)):
    """Resend email verification."""
    db = get_db()
    result = db.table("students").select("id, email, email_verified").eq("id", user["sub"]).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "User not found")
    
    student = result.data[0]
    if student["email_verified"]:
        return {"message": "Email already verified"}
    
    verification_token = generate_verification_token()
    db.table("students").update({
        "verification_token": verification_token,
    }).eq("id", student["id"]).execute()
    
    # TODO: Send verification email
    logger.info(f"Resent verification token to {student['email']}: {verification_token}")
    
    return {"message": "Verification email sent"}