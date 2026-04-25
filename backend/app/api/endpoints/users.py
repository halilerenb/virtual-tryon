from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.models.database import get_db, User, UserMeasurement, Gender
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


# ── Pydantic şemaları ─────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserMeasurementInput(BaseModel):
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    gender: Optional[str] = "unisex"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ── Endpoint'ler ──────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı"""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı"
        )

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı"
        )

    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Giriş yapan kullanıcının bilgileri"""
    return current_user


@router.post("/measurements")
def save_measurements(
    data: UserMeasurementInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcı beden ölçülerini kaydet"""
    measurements = db.query(UserMeasurement).filter(
        UserMeasurement.user_id == current_user.id
    ).first()

    if measurements:
        for key, value in data.dict(exclude_unset=True).items():
            setattr(measurements, key, value)
    else:
        measurements = UserMeasurement(
            user_id=current_user.id,
            **data.dict(exclude_unset=True)
        )
        db.add(measurements)

    db.commit()
    db.refresh(measurements)

    return {
        "success": True,
        "message": "Ölçüler kaydedildi",
        "measurements": {
            "height_cm": measurements.height_cm,
            "weight_kg": measurements.weight_kg,
            "chest_cm": measurements.chest_cm,
            "waist_cm": measurements.waist_cm,
            "hip_cm": measurements.hip_cm,
            "gender": measurements.gender
        }
    }


@router.get("/measurements")
def get_measurements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcı beden ölçülerini getir"""
    measurements = db.query(UserMeasurement).filter(
        UserMeasurement.user_id == current_user.id
    ).first()

    if not measurements:
        return {"success": False, "message": "Ölçü bilgisi bulunamadı"}

    return {
        "success": True,
        "measurements": {
            "height_cm": measurements.height_cm,
            "weight_kg": measurements.weight_kg,
            "chest_cm": measurements.chest_cm,
            "waist_cm": measurements.waist_cm,
            "hip_cm": measurements.hip_cm,
            "gender": measurements.gender
        }
    }