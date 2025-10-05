import os
import io
import torch
import torch.nn as nn
from torchvision import models, transforms
import timm
import numpy as np
from PIL import Image
import cv2
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Tuple, Optional
import uuid
from datetime import datetime

from app.models.diagnosis import DiagnosisResult
from app.core.config import settings
from app.services.cloudinary_service import cloudinary_service


# Device configuration - using CPU for your setup
DEVICE = "cpu"  # Force CPU usage as requested

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), "../models/ai_models")
CLASSIFICATION_MODEL_PATH = os.path.join(MODELS_DIR, "best_resnet18_mri.pth")
SEGMENTATION_MODEL_PATH = os.path.join(MODELS_DIR, "swinunet_best (6).pth")

# Class names for brain tumor classification
CLASS_NAMES = ["glioma", "meningioma", "notumor", "pituitary"]


class BrainTumorResNet18(nn.Module):
    """Brain tumor classification model using ResNet18"""
    def __init__(self, num_classes=4, pretrained=False):
        super().__init__()
        self.model = models.resnet18(pretrained=pretrained)
        in_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, num_classes)
        )
    
    def forward(self, x):
        return self.model(x)


class ConvBlock(nn.Module):
    """Convolutional block for SwinUNet"""
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    
    def forward(self, x):
        return self.block(x)


class SwinUNet(nn.Module):
    """SwinUNet model for brain tumor segmentation"""
    def __init__(self, encoder_name="swin_small_patch4_window7_224", pretrained=True, num_classes=1):
        super().__init__()
        self.encoder = timm.create_model(encoder_name, pretrained=pretrained,
                                       features_only=True, out_indices=(0,1,2,3))
        enc_chs = self.encoder.feature_info.channels()
        self.up3 = nn.ConvTranspose2d(enc_chs[3], enc_chs[2], 2, stride=2)
        self.dec3 = ConvBlock(enc_chs[2]*2, enc_chs[2])
        self.up2 = nn.ConvTranspose2d(enc_chs[2], enc_chs[1], 2, stride=2)
        self.dec2 = ConvBlock(enc_chs[1]*2, enc_chs[1])
        self.up1 = nn.ConvTranspose2d(enc_chs[1], enc_chs[0], 2, stride=2)
        self.dec1 = ConvBlock(enc_chs[0]*2, enc_chs[0])
        self.final_up = nn.ConvTranspose2d(enc_chs[0], 64, 2, stride=2)
        self.final_conv = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_classes, 1)
        )

    def _ensure_nchw(self, feat, expected_ch):
        if feat.ndim==4:
            if feat.shape[1]==expected_ch: return feat
            if feat.shape[-1]==expected_ch: return feat.permute(0,3,1,2).contiguous()
        return feat

    def forward(self, x):
        feats = self.encoder(x)
        expected = self.encoder.feature_info.channels()
        for i in range(len(feats)):
            feats[i] = self._ensure_nchw(feats[i], expected[i])
        f0,f1,f2,f3 = feats
        d3 = self.up3(f3)
        if d3.shape[-2:] != f2.shape[-2:]:
            d3 = nn.functional.interpolate(d3, size=f2.shape[-2:], mode='bilinear', align_corners=False)
        d3 = self.dec3(torch.cat([d3,f2], dim=1))
        d2 = self.up2(d3)
        if d2.shape[-2:] != f1.shape[-2:]:
            d2 = nn.functional.interpolate(d2, size=f1.shape[-2:], mode='bilinear', align_corners=False)
        d2 = self.dec2(torch.cat([d2,f1], dim=1))
        d1 = self.up1(d2)
        if d1.shape[-2:] != f0.shape[-2:]:
            d1 = nn.functional.interpolate(d1, size=f0.shape[-2:], mode='bilinear', align_corners=False)
        d1 = self.dec1(torch.cat([d1,f0], dim=1))
        out = self.final_up(d1)
        return self.final_conv(out)


class BrainTumorDiagnosisService:
    """Service for brain tumor diagnosis using classification and segmentation"""
    
    def __init__(self):
        self.classification_model = None
        self.segmentation_model = None
        self.clf_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.5,), std=(0.5,))
        ])
        self.seg_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])
        self._load_models()
    
    def _load_models(self):
        """Load the pre-trained models"""
        try:
            # Load classification model
            self.classification_model = BrainTumorResNet18(num_classes=4).to(DEVICE)
            self.classification_model.load_state_dict(
                torch.load(CLASSIFICATION_MODEL_PATH, map_location=DEVICE)
            )
            self.classification_model.eval()
            
            # Load segmentation model
            self.segmentation_model = SwinUNet().to(DEVICE)
            self.segmentation_model.load_state_dict(
                torch.load(SEGMENTATION_MODEL_PATH, map_location=DEVICE), strict=False
            )
            self.segmentation_model.eval()
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to load models: {str(e)}"
            )
    
    async def process_image(self, file: UploadFile, user_id: int) -> Tuple[str, float, Optional[str]]:
        """
        Process uploaded image for brain tumor diagnosis
        Returns: (predicted_class, confidence_score, segmentation_url)
        """
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        try:
            # Read image
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            
            # Classification
            pred_class, confidence = self._classify_image(image)
            
            # Segmentation (only if tumor is detected)
            segmentation_url = None
            if pred_class != "notumor":
                segmentation_url = await self._segment_image(image, file.filename, user_id)
            
            return pred_class, confidence, segmentation_url
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing image: {str(e)}"
            )
    
    def _classify_image(self, image: Image.Image) -> Tuple[str, float]:
        """Classify brain tumor type"""
        # Prepare image for classification
        x = self.clf_transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            logits = self.classification_model(x)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        
        pred_class = CLASS_NAMES[np.argmax(probs)]
        confidence = float(np.max(probs))
        
        return pred_class, confidence
    
    async def _segment_image(self, image: Image.Image, filename: str, user_id: int) -> str:
        """Segment brain tumor and upload result to Cloudinary"""
        # Prepare image for segmentation
        seg_in = self.seg_transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            mask = self.segmentation_model(seg_in)[0, 0].cpu().numpy()
        
        mask = (mask > 0.5).astype(np.uint8)
        
        # Create overlay
        img_np = np.array(image.resize((224, 224)))
        mask_resized = cv2.resize(mask, (img_np.shape[1], img_np.shape[0]), interpolation=cv2.INTER_NEAREST)
        overlay = img_np.copy()
        overlay[mask_resized > 0] = [255, 0, 0]  # red overlay
        blended = cv2.addWeighted(img_np, 0.7, overlay, 0.3, 0)
        
        # Convert back to PIL Image for Cloudinary upload
        segmentation_image = Image.fromarray(blended)
        
        # Upload segmentation result to Cloudinary
        segmentation_url = await cloudinary_service.upload_segmentation_image(
            image=segmentation_image,
            user_id=user_id,
            original_filename=filename,
            diagnosis_type="brain_tumor"
        )
        
        return segmentation_url
    
    async def save_diagnosis_result(
        self, 
        db: Session, 
        user_id: int, 
        file: UploadFile,
        predicted_class: str,
        confidence_score: float,
        segmentation_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DiagnosisResult:
        """Save diagnosis result to database"""
        
        # Upload image to Cloudinary
        image_url = await cloudinary_service.upload_diagnosis_image(
            file=file,
            user_id=user_id,
            diagnosis_type="brain_tumor"
        )
        
        # Create diagnosis result
        diagnosis_result = DiagnosisResult(
            user_id=user_id,
            image_path=image_url,  # Now stores Cloudinary URL
            predicted_class=predicted_class,
            confidence_score=confidence_score,
            segmentation_path=segmentation_url,  # Now stores Cloudinary URL
            diagnosis_type="brain_tumor",  # Explicitly set diagnosis_type
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
        """Get all brain tumor diagnoses for a user"""
        return db.query(DiagnosisResult)\
                .filter(
                    DiagnosisResult.user_id == user_id,
                    DiagnosisResult.diagnosis_type == "brain_tumor"
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
        """Get specific brain tumor diagnosis by ID for a user"""
        return db.query(DiagnosisResult)\
                .filter(
                    DiagnosisResult.id == diagnosis_id,
                    DiagnosisResult.user_id == user_id,
                    DiagnosisResult.diagnosis_type == "brain_tumor"
                )\
                .first()


# Singleton instance
diagnosis_service = BrainTumorDiagnosisService()