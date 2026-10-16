from sqlalchemy import JSON, ForeignKey, Integer, Float, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class FarmProfile(Base):
    __tablename__ = "farm_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    farmer_name: Mapped[str|None] = mapped_column(String(120))
    age: Mapped[int|None] = mapped_column(Integer)
    gender: Mapped[str|None] = mapped_column(String(30))
    farmer_type: Mapped[str|None] = mapped_column(String(40))
    social_category: Mapped[str|None] = mapped_column(String(30))
    state: Mapped[str|None] = mapped_column(String(80))
    district: Mapped[str|None] = mapped_column(String(80))
    block: Mapped[str|None] = mapped_column(String(80))
    village: Mapped[str|None] = mapped_column(String(120))
    land_size_hectares: Mapped[float|None] = mapped_column(Float)
    land_ownership_type: Mapped[str|None] = mapped_column(String(50))
    cultivable_land_hectares: Mapped[float|None] = mapped_column(Float)
    crop_types: Mapped[list] = mapped_column(JSON, default=list)
    primary_crop: Mapped[str|None] = mapped_column(String(80))
    irrigation_type: Mapped[str|None] = mapped_column(String(50))
    soil_type: Mapped[str|None] = mapped_column(String(50))
    income_category: Mapped[str|None] = mapped_column(String(50))
    bank_account_status: Mapped[str|None] = mapped_column(String(40))
    kcc_holder: Mapped[bool|None] = mapped_column(Boolean)
    years_of_cultivation: Mapped[int|None] = mapped_column(Integer)
    farming_type: Mapped[str|None] = mapped_column(String(50))
    livestock_owned: Mapped[bool|None] = mapped_column(Boolean)
    equipment_owned: Mapped[list] = mapped_column(JSON, default=list)
    extra_attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    user = relationship("User", back_populates="profile")
