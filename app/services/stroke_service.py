import os
import io
import numpy as np
from PIL import Image
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict, Any
import uuid
from datetime import datetime

from app.services.cloudinary_service import cloudinary_service
from app.models.diagnosis import DiagnosisResult
from app.core.config import settings

# TensorFlow/Keras imports
try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. Stroke analysis will be disabled.")

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), "../models/ai_models")
STROKE_MODEL_PATH = os.path.join(MODELS_DIR, "stroke_classification_model.h5")

# Class names for stroke classification
CLASS_NAMES = ['hemorrhagic_stroke', 'ischemic_stroke', 'no_stroke']


class StrokeDiagnosisService:
    """Service for stroke diagnosis using ResNet50-based classification"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained stroke classification model"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available. Stroke model cannot be loaded.")
            return
        
        try:
            if os.path.exists(STROKE_MODEL_PATH):
                self.model = keras.models.load_model(STROKE_MODEL_PATH)
                print("Stroke classification model loaded successfully")
            else:
                print(f"Warning: Stroke model not found at {STROKE_MODEL_PATH}")
        except Exception as e:
            print(f"Error loading stroke model: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def preprocess_image_for_prediction(
        self, 
        image: Image.Image, 
        target_size: Tuple[int, int] = (224, 224),
        pixel_threshold: int = 40
    ) -> Optional[np.ndarray]:
        """
        Preprocess MRI image for stroke classification
        
        Args:
            image: PIL Image object
            target_size: Target size for resizing (default: 224x224)
            pixel_threshold: Threshold for content detection (default: 40)
        
        Returns:
            Preprocessed image array ready for model prediction
        """
        try:
            # Convert to grayscale
            img = image.convert("L")
            original_width, original_height = img.size
            
            # Convert to numpy array for processing
            data = np.array(img)
            
            # Detect content boundaries
            rows_with_content = np.any(data > pixel_threshold, axis=1)
            cols_with_content = np.any(data > pixel_threshold, axis=0)
            
            try:
                min_row = np.where(rows_with_content)[0][0]
                max_row = np.where(rows_with_content)[0][-1]
                min_col = np.where(cols_with_content)[0][0]
                max_col = np.where(cols_with_content)[0][-1]
            except IndexError:
                # No content detected, use original image
                cropped_img = img
            else:
                # Add buffer around detected content
                buffer = 5
                min_row = max(0, min_row - buffer)
                max_row = min(original_height - 1, max_row + buffer)
                min_col = max(0, min_col - buffer)
                max_col = min(original_width - 1, max_col + buffer)
                
                # Crop image to content
                cropped_img = img.crop((min_col, min_row, max_col + 1, max_row + 1))
            
            # Resize to target size
            processed_img = cropped_img.resize(target_size, Image.LANCZOS)
            
            # Convert back to RGB (model expects RGB input)
            if processed_img.mode == 'L':
                processed_img = processed_img.convert('RGB')
            
            # Convert to array and expand dimensions for batch
            img_array = keras.utils.img_to_array(processed_img)
            img_array = tf.expand_dims(img_array, 0)
            
            return img_array
            
        except Exception as e:
            print(f"Error preprocessing image: {str(e)}")
            return None
    
    async def process_image(
        self, 
        file: UploadFile, 
        user_id: int
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Process uploaded MRI image for stroke diagnosis
        
        Args:
            file: Uploaded image file
            user_id: ID of the user requesting diagnosis
        
        Returns:
            Tuple of (predicted_class, confidence_score, all_probabilities)
        """
        if self.model is None:
            raise HTTPException(
                status_code=503,
                detail="Stroke classification model is not available"
            )
        
        # Check content type if available
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file extension as backup
        if file.filename:
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail="File must be an image with valid extension")
        
        try:
            # Read image
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Preprocess image
            preprocessed_img = self.preprocess_image_for_prediction(image)
            
            if preprocessed_img is None:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to preprocess image"
                )
            
            # Make prediction
            predictions = self.model.predict(preprocessed_img)
            predicted_class_index = np.argmax(predictions[0])
            predicted_class_name = CLASS_NAMES[predicted_class_index]
            confidence = float(np.max(predictions[0]))
            
            # Create probability dictionary for all classes
            all_probabilities = {
                CLASS_NAMES[i]: float(predictions[0][i]) 
                for i in range(len(CLASS_NAMES))
            }
            
            return predicted_class_name, confidence, all_probabilities
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing stroke diagnosis: {str(e)}"
            )
    
    async def save_diagnosis_result(
        self,
        db: Session,
        user_id: int,
        file: UploadFile,
        predicted_class: str,
        confidence_score: float,
        all_probabilities: Dict[str, float],
        notes: Optional[str] = None
    ) -> DiagnosisResult:
        """
        Save stroke diagnosis result to database and upload image to Cloudinary
        
        Args:
            db: Database session
            user_id: ID of the user
            file: Uploaded image file
            predicted_class: Predicted stroke class
            confidence_score: Confidence score of prediction
            all_probabilities: Dictionary of all class probabilities
            notes: Optional notes about the diagnosis
        
        Returns:
            Created DiagnosisResult object
        """
        try:
            # Reset file pointer
            await file.seek(0)
            
            # Upload original image to Cloudinary
            image_url = await cloudinary_service.upload_diagnosis_image(
                file=file,
                user_id=user_id,
                diagnosis_type="stroke"
            )
            
            # Create diagnosis result
            diagnosis_result = DiagnosisResult(
                user_id=user_id,
                image_path=image_url,
                predicted_class=predicted_class,
                confidence_score=confidence_score,
                diagnosis_type="stroke",
                analysis_type="stroke_classification",
                additional_results={
                    "all_probabilities": all_probabilities,
                    "class_names": CLASS_NAMES
                },
                notes=notes
            )
            
            db.add(diagnosis_result)
            db.commit()
            db.refresh(diagnosis_result)
            
            return diagnosis_result
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error saving diagnosis result: {str(e)}"
            )
    
    def get_user_diagnoses(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[DiagnosisResult]:
        """
        Get all stroke diagnoses for a user
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of DiagnosisResult objects
        """
        return db.query(DiagnosisResult)\
                 .filter(
                     DiagnosisResult.user_id == user_id,
                     DiagnosisResult.diagnosis_type == "stroke"
                 )\
                 .order_by(DiagnosisResult.created_at.desc())\
                 .offset(skip)\
                 .limit(limit)\
                 .all()
    
    def get_diagnosis_by_id(
        self,
        db: Session,
        diagnosis_id: int,
        user_id: int
    ) -> Optional[DiagnosisResult]:
        """
        Get a specific stroke diagnosis by ID
        
        Args:
            db: Database session
            diagnosis_id: ID of the diagnosis
            user_id: ID of the user (for authorization)
        
        Returns:
            DiagnosisResult object or None if not found
        """
        return db.query(DiagnosisResult)\
                 .filter(
                     DiagnosisResult.id == diagnosis_id,
                     DiagnosisResult.user_id == user_id,
                     DiagnosisResult.diagnosis_type == "stroke"
                 )\
                 .first()
    
    def update_diagnosis_notes(
        self,
        db: Session,
        diagnosis_id: int,
        user_id: int,
        notes: str
    ) -> Optional[DiagnosisResult]:
        """
        Update notes for a stroke diagnosis
        
        Args:
            db: Database session
            diagnosis_id: ID of the diagnosis
            user_id: ID of the user (for authorization)
            notes: Updated notes
        
        Returns:
            Updated DiagnosisResult object or None if not found
        """
        diagnosis = self.get_diagnosis_by_id(db, diagnosis_id, user_id)
        
        if diagnosis:
            diagnosis.notes = notes
            db.commit()
            db.refresh(diagnosis)
        
        return diagnosis
    
    def delete_diagnosis(
        self,
        db: Session,
        diagnosis_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a stroke diagnosis
        
        Args:
            db: Database session
            diagnosis_id: ID of the diagnosis
            user_id: ID of the user (for authorization)
        
        Returns:
            True if deleted, False if not found
        """
        diagnosis = self.get_diagnosis_by_id(db, diagnosis_id, user_id)
        
        if diagnosis:
            # Optionally delete image from Cloudinary
            try:
                if diagnosis.image_path:
                    # Extract public_id from URL and delete
                    cloudinary_service.delete_image_from_url(diagnosis.image_path)
            except Exception as e:
                print(f"Warning: Failed to delete image from Cloudinary: {str(e)}")
            
            db.delete(diagnosis)
            db.commit()
            return True
        
        return False


# Create a singleton instance
stroke_service = StrokeDiagnosisService()
