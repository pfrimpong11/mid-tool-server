from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    verify_password_reset_token
)


class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by email (case-insensitive)"""
        from sqlalchemy import func
        query = db.query(User).filter(func.lower(User.email) == func.lower(email))
        if not include_deleted:
            query = query.filter(User.is_deleted == False)
        return query.first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str, include_deleted: bool = False) -> Optional[User]:
        """Get user by username (case-insensitive)"""
        from sqlalchemy import func
        query = db.query(User).filter(func.lower(User.username) == func.lower(username))
        if not include_deleted:
            query = query.filter(User.is_deleted == False)
        return query.first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """Get user by ID"""
        query = db.query(User).filter(User.id == user_id)
        if not include_deleted:
            query = query.filter(User.is_deleted == False)
        return query.first()
    
    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user by username/email and password"""
        # Try to find user by email first, then by username
        user = None
        if "@" in username_or_email:
            user = AuthService.get_user_by_email(db, username_or_email)
        else:
            user = AuthService.get_user_by_username(db, username_or_email)
        
        if not user:
            return None
        
        # Check if user account is deleted
        if user.is_deleted:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        # Validate GDPR consent
        if not user_create.gdpr_consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GDPR consent is required to create an account"
            )
        
        # Check if user already exists
        existing_user = AuthService.get_user_by_email(db, user_create.email, include_deleted=True)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_user = AuthService.get_user_by_username(db, user_create.username, include_deleted=True)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        from datetime import datetime
        hashed_password = get_password_hash(user_create.password)
        current_time = datetime.utcnow()
        
        db_user = User(
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            username=user_create.username.lower(),  # Store username in lowercase
            email=user_create.email.lower(),  # Also store email in lowercase for consistency
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,  # User needs to verify email
            gdpr_consent=user_create.gdpr_consent,
            gdpr_consent_date=current_time if user_create.gdpr_consent else None,
            marketing_consent=user_create.marketing_consent or False,
            marketing_consent_date=current_time if user_create.marketing_consent else None
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def create_tokens(user_id: int) -> dict:
        """Create access and refresh tokens for user"""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def initiate_password_reset(db: Session, email: str) -> str:
        """Initiate password reset process"""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email does not exist"
            )
        
        # Generate reset token
        reset_token = generate_password_reset_token(email)
        
        # Save reset token to database
        user.reset_token = reset_token
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=48)
        
        db.commit()
        
        return reset_token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> User:
        """Reset user password with token"""
        # Verify reset token
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )
        
        # Get user by email
        user = AuthService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if token matches and is not expired
        if (user.reset_token != token or 
            not user.reset_token_expires_at or 
            user.reset_token_expires_at < datetime.utcnow()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )
        
        # Update password and clear reset token
        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
        """Change user password"""
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_user_settings(db: Session, user_id: int, settings_update) -> User:
        """Update user settings"""
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update settings fields if provided
        update_data = settings_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_user_profile(db: Session, user_id: int, user_update) -> User:
        """Update user profile information"""
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email is being changed and if it's already taken
        if user_update.email and user_update.email != user.email:
            existing_user = AuthService.get_user_by_email(db, user_update.email, include_deleted=True)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Check if username is being changed and if it's already taken
        if user_update.username and user_update.username != user.username:
            existing_user = AuthService.get_user_by_username(db, user_update.username, include_deleted=True)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Update fields if provided
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                # Normalize email and username to lowercase
                if field == 'email' and value:
                    value = value.lower()
                elif field == 'username' and value:
                    value = value.lower()
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def delete_user_account(db: Session, user_id: int) -> None:
        """Soft delete user account - mark as deleted and anonymize personal data"""
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is already deleted
        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is already deleted"
            )
        
        # Soft delete: anonymize personal data and mark as deleted
        from datetime import datetime
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        
        # Anonymize personal information
        user.first_name = "Deleted"
        user.last_name = "User"
        user.username = f"deleted_user_{user_id}"
        user.email = f"deleted_user_{user_id}@deleted.local"
        user.phone_number = None
        
        # Clear sensitive data
        user.hashed_password = ""  # Clear password hash
        user.reset_token = None
        user.reset_token_expires_at = None
        
        # Clear consents and preferences
        user.gdpr_consent = False
        user.gdpr_consent_date = None
        user.marketing_consent = False
        user.marketing_consent_date = None
        
        # Deactivate account
        user.is_active = False
        user.is_verified = False
        
        db.commit()