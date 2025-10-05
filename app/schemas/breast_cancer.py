from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class BreastCancerAnalysisType(str, Enum):
    """Breast cancer analysis types"""
    BIRADS = "birads"
    PATHOLOGICAL = "pathological"
    BOTH = "both"


class BreastCancerDiagnosisRequest(BaseModel):
    """Schema for breast cancer diagnosis request"""
    analysis_type: Optional[BreastCancerAnalysisType] = Field(
        None, 
        description="Type of analysis to perform: birads, pathological, or both. If not specified, both analyses will be performed."
    )
    notes: Optional[str] = Field(None, description="Optional notes about the diagnosis")


class BiRadsResult(BaseModel):
    """Schema for BI-RADS analysis result"""
    predicted_class: str = Field(..., description="BI-RADS classification result")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    all_probabilities: Dict[str, float] = Field(..., description="Probabilities for all BI-RADS categories")


class PathologicalResult(BaseModel):
    """Schema for pathological analysis result"""
    predicted_class: str = Field(..., description="Pathological classification: benign, malignant, normal")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    all_probabilities: Dict[str, float] = Field(..., description="Probabilities for all pathological categories")


class BreastCancerDiagnosisResponse(BaseModel):
    """Schema for breast cancer diagnosis response"""
    id: int
    diagnosis_type: str = Field(..., description="Type of diagnosis performed")
    analysis_type: str = Field(..., description="Type of analysis performed: birads, pathological, or both")
    image_url: str = Field(..., description="URL to view the uploaded image")
    notes: Optional[str] = Field(None, description="Optional notes about the diagnosis")
    created_at: datetime
    
    # Main result (will be the most relevant result)
    predicted_class: str = Field(..., description="Primary classification result")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Primary confidence score")
    
    # Detailed results for each analysis type
    birads_result: Optional[BiRadsResult] = Field(None, description="BI-RADS analysis result if performed")
    pathological_result: Optional[PathologicalResult] = Field(None, description="Pathological analysis result if performed")
    
    class Config:
        from_attributes = True


class BreastCancerDiagnosisListResponse(BaseModel):
    """Schema for listing breast cancer diagnosis results"""
    results: List[BreastCancerDiagnosisResponse]
    total: int
    page: int
    size: int


class BreastCancerDiagnosisUpdate(BaseModel):
    """Schema for updating breast cancer diagnosis notes"""
    notes: Optional[str] = Field(None, description="Updated notes about the diagnosis")