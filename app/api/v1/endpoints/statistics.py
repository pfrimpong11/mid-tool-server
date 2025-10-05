"""
Statistics endpoints for dashboard analytics and user statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.statistics import (
    DashboardStats,
    TumorTypeDistribution,
    WeeklyAnalytics,
    MonthlyTrends,
    RecentActivity,
    StatisticsResponse,
    UserStatsSummary
)
from app.services.statistics_service import statistics_service

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get main dashboard statistics for the current user.
    
    Returns:
    - Total diagnoses count
    - Brain tumor and breast cancer counts
    - Critical, normal, and warning findings
    - Overall AI accuracy rate
    """
    try:
        stats = statistics_service.get_dashboard_stats(db, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard statistics: {str(e)}"
        )


@router.get("/tumor-distribution", response_model=List[TumorTypeDistribution])
async def get_tumor_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tumor type distribution for brain tumor diagnoses.
    
    Returns distribution of detected tumor types with counts and percentages.
    """
    try:
        distribution = statistics_service.get_tumor_distribution(db, current_user.id)
        return distribution
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tumor distribution: {str(e)}"
        )


@router.get("/weekly-analytics", response_model=List[WeeklyAnalytics])
async def get_weekly_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly analytics for the past 7 days.
    
    Returns daily analysis counts and accuracy rates for the current week.
    """
    try:
        analytics = statistics_service.get_weekly_analytics(db, current_user.id)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching weekly analytics: {str(e)}"
        )


@router.get("/monthly-trends", response_model=List[MonthlyTrends])
async def get_monthly_trends(
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly trends for the specified number of months.
    
    Args:
    - months: Number of months to include (default: 6, max: 12)
    
    Returns monthly diagnosis counts, findings, and average confidence scores.
    """
    try:
        # Validate months parameter
        if months < 1 or months > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Months parameter must be between 1 and 12"
            )
        
        trends = statistics_service.get_monthly_trends(db, current_user.id, months)
        return trends
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching monthly trends: {str(e)}"
        )


@router.get("/recent-activity", response_model=List[RecentActivity])
async def get_recent_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent diagnosis activity.
    
    Args:
    - limit: Number of recent activities to return (default: 10, max: 50)
    
    Returns recent diagnosis activities with severity levels.
    """
    try:
        # Validate limit parameter
        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit parameter must be between 1 and 50"
            )
        
        activity = statistics_service.get_recent_activity(db, current_user.id, limit)
        return activity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recent activity: {str(e)}"
        )


@router.get("/complete", response_model=StatisticsResponse)
async def get_complete_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete statistics for the dashboard.
    
    Returns all statistics in a single response:
    - Dashboard stats
    - Tumor distribution
    - Weekly analytics
    - Monthly trends
    - Recent activity
    """
    try:
        complete_stats = statistics_service.get_complete_statistics(db, current_user.id)
        return complete_stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching complete statistics: {str(e)}"
        )


@router.get("/user-summary", response_model=UserStatsSummary)
async def get_user_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics summary.
    
    Returns comprehensive user statistics including:
    - Total uploads and date range
    - Most common diagnosis type
    - Average confidence score
    - Breakdown by diagnosis type
    """
    try:
        summary = statistics_service.get_user_summary(db, current_user.id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user summary: {str(e)}"
        )