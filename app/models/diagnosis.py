from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String, nullable=False)  # URL to stored image (Cloudinary)
    predicted_class = Column(String, nullable=False)  # Main classification result
    confidence_score = Column(Float, nullable=False)  # Main confidence score
    segmentation_path = Column(String, nullable=True)  # URL to segmentation result (Cloudinary)
    diagnosis_type = Column(String, nullable=False)  # brain_tumor, breast_cancer_birads, breast_cancer_pathological
    analysis_type = Column(String, nullable=True)  # birads, pathological, both (for breast cancer)
    additional_results = Column(JSON, nullable=True)  # For storing multiple analysis results when analysis_type='both'
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="diagnosis_results")


# Add this to the User model relationship (we'll need to update user.py)