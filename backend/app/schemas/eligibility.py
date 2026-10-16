from pydantic import BaseModel, Field
from .profile import FarmerProfile

class EligibilityRequest(BaseModel):
    scheme_code: str
    profile: FarmerProfile

class DiscoveryRequest(BaseModel):
    profile: FarmerProfile = Field(default_factory=FarmerProfile)
    need: str
    category: str | None = None
