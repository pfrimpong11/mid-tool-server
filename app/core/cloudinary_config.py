"""
Cloudinary configuration for handling image uploads to the cloud.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.core.config import settings


def configure_cloudinary():
    """Configure Cloudinary with credentials from environment variables"""
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True  # Use HTTPS URLs
    )


# Initialize Cloudinary configuration
configure_cloudinary()