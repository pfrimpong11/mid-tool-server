"""
Schemas for statistics endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DashboardStats(BaseModel):
    """Main dashboard statistics"""
    total_diagnoses: int = Field(..., description="Total number of diagnoses")
    brain_tumor_diagnoses: int = Field(..., description="Number of brain tumor diagnoses")
    breast_cancer_diagnoses: int = Field(..., description="Number of breast cancer diagnoses")
    stroke_diagnoses: int = Field(0, description="Number of stroke diagnoses")
    critical_findings: int = Field(..., description="Number of critical findings")
    normal_findings: int = Field(..., description="Number of normal findings")
    warning_findings: int = Field(..., description="Number of warning findings")
    accuracy_rate: float = Field(..., description="Overall AI accuracy rate")
    
    class Config:
        from_attributes = True


class TumorTypeDistribution(BaseModel):
    """Tumor type distribution statistics"""
    name: str = Field(..., description="Tumor type name")
    count: int = Field(..., description="Number of cases")
    percentage: float = Field(..., description="Percentage of total cases")
    
    class Config:
        from_attributes = True


class WeeklyAnalytics(BaseModel):
    """Weekly analytics data"""
    day: str = Field(..., description="Day of the week")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    analyses: int = Field(..., description="Number of analyses performed")
    accuracy: float = Field(..., description="Accuracy percentage for that day")
    
    class Config:
        from_attributes = True


class MonthlyTrends(BaseModel):
    """Monthly trends data"""
    month: str = Field(..., description="Month name")
    year: int = Field(..., description="Year")
    total_diagnoses: int = Field(..., description="Total diagnoses in the month")
    critical_findings: int = Field(..., description="Critical findings in the month")
    normal_findings: int = Field(..., description="Normal findings in the month")
    average_confidence: float = Field(..., description="Average confidence score")
    
    class Config:
        from_attributes = True


class RecentActivity(BaseModel):
    """Recent activity item"""
    id: int
    diagnosis_type: str
    predicted_class: str
    confidence_score: float
    image_url: Optional[str] = Field(None, description="URL to the diagnosis image")
    segmentation_url: Optional[str] = Field(None, description="URL to the segmentation image")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime
    severity: str = Field(..., description="Severity level: normal, warning, critical")
    
    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    """Complete statistics response"""
    dashboard_stats: DashboardStats
    tumor_distribution: List[TumorTypeDistribution]
    weekly_analytics: List[WeeklyAnalytics]
    monthly_trends: List[MonthlyTrends]
    recent_activity: List[RecentActivity]
    
    class Config:
        from_attributes = True


class UserStatsSummary(BaseModel):
    """User-specific statistics summary"""
    user_id: int
    total_uploads: int
    first_diagnosis_date: Optional[datetime]
    last_diagnosis_date: Optional[datetime]
    most_common_diagnosis: Optional[str]
    average_confidence: float
    total_brain_tumor_scans: int
    total_breast_cancer_scans: int
    total_stroke_scans: int = 0
    
    class Config:
        from_attributes = True