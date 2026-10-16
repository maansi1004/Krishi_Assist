from app.schemas.profile import FarmerProfile
class ProfileResponse(FarmerProfile):
    user_id: int
