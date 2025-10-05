from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DiagnosisRequest(BaseModel):
    """Schema for diagnosis request"""
    notes: Optional[str] = Field(None, description="Optional notes about the diagnosis")


class DiagnosisResponse(BaseModel):
    """Schema for diagnosis response"""
    id: int
    predicted_class: str = Field(..., description="Predicted tumor class: glioma, meningioma, notumor, pituitary")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    diagnosis_type: str = Field(default="brain_tumor", description="Type of diagnosis performed")
    image_url: str = Field(..., description="URL to view the uploaded image")
    segmentation_url: Optional[str] = Field(None, description="URL to view the segmentation result")
    notes: Optional[str] = Field(None, description="Optional notes about the diagnosis")
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiagnosisListResponse(BaseModel):
    """Schema for listing diagnosis results"""
    results: list[DiagnosisResponse]
    total: int
    page: int
    size: int


class DiagnosisUpdate(BaseModel):
    """Schema for updating diagnosis notes"""
    notes: Optional[str] = Field(None, description="Updated notes about the diagnosis")