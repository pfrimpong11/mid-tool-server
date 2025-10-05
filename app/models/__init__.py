# This makes the models directory a Python package
from .user import User
from .diagnosis import DiagnosisResult

__all__ = ["User", "DiagnosisResult"]