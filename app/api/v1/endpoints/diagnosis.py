from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.diagnosis import DiagnosisResult
from app.schemas.diagnosis import (
    DiagnosisResponse, 
    DiagnosisListResponse, 
    DiagnosisUpdate
)
from app.services.diagnosis_service import diagnosis_service
from app.services.cloudinary_service import cloudinary_service

router = APIRouter()


@router.post("/diagnose", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def diagnose_brain_tumor(
    file: UploadFile = File(..., description="MRI image file for brain tumor diagnosis"),
    notes: Optional[str] = Form(None, description="Optional notes about the diagnosis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an MRI image for brain tumor diagnosis.
    
    - **file**: MRI image file (JPEG, PNG, etc.)
    - **notes**: Optional notes about the diagnosis
    
    Returns classification result and segmentation if tumor is detected.
    """
    try:
        # Process the image using the diagnosis service
        predicted_class, confidence_score, segmentation_url = await diagnosis_service.process_image(file, current_user.id)
        
        # Reset file pointer for saving
        await file.seek(0)
        
        # Save diagnosis result to database
        diagnosis_result = await diagnosis_service.save_diagnosis_result(
            db=db,
            user_id=current_user.id,
            file=file,
            predicted_class=predicted_class,
            confidence_score=confidence_score,
            segmentation_url=segmentation_url,
            notes=notes
        )
        
        # Create response
        return DiagnosisResponse(
            id=diagnosis_result.id,
            predicted_class=diagnosis_result.predicted_class,
            confidence_score=diagnosis_result.confidence_score,
            diagnosis_type=diagnosis_result.diagnosis_type,
            image_url=diagnosis_result.image_path,  # Now contains Cloudinary URL
            segmentation_url=diagnosis_result.segmentation_path,  # Now contains Cloudinary URL
            notes=diagnosis_result.notes,
            created_at=diagnosis_result.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing diagnosis: {str(e)}"
        )


@router.get("/", response_model=DiagnosisListResponse)
async def get_diagnoses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all diagnosis results for the current user.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    diagnoses = diagnosis_service.get_user_diagnoses(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    
    # Count total diagnoses for pagination
    total = db.query(DiagnosisResult)\
             .filter(
                 DiagnosisResult.user_id == current_user.id,
                 DiagnosisResult.diagnosis_type == "brain_tumor"
             ).count()
    
    diagnosis_responses = []
    for diagnosis in diagnoses:
        diagnosis_responses.append(
            DiagnosisResponse(
                id=diagnosis.id,
                predicted_class=diagnosis.predicted_class,
                confidence_score=diagnosis.confidence_score,
                diagnosis_type=diagnosis.diagnosis_type,
                image_url=diagnosis.image_path,  # Now contains Cloudinary URL
                segmentation_url=diagnosis.segmentation_path,  # Now contains Cloudinary URL
                notes=diagnosis.notes,
                created_at=diagnosis.created_at
            )
        )
    
    return DiagnosisListResponse(
        results=diagnosis_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=len(diagnosis_responses)
    )


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific diagnosis result by ID.
    """
    diagnosis = diagnosis_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )
    
    return DiagnosisResponse(
        id=diagnosis.id,
        predicted_class=diagnosis.predicted_class,
        confidence_score=diagnosis.confidence_score,
        diagnosis_type=diagnosis.diagnosis_type,
        image_url=diagnosis.image_path,  # Now contains Cloudinary URL
        segmentation_url=diagnosis.segmentation_path,  # Now contains Cloudinary URL
        notes=diagnosis.notes,
        created_at=diagnosis.created_at
    )


@router.patch("/{diagnosis_id}", response_model=DiagnosisResponse)
async def update_diagnosis(
    diagnosis_id: int,
    diagnosis_update: DiagnosisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update diagnosis notes.
    """
    diagnosis = diagnosis_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )
    
    # Update notes
    if diagnosis_update.notes is not None:
        diagnosis.notes = diagnosis_update.notes
    
    db.commit()
    db.refresh(diagnosis)
    
    return DiagnosisResponse(
        id=diagnosis.id,
        predicted_class=diagnosis.predicted_class,
        confidence_score=diagnosis.confidence_score,
        diagnosis_type=diagnosis.diagnosis_type,
        image_url=diagnosis.image_path,  # Now contains Cloudinary URL
        segmentation_url=diagnosis.segmentation_path,  # Now contains Cloudinary URL
        notes=diagnosis.notes,
        created_at=diagnosis.created_at
    )


@router.delete("/{diagnosis_id}")
async def delete_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a diagnosis result.
    """
    diagnosis = diagnosis_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )
    
    # Delete associated images from Cloudinary
    try:
        if diagnosis.image_path:
            public_id = cloudinary_service.extract_public_id_from_url(diagnosis.image_path)
            if public_id:
                cloudinary_service.delete_image(public_id)
        
        if diagnosis.segmentation_path:
            public_id = cloudinary_service.extract_public_id_from_url(diagnosis.segmentation_path)
            if public_id:
                cloudinary_service.delete_image(public_id)
    except Exception as e:
        # Log error but don't fail the deletion
        print(f"Error deleting images from Cloudinary: {e}")
    
    # Delete from database
    db.delete(diagnosis)
    db.commit()
    
    return {"message": "Diagnosis deleted successfully"}


# Image serving endpoints removed - images are now served directly from Cloudinary URLs