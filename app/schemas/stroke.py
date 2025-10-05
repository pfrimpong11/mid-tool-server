from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class StrokeDiagnosisRequest(BaseModel):
    """Schema for stroke diagnosis request"""
    notes: Optional[str] = Field(None, description="Optional notes about the diagnosis")


class StrokeDiagnosisResponse(BaseModel):
    """Schema for stroke diagnosis response"""
    id: int
    predicted_class: str = Field(
        ..., 
        description="Predicted stroke class: hemorrhagic_stroke, ischemic_stroke, or no_stroke"
    )
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score between 0 and 1"
    )
    all_probabilities: Dict[str, float] = Field(
        ..., 
        description="Probabilities for all stroke classes"
    )
    diagnosis_type: str = Field(
        default="stroke", 
        description="Type of diagnosis performed"
    )
    image_url: str = Field(..., description="URL to view the uploaded MRI image")
    notes: Optional[str] = Field(None, description="Optional notes about the diagnosis")
    created_at: datetime
    
    class Config:
        from_attributes = True


class StrokeDiagnosisListResponse(BaseModel):
    """Schema for listing stroke diagnosis results"""
    results: List[StrokeDiagnosisResponse]
    total: int
    page: int
    size: int


class StrokeDiagnosisUpdate(BaseModel):
    """Schema for updating stroke diagnosis notes"""
    notes: Optional[str] = Field(None, description="Updated notes about the diagnosis")
