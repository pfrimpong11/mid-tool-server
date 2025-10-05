from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.diagnosis import DiagnosisResult
from app.schemas.stroke import (
    StrokeDiagnosisResponse,
    StrokeDiagnosisListResponse,
    StrokeDiagnosisUpdate
)
from app.services.stroke_service import stroke_service

router = APIRouter()


@router.post("/diagnose", response_model=StrokeDiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def diagnose_stroke(
    file: UploadFile = File(..., description="MRI image file for stroke diagnosis"),
    notes: Optional[str] = Form(None, description="Optional notes about the diagnosis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an MRI image for stroke diagnosis.
    
    - **file**: MRI image file (JPEG, PNG, etc.)
    - **notes**: Optional notes about the diagnosis
    
    Returns classification result: hemorrhagic_stroke, ischemic_stroke, or no_stroke.
    """
    try:
        # Process the image using the stroke service
        predicted_class, confidence_score, all_probabilities = await stroke_service.process_image(
            file, 
            current_user.id
        )
        
        # Reset file pointer for saving
        await file.seek(0)
        
        # Save diagnosis result to database
        diagnosis_result = await stroke_service.save_diagnosis_result(
            db=db,
            user_id=current_user.id,
            file=file,
            predicted_class=predicted_class,
            confidence_score=confidence_score,
            all_probabilities=all_probabilities,
            notes=notes
        )
        
        # Create response
        return StrokeDiagnosisResponse(
            id=diagnosis_result.id,
            predicted_class=diagnosis_result.predicted_class,
            confidence_score=diagnosis_result.confidence_score,
            all_probabilities=diagnosis_result.additional_results.get("all_probabilities", {}),
            diagnosis_type=diagnosis_result.diagnosis_type,
            image_url=diagnosis_result.image_path,
            notes=diagnosis_result.notes,
            created_at=diagnosis_result.created_at
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing stroke diagnosis: {str(e)}"
        )


@router.get("/", response_model=StrokeDiagnosisListResponse)
async def get_stroke_diagnoses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all stroke diagnosis results for the current user.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    diagnoses = stroke_service.get_user_diagnoses(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    
    # Count total diagnoses for pagination
    total = db.query(DiagnosisResult)\
             .filter(
                 DiagnosisResult.user_id == current_user.id,
                 DiagnosisResult.diagnosis_type == "stroke"
             ).count()
    
    diagnosis_responses = []
    for diagnosis in diagnoses:
        diagnosis_responses.append(
            StrokeDiagnosisResponse(
                id=diagnosis.id,
                predicted_class=diagnosis.predicted_class,
                confidence_score=diagnosis.confidence_score,
                all_probabilities=diagnosis.additional_results.get("all_probabilities", {}),
                diagnosis_type=diagnosis.diagnosis_type,
                image_url=diagnosis.image_path,
                notes=diagnosis.notes,
                created_at=diagnosis.created_at
            )
        )
    
    return StrokeDiagnosisListResponse(
        results=diagnosis_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=len(diagnosis_responses)
    )


@router.get("/{diagnosis_id}", response_model=StrokeDiagnosisResponse)
async def get_stroke_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific stroke diagnosis result by ID.
    """
    diagnosis = stroke_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stroke diagnosis not found"
        )
    
    return StrokeDiagnosisResponse(
        id=diagnosis.id,
        predicted_class=diagnosis.predicted_class,
        confidence_score=diagnosis.confidence_score,
        all_probabilities=diagnosis.additional_results.get("all_probabilities", {}),
        diagnosis_type=diagnosis.diagnosis_type,
        image_url=diagnosis.image_path,
        notes=diagnosis.notes,
        created_at=diagnosis.created_at
    )


@router.put("/{diagnosis_id}", response_model=StrokeDiagnosisResponse)
async def update_stroke_diagnosis(
    diagnosis_id: int,
    update_data: StrokeDiagnosisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notes for a specific stroke diagnosis.
    """
    diagnosis = stroke_service.update_diagnosis_notes(
        db=db,
        diagnosis_id=diagnosis_id,
        user_id=current_user.id,
        notes=update_data.notes
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stroke diagnosis not found"
        )
    
    return StrokeDiagnosisResponse(
        id=diagnosis.id,
        predicted_class=diagnosis.predicted_class,
        confidence_score=diagnosis.confidence_score,
        all_probabilities=diagnosis.additional_results.get("all_probabilities", {}),
        diagnosis_type=diagnosis.diagnosis_type,
        image_url=diagnosis.image_path,
        notes=diagnosis.notes,
        created_at=diagnosis.created_at
    )


@router.delete("/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stroke_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific stroke diagnosis.
    """
    success = stroke_service.delete_diagnosis(
        db=db,
        diagnosis_id=diagnosis_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stroke diagnosis not found"
        )
    
    return None
