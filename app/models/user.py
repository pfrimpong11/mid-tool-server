from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)  # New field
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Consent fields
    gdpr_consent = Column(Boolean, default=False, nullable=False)
    gdpr_consent_date = Column(DateTime(timezone=True), nullable=True)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    marketing_consent_date = Column(DateTime(timezone=True), nullable=True)
    
    # Profile settings
    role = Column(String(50), nullable=True)
    institution = Column(String(100), nullable=True)
    
    # Preferences
    dark_mode = Column(Boolean, default=False)
    interface_scale = Column(String(20), default='normal')
    default_analysis_model = Column(String(20), default='advanced')
    
    # Notification settings
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    analysis_notifications = Column(Boolean, default=True)
    report_notifications = Column(Boolean, default=True)
    
    # Privacy settings
    data_retention_period = Column(String(20), default='1year')
    anonymous_analytics = Column(Boolean, default=True)
    data_sharing = Column(Boolean, default=False)
    
    # Soft delete fields
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Password reset fields
    reset_token = Column(String(255), nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    diagnosis_results = relationship("DiagnosisResult", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"