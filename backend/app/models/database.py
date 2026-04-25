from sqlalchemy import (
    create_engine, Column, Integer, String, Float, 
    DateTime, Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://vtryon:vtryon123@localhost:5432/vtryon_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Enum tanımları ────────────────────────────────────────────────────────────
class GarmentCategory(str, enum.Enum):
    upper = "upper"        # Üst giyim
    lower = "lower"        # Alt giyim
    outer = "outer"        # Dış giyim
    dress = "dress"        # Elbise/tulum
    unknown = "unknown"    # Belirlenemedi

class JobStatus(str, enum.Enum):
    pending = "pending"        # Bekliyor
    processing = "processing"  # İşleniyor
    completed = "completed"    # Tamamlandı
    failed = "failed"          # Başarısız

class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    unisex = "unisex"


# ── Tablolar ──────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    measurements = relationship("UserMeasurement", back_populates="user", uselist=False)
    photos = relationship("UserPhoto", back_populates="user")
    tryon_jobs = relationship("TryonJob", back_populates="user")


class UserMeasurement(Base):
    __tablename__ = "user_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    chest_cm = Column(Float)
    waist_cm = Column(Float)
    hip_cm = Column(Float)
    gender = Column(Enum(Gender), default=Gender.unisex)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="measurements")


class UserPhoto(Base):
    __tablename__ = "user_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="photos")


class TryonJob(Base):
    __tablename__ = "tryon_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_url = Column(String(1000))
    garment_image_url = Column(String(500))
    result_image_url = Column(String(500))
    garment_category = Column(Enum(GarmentCategory), default=GarmentCategory.unknown)
    category_auto_detected = Column(Boolean, default=False)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    error_message = Column(Text)
    recommended_size = Column(String(10))
    confidence_percent = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    user = relationship("User", back_populates="tryon_jobs")


# ── Tabloları oluştur ─────────────────────────────────────────────────────────
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tablolar oluşturuldu.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()