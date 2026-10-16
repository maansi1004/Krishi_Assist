from pydantic import BaseModel, Field
from typing import Any


class FarmerProfile(BaseModel):
    farmer_name: str | None = None
    age: int | None = None
    gender: str | None = None
    farmer_type: str | None = None
    social_category: str | None = None
    state: str | None = None
    district: str | None = None
    block: str | None = None
    village: str | None = None
    land_size_hectares: float | None = None
    land_ownership_type: str | None = None
    cultivable_land_hectares: float | None = None
    crop_types: list[str] = Field(default_factory=list)
    primary_crop: str | None = None
    irrigation_type: str | None = None
    soil_type: str | None = None
    income_category: str | None = None
    bank_account_status: str | None = None
    kcc_holder: bool | None = None
    years_of_cultivation: int | None = None
    farming_type: str | None = None
    livestock_owned: bool | None = None
    equipment_owned: list[str] = Field(default_factory=list)
    extra_attributes: dict[str, Any] = Field(default_factory=dict)
