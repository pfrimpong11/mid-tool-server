# This makes the schemas directory a Python package
from .user import UserCreate, User, UserUpdate, Token, UserLogin
from .diagnosis import DiagnosisRequest, DiagnosisResponse, DiagnosisListResponse, DiagnosisUpdate

__all__ = [
    "UserCreate", "User", "UserUpdate", "Token", "UserLogin",
    "DiagnosisRequest", "DiagnosisResponse", "DiagnosisListResponse", "DiagnosisUpdate"
]