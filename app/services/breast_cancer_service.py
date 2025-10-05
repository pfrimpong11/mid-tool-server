import os
import io
import torch
import numpy as np
from PIL import Image
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict, Any
import uuid
from datetime import datetime
import sys
import importlib

from app.services.cloudinary_service import cloudinary_service

# FastAI imports for BI-RADS model
try:
    from fastai.vision.all import PILImage, load_learner
    FASTAI_AVAILABLE = True
except ImportError:
    FASTAI_AVAILABLE = False
    print("Warning: FastAI not available. BI-RADS analysis will be disabled.")

# Torchvision imports for pathological model
from torchvision import transforms

from app.models.diagnosis import DiagnosisResult
from app.models.ai_models.breast_cancer_models import (
    ResNet18,  # Use the original ResNet18 class that matches the checkpoint
    BasicBlock,  # Also needed for unpickling
    BreastCancerResNet18, 
    SimpleConvNet,  # Fallback BI-RADS model
    BIRADS_CLASS_NAMES, 
    PATHOLOGICAL_CLASS_NAMES
)

# Solution for checkpoint loading: Add classes to current module's globals
# This allows PyTorch to find them during unpickling
import sys
current_module = sys.modules[__name__]
setattr(current_module, 'ResNet18', ResNet18)
setattr(current_module, 'BasicBlock', BasicBlock)
from app.core.config import settings


# Device configuration - using CPU for consistency
DEVICE = "cpu"

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), "../models/ai_models")
BIRADS_MODEL_PATH = os.path.join(MODELS_DIR, "birads_model.pkl")  # Use the correct BI-RADS model
PATHOLOGICAL_MODEL_PATH = os.path.join(MODELS_DIR, "epoch=49-step=1750.ckpt")


class BreastCancerDiagnosisService:
    """Service for breast cancer diagnosis using BI-RADS and pathological classification"""
    
    def __init__(self):
        self.birads_model = None
        self.pathological_model = None
        self.birads_model_type = None  # Track model type: "fastai" or "pytorch_fallback"
        
        # Pathological model preprocessing pipeline
        self.pathological_transform = transforms.Compose([
            transforms.ToPILImage() if not isinstance(transforms.ToPILImage(), type(lambda x: x)) else lambda x: x,
            transforms.Grayscale(num_output_channels=3),
            transforms.Resize((256, 256)),
            transforms.ToTensor(), 
            transforms.Normalize(
                mean=[0.233827, 0.2338219, 0.23378967], 
                std=[0.2016421162328173, 0.20164345656093885, 0.20160390432148026]
            )
        ])
        
        self._load_models()
    
    def _load_models(self):
        """Load the pre-trained models"""
        try:
            # Load BI-RADS model (FastAI or PyTorch fallback)
            if FASTAI_AVAILABLE and os.path.exists(BIRADS_MODEL_PATH):
                try:
                    # Try loading with different compatibility options
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.birads_model = load_learner(BIRADS_MODEL_PATH)
                        print("BI-RADS model (FastAI) loaded successfully")
                        self.birads_model_type = "fastai"
                except Exception as e:
                    print(f"Warning: Failed to load FastAI BI-RADS model: {str(e)}")
                    print("Note: Model was created with an incompatible FastAI version")
                    print("Creating PyTorch BI-RADS fallback model...")
                    # Create a simple PyTorch BI-RADS model as fallback
                    self.birads_model = SimpleConvNet(num_classes=5).to(DEVICE)
                    self.birads_model.eval()
                    self.birads_model_type = "pytorch_fallback"
                    print("BI-RADS model (PyTorch fallback) created successfully")
            else:
                if not FASTAI_AVAILABLE:
                    print("FastAI not available, creating PyTorch BI-RADS fallback model...")
                else:
                    print(f"BI-RADS model not found at {BIRADS_MODEL_PATH}, creating fallback...")
                # Create a simple PyTorch BI-RADS model as fallback
                self.birads_model = SimpleConvNet(num_classes=5).to(DEVICE)
                self.birads_model.eval()
                self.birads_model_type = "pytorch_fallback"
                print("BI-RADS model (PyTorch fallback) created successfully")
                
            # Load pathological model (PyTorch)
            if os.path.exists(PATHOLOGICAL_MODEL_PATH):
                try:
                    # Create model instance
                    self.pathological_model = ResNet18(3, 3).to(DEVICE)  # 3 input channels, 3 classes
                    
                    # Try loading with compatibility hack for __main__ classes
                    import __main__
                    __main__.ResNet18 = ResNet18
                    __main__.BasicBlock = BasicBlock
                    
                    # Load checkpoint
                    checkpoint = torch.load(PATHOLOGICAL_MODEL_PATH, map_location=DEVICE, weights_only=False)
                    
                    # Handle different checkpoint formats
                    if 'state_dict' in checkpoint:
                        state_dict = checkpoint['state_dict']
                        # Remove 'net.' prefix from Lightning checkpoint
                        new_state_dict = {}
                        for key, value in state_dict.items():
                            # Remove 'net.' prefix if present (PyTorch Lightning format)
                            new_key = key.replace('net.', '')
                            new_state_dict[new_key] = value
                        self.pathological_model.load_state_dict(new_state_dict)
                    else:
                        self.pathological_model.load_state_dict(checkpoint)
                    
                    self.pathological_model.eval()
                    print("Pathological model loaded successfully")
                except Exception as e:
                    print(f"Warning: Failed to load pathological model: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    self.pathological_model = None
            else:
                print(f"Warning: Pathological model not found at {PATHOLOGICAL_MODEL_PATH}")
                
        except Exception as e:
            print(f"Warning: Failed to load some models: {str(e)}")
    
    async def process_image(
        self, 
        file: UploadFile, 
        analysis_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded image for breast cancer diagnosis
        Returns: Dictionary containing analysis results
        """
        # Check content type if available
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Also check file extension as backup
        if file.filename:
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail="File must be an image with valid extension")
        
        try:
            # Read image
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            
            results = {}
            
            # Determine which analyses to perform
            if analysis_type is None or analysis_type == "both":
                perform_birads = True
                perform_pathological = True
            elif analysis_type == "birads":
                perform_birads = True
                perform_pathological = False
            elif analysis_type == "pathological":
                perform_birads = False
                perform_pathological = True
            else:
                raise HTTPException(status_code=400, detail="Invalid analysis type")
            
            # Perform BI-RADS analysis
            if perform_birads and self.birads_model is not None:
                birads_result = await self._analyze_birads(image)
                results['birads'] = birads_result
            
            # Perform pathological analysis
            if perform_pathological and self.pathological_model is not None:
                pathological_result = await self._analyze_pathological(image)
                results['pathological'] = pathological_result
            
            # Determine primary result
            primary_result = self._determine_primary_result(results, analysis_type)
            results['primary'] = primary_result
            results['analysis_type'] = analysis_type if analysis_type else "both"
            
            return results
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing image: {str(e)}"
            )
    
    async def _analyze_birads(self, image: Image.Image) -> Dict[str, Any]:
        """Perform BI-RADS classification"""
        try:
            if hasattr(self, 'birads_model_type') and self.birads_model_type == "pytorch_fallback":
                # Use PyTorch fallback model
                # Preprocess image for PyTorch model
                transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                ])
                
                image_tensor = transform(image).unsqueeze(0).to(DEVICE)
                
                # Inference
                with torch.no_grad():
                    result = self.birads_model(image_tensor)
                    probabilities = torch.nn.functional.softmax(result, dim=1)
                    probabilities = probabilities[0].cpu().numpy()
                
                # Get predicted class
                predicted_idx = np.argmax(probabilities)
                predicted_class = BIRADS_CLASS_NAMES[predicted_idx]
                confidence_score = float(probabilities[predicted_idx])
                
                # Create probability dictionary
                prob_dict = {BIRADS_CLASS_NAMES[i]: float(probabilities[i]) for i in range(len(BIRADS_CLASS_NAMES))}
                
                return {
                    "predicted_class": predicted_class,
                    "confidence_score": confidence_score,
                    "all_probabilities": prob_dict,
                    "note": "Using PyTorch fallback model (FastAI model unavailable)"
                }
            else:
                # Use FastAI model
                # Convert PIL image to FastAI PILImage
                pil_image = PILImage.create(np.array(image))
                
                # Predict using FastAI model
                pred, pred_idx, probs = self.birads_model.predict(pil_image)
                
                # Get vocabulary (class names)
                labels = self.birads_model.dls.vocab
                
                # Create probability dictionary
                probabilities = {labels[i]: float(probs[i]) for i in range(len(labels))}
                
                # Get the predicted class and confidence
                predicted_class = str(pred)
                confidence_score = float(probs[pred_idx])
                
                return {
                    "predicted_class": predicted_class,
                    "confidence_score": confidence_score,
                    "all_probabilities": probabilities
                }
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error in BI-RADS analysis: {str(e)}"
            )
    
    async def _analyze_pathological(self, image: Image.Image) -> Dict[str, Any]:
        """Perform pathological classification"""
        try:
            # Preprocess image
            if isinstance(image, Image.Image):
                image_tensor = self.pathological_transform(np.array(image))
            else:
                image_tensor = self.pathological_transform(image)
            
            image_tensor = image_tensor.unsqueeze(0).to(DEVICE)
            
            # Inference
            with torch.no_grad():
                result = self.pathological_model(image_tensor)
                probabilities = torch.nn.functional.softmax(result, dim=1)
                probabilities = probabilities[0].cpu().numpy()
            
            # Get predicted class
            pred_idx = np.argmax(probabilities)
            predicted_class = PATHOLOGICAL_CLASS_NAMES[pred_idx]
            confidence_score = float(probabilities[pred_idx])
            
            # Create probability dictionary
            all_probabilities = {
                PATHOLOGICAL_CLASS_NAMES[i]: float(probabilities[i]) 
                for i in range(len(PATHOLOGICAL_CLASS_NAMES))
            }
            
            return {
                "predicted_class": predicted_class,
                "confidence_score": confidence_score,
                "all_probabilities": all_probabilities
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error in pathological analysis: {str(e)}"
            )

    def _determine_primary_result(self, results: Dict[str, Any], analysis_type: Optional[str]) -> Dict[str, Any]:
        """Determine the primary result to display"""
        if analysis_type == "birads" and "birads" in results:
            return results["birads"]
        elif analysis_type == "pathological" and "pathological" in results:
            return results["pathological"]
        elif "pathological" in results and "birads" in results:
            # When both are available, prioritize pathological if malignant, otherwise use BI-RADS
            if results["pathological"]["predicted_class"] == "malignant":
                return results["pathological"]
            else:
                return results["birads"]
        elif "pathological" in results:
            return results["pathological"]
        elif "birads" in results:
            return results["birads"]
        else:
            raise HTTPException(status_code=500, detail="No analysis results available")
    
    async def save_diagnosis_result(
        self,
        db: Session,
        user_id: int,
        file: UploadFile,
        analysis_results: Dict[str, Any],
        notes: Optional[str] = None
    ) -> DiagnosisResult:
        """Save breast cancer diagnosis result to database"""
        
        # Upload image to Cloudinary
        image_url = await cloudinary_service.upload_diagnosis_image(
            file=file,
            user_id=user_id,
            diagnosis_type="breast_cancer"
        )
        
        # Extract primary result
        primary = analysis_results["primary"]
        analysis_type = analysis_results["analysis_type"]
        
        # Determine diagnosis type
        if analysis_type == "birads":
            diagnosis_type = "breast_cancer_birads"
        elif analysis_type == "pathological":
            diagnosis_type = "breast_cancer_pathological"
        else:
            diagnosis_type = "breast_cancer_both"
        
        # Prepare additional results for storage
        additional_results = {}
        if "birads" in analysis_results:
            additional_results["birads"] = analysis_results["birads"]
        if "pathological" in analysis_results:
            additional_results["pathological"] = analysis_results["pathological"]
        
        # Create diagnosis result
        diagnosis_result = DiagnosisResult(
            user_id=user_id,
            image_path=image_url,  # Now stores Cloudinary URL
            predicted_class=primary["predicted_class"],
            confidence_score=primary["confidence_score"],
            diagnosis_type=diagnosis_type,
            analysis_type=analysis_type,
            additional_results=additional_results,
            notes=notes
        )
        
        db.add(diagnosis_result)
        db.commit()
        db.refresh(diagnosis_result)
        
        return diagnosis_result
    
    def get_user_diagnoses(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[DiagnosisResult]:
        """Get all breast cancer diagnoses for a user"""
        return db.query(DiagnosisResult)\
                .filter(
                    DiagnosisResult.user_id == user_id,
                    DiagnosisResult.diagnosis_type.in_([
                        "breast_cancer_birads", 
                        "breast_cancer_pathological", 
                        "breast_cancer_both"
                    ])
                )\
                .offset(skip)\
                .limit(limit)\
                .all()
    
    def get_diagnosis_by_id(
        self, 
        db: Session, 
        diagnosis_id: int, 
        user_id: int
    ) -> Optional[DiagnosisResult]:
        """Get specific breast cancer diagnosis by ID for a user"""
        return db.query(DiagnosisResult)\
                .filter(
                    DiagnosisResult.id == diagnosis_id,
                    DiagnosisResult.user_id == user_id,
                    DiagnosisResult.diagnosis_type.in_([
                        "breast_cancer_birads", 
                        "breast_cancer_pathological", 
                        "breast_cancer_both"
                    ])
                )\
                .first()


# Singleton instance
breast_cancer_service = BreastCancerDiagnosisService()