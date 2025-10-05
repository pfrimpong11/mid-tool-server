"""
Cloudinary service for handling image uploads to the cloud.
"""
import io
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import cloudinary.uploader
import cloudinary.api
from app.core.cloudinary_config import configure_cloudinary


class CloudinaryService:
    """Service for managing image uploads to Cloudinary"""
    
    def __init__(self):
        # Ensure Cloudinary is configured
        configure_cloudinary()
    
    async def upload_image(
        self, 
        file: UploadFile, 
        folder: str = "medical-diagnostics",
        public_id: Optional[str] = None,
        transformation: Optional[dict] = None
    ) -> str:
        """
        Upload image to Cloudinary and return the secure URL.
        
        Args:
            file: The uploaded file object
            folder: Cloudinary folder to organize uploads
            public_id: Optional custom public ID for the image
            transformation: Optional Cloudinary transformations to apply
            
        Returns:
            str: Secure URL of the uploaded image
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            # Read file contents
            contents = await file.read()
            
            # Generate unique public_id if not provided
            if not public_id:
                public_id = f"{uuid.uuid4()}_{file.filename}"
            
            # Prepare upload parameters
            upload_params = {
                "folder": folder,
                "public_id": public_id,
                "overwrite": True,
                "resource_type": "image",
                "format": "jpg",  # Convert all images to JPG for consistency
                "quality": "auto:good",  # Optimize quality
            }
            
            # Add transformations if provided
            if transformation:
                upload_params["transformation"] = transformation
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                io.BytesIO(contents),
                **upload_params
            )
            
            return result["secure_url"]
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image to Cloudinary: {str(e)}"
            )
    
    async def upload_diagnosis_image(
        self, 
        file: UploadFile, 
        user_id: int,
        diagnosis_type: str = "brain_tumor"
    ) -> str:
        """
        Upload original diagnosis image to Cloudinary.
        
        Args:
            file: The uploaded file object
            user_id: ID of the user
            diagnosis_type: Type of diagnosis (brain_tumor, breast_cancer, etc.)
            
        Returns:
            str: Secure URL of the uploaded image
        """
        folder = f"medical-diagnostics/{diagnosis_type}/images"
        public_id = f"user_{user_id}_{diagnosis_type}_{uuid.uuid4()}"
        
        # Apply basic transformations for medical images
        transformation = {
            "quality": "auto:good",
            "fetch_format": "auto",
            "width": 1024,
            "height": 1024,
            "crop": "limit"  # Don't crop, just limit size
        }
        
        return await self.upload_image(
            file=file,
            folder=folder,
            public_id=public_id,
            transformation=transformation
        )
    
    async def upload_segmentation_image(
        self, 
        image: Image.Image, 
        user_id: int,
        original_filename: str,
        diagnosis_type: str = "brain_tumor"
    ) -> str:
        """
        Upload segmentation result image to Cloudinary.
        
        Args:
            image: PIL Image object of the segmentation result
            user_id: ID of the user
            original_filename: Original filename for reference
            diagnosis_type: Type of diagnosis
            
        Returns:
            str: Secure URL of the uploaded segmentation image
        """
        try:
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=90)
            img_buffer.seek(0)
            
            folder = f"medical-diagnostics/{diagnosis_type}/segmentations"
            public_id = f"user_{user_id}_{diagnosis_type}_seg_{uuid.uuid4()}"
            
            # Upload parameters for segmentation images
            upload_params = {
                "folder": folder,
                "public_id": public_id,
                "overwrite": True,
                "resource_type": "image",
                "format": "jpg",
                "quality": "auto:good",
                "transformation": {
                    "quality": "auto:good",
                    "fetch_format": "auto"
                }
            }
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                img_buffer,
                **upload_params
            )
            
            return result["secure_url"]
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload segmentation image to Cloudinary: {str(e)}"
            )
    
    def delete_image(self, public_id: str) -> bool:
        """
        Delete image from Cloudinary by public ID.
        
        Args:
            public_id: The public ID of the image to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as e:
            # Log error but don't raise exception
            print(f"Failed to delete image from Cloudinary: {e}")
            return False
    
    def extract_public_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract public ID from Cloudinary URL for deletion purposes.
        
        Args:
            url: Cloudinary secure URL
            
        Returns:
            str: Public ID if extraction successful, None otherwise
        """
        try:
            # Cloudinary URLs typically follow this pattern:
            # https://res.cloudinary.com/{cloud_name}/image/upload/v{version}/{folder}/{public_id}.{format}
            parts = url.split('/')
            if 'cloudinary.com' in url and len(parts) >= 3:
                # Find the upload part and get everything after it
                upload_index = parts.index('upload')
                if upload_index + 2 < len(parts):
                    # Skip version (v1234567890) if present
                    start_index = upload_index + 1
                    if parts[start_index].startswith('v') and parts[start_index][1:].isdigit():
                        start_index += 1
                    
                    # Join the remaining parts and remove extension
                    public_id_with_ext = '/'.join(parts[start_index:])
                    public_id = public_id_with_ext.rsplit('.', 1)[0]  # Remove extension
                    return public_id
            return None
        except Exception:
            return None


# Singleton instance
cloudinary_service = CloudinaryService()