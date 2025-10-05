from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.diagnosis import DiagnosisResult
from app.schemas.breast_cancer import (
    BreastCancerDiagnosisResponse,
    BreastCancerDiagnosisListResponse,
    BreastCancerDiagnosisUpdate,
    BreastCancerAnalysisType,
    BiRadsResult,
    PathologicalResult
)
from app.services.breast_cancer_service import breast_cancer_service
from app.services.cloudinary_service import cloudinary_service

router = APIRouter()


@router.post("/diagnose", response_model=BreastCancerDiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def diagnose_breast_cancer(
    file: UploadFile = File(..., description="Medical image file for breast cancer diagnosis"),
    analysis_type: Optional[BreastCancerAnalysisType] = Form(None, description="Type of analysis: birads, pathological, or both"),
    notes: Optional[str] = Form(None, description="Optional notes about the diagnosis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image for breast cancer diagnosis.
    
    - **file**: Medical image file (mammogram, histology image, etc.)
    - **analysis_type**: Type of analysis to perform:
        - birads: BI-RADS Classification (Imaging Analysis) for mammograms
        - pathological: Pathological Classification (Tissue Analysis) for histology
        - both: Perform both analyses (default if not specified)
    - **notes**: Optional notes about the diagnosis
    
    Returns classification results based on the selected analysis type(s).
    """
    try:
        # Process the image using the breast cancer service
        analysis_results = await breast_cancer_service.process_image(file, analysis_type)
        
        # Reset file pointer for saving
        await file.seek(0)
        
        # Save diagnosis result to database
        diagnosis_result = await breast_cancer_service.save_diagnosis_result(
            db=db,
            user_id=current_user.id,
            file=file,
            analysis_results=analysis_results,
            notes=notes
        )
        
        # Prepare response data
        response_data = {
            "id": diagnosis_result.id,
            "diagnosis_type": diagnosis_result.diagnosis_type,
            "analysis_type": diagnosis_result.analysis_type,
            "image_url": diagnosis_result.image_path,  # Now contains Cloudinary URL
            "notes": diagnosis_result.notes,
            "created_at": diagnosis_result.created_at,
            "predicted_class": diagnosis_result.predicted_class,
            "confidence_score": diagnosis_result.confidence_score
        }
        
        # Add specific analysis results
        additional_results = diagnosis_result.additional_results or {}
        
        if "birads" in additional_results:
            birads_data = additional_results["birads"]
            response_data["birads_result"] = BiRadsResult(
                predicted_class=birads_data["predicted_class"],
                confidence_score=birads_data["confidence_score"],
                all_probabilities=birads_data["all_probabilities"]
            )
        
        if "pathological" in additional_results:
            path_data = additional_results["pathological"]
            response_data["pathological_result"] = PathologicalResult(
                predicted_class=path_data["predicted_class"],
                confidence_score=path_data["confidence_score"],
                all_probabilities=path_data["all_probabilities"]
            )
        
        return BreastCancerDiagnosisResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing breast cancer diagnosis: {str(e)}"
        )


@router.get("/", response_model=BreastCancerDiagnosisListResponse)
async def get_breast_cancer_diagnoses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all breast cancer diagnosis results for the current user.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    diagnoses = breast_cancer_service.get_user_diagnoses(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    
    # Count total diagnoses for pagination
    total = db.query(DiagnosisResult)\
             .filter(
                 DiagnosisResult.user_id == current_user.id,
                 DiagnosisResult.diagnosis_type.in_([
                     "breast_cancer_birads", 
                     "breast_cancer_pathological", 
                     "breast_cancer_both"
                 ])
             ).count()
    
    diagnosis_responses = []
    for diagnosis in diagnoses:
        response_data = {
            "id": diagnosis.id,
            "diagnosis_type": diagnosis.diagnosis_type,
            "analysis_type": diagnosis.analysis_type,
            "image_url": diagnosis.image_path,  # Now contains Cloudinary URL
            "notes": diagnosis.notes,
            "created_at": diagnosis.created_at,
            "predicted_class": diagnosis.predicted_class,
            "confidence_score": diagnosis.confidence_score
        }
        
        # Add specific analysis results
        additional_results = diagnosis.additional_results or {}
        
        if "birads" in additional_results:
            birads_data = additional_results["birads"]
            response_data["birads_result"] = BiRadsResult(
                predicted_class=birads_data["predicted_class"],
                confidence_score=birads_data["confidence_score"],
                all_probabilities=birads_data["all_probabilities"]
            )
        
        if "pathological" in additional_results:
            path_data = additional_results["pathological"]
            response_data["pathological_result"] = PathologicalResult(
                predicted_class=path_data["predicted_class"],
                confidence_score=path_data["confidence_score"],
                all_probabilities=path_data["all_probabilities"]
            )
        
        diagnosis_responses.append(BreastCancerDiagnosisResponse(**response_data))
    
    return BreastCancerDiagnosisListResponse(
        results=diagnosis_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=len(diagnosis_responses)
    )


@router.get("/{diagnosis_id}", response_model=BreastCancerDiagnosisResponse)
async def get_breast_cancer_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific breast cancer diagnosis result by ID.
    """
    diagnosis = breast_cancer_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breast cancer diagnosis not found"
        )
    
    response_data = {
        "id": diagnosis.id,
        "diagnosis_type": diagnosis.diagnosis_type,
        "analysis_type": diagnosis.analysis_type,
        "image_url": diagnosis.image_path,  # Now contains Cloudinary URL
        "notes": diagnosis.notes,
        "created_at": diagnosis.created_at,
        "predicted_class": diagnosis.predicted_class,
        "confidence_score": diagnosis.confidence_score
    }
    
    # Add specific analysis results
    additional_results = diagnosis.additional_results or {}
    
    if "birads" in additional_results:
        birads_data = additional_results["birads"]
        response_data["birads_result"] = BiRadsResult(
            predicted_class=birads_data["predicted_class"],
            confidence_score=birads_data["confidence_score"],
            all_probabilities=birads_data["all_probabilities"]
        )
    
    if "pathological" in additional_results:
        path_data = additional_results["pathological"]
        response_data["pathological_result"] = PathologicalResult(
            predicted_class=path_data["predicted_class"],
            confidence_score=path_data["confidence_score"],
            all_probabilities=path_data["all_probabilities"]
        )
    
    return BreastCancerDiagnosisResponse(**response_data)


@router.patch("/{diagnosis_id}", response_model=BreastCancerDiagnosisResponse)
async def update_breast_cancer_diagnosis(
    diagnosis_id: int,
    diagnosis_update: BreastCancerDiagnosisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update breast cancer diagnosis notes.
    """
    diagnosis = breast_cancer_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breast cancer diagnosis not found"
        )
    
    # Update notes
    if diagnosis_update.notes is not None:
        diagnosis.notes = diagnosis_update.notes
    
    db.commit()
    db.refresh(diagnosis)
    
    response_data = {
        "id": diagnosis.id,
        "diagnosis_type": diagnosis.diagnosis_type,
        "analysis_type": diagnosis.analysis_type,
        "image_url": diagnosis.image_path,  # Now contains Cloudinary URL
        "notes": diagnosis.notes,
        "created_at": diagnosis.created_at,
        "predicted_class": diagnosis.predicted_class,
        "confidence_score": diagnosis.confidence_score
    }
    
    # Add specific analysis results
    additional_results = diagnosis.additional_results or {}
    
    if "birads" in additional_results:
        birads_data = additional_results["birads"]
        response_data["birads_result"] = BiRadsResult(
            predicted_class=birads_data["predicted_class"],
            confidence_score=birads_data["confidence_score"],
            all_probabilities=birads_data["all_probabilities"]
        )
    
    if "pathological" in additional_results:
        path_data = additional_results["pathological"]
        response_data["pathological_result"] = PathologicalResult(
            predicted_class=path_data["predicted_class"],
            confidence_score=path_data["confidence_score"],
            all_probabilities=path_data["all_probabilities"]
        )
    
    return BreastCancerDiagnosisResponse(**response_data)


@router.delete("/{diagnosis_id}")
async def delete_breast_cancer_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a breast cancer diagnosis result.
    """
    diagnosis = breast_cancer_service.get_diagnosis_by_id(
        db=db, 
        diagnosis_id=diagnosis_id, 
        user_id=current_user.id
    )
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breast cancer diagnosis not found"
        )
    
    # Delete associated image from Cloudinary
    try:
        if diagnosis.image_path:
            public_id = cloudinary_service.extract_public_id_from_url(diagnosis.image_path)
            if public_id:
                cloudinary_service.delete_image(public_id)
    except Exception as e:
        # Log error but don't fail the deletion
        print(f"Error deleting image from Cloudinary: {e}")
    
    # Delete from database
    db.delete(diagnosis)
    db.commit()
    
    return {"message": "Breast cancer diagnosis deleted successfully"}


# Image serving endpoints removed - images are now served directly from Cloudinary URLs