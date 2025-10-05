from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import (
    UserCreate,
    UserLogin,
    User,
    Token,
    PasswordReset,
    PasswordResetConfirm,
    ChangePassword,
    UserSettingsUpdate,
    UserSettings,
    UserUpdate,
    AccountDeletion
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    try:
        user = AuthService.create_user(db, user_create)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """
    User login endpoint
    """
    user = AuthService.authenticate_user(
        db, 
        user_login.username_or_email, 
        user_login.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    tokens = AuthService.create_tokens(user.id)
    return tokens


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return current_user


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset process
    """
    try:
        reset_token = AuthService.initiate_password_reset(db, password_reset.email)
        
        # In a real application, you would send this token via email
        # For now, we'll return it in the response (NOT recommended for production)
        return {
            "message": "Password reset instructions sent to your email",
            "reset_token": reset_token  # Remove this in production
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate password reset"
        )


@router.post("/reset-password")
async def reset_password(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token
    """
    try:
        user = AuthService.reset_password(
            db,
            password_reset_confirm.token,
            password_reset_confirm.new_password
        )
        
        return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/change-password")
async def change_password(
    password_change: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password (requires authentication)
    """
    try:
        user = AuthService.change_password(
            db,
            current_user,
            password_change.current_password,
            password_change.new_password
        )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    # In a real application, you would get the refresh token from request
    # For now, we'll implement a simple refresh endpoint
    current_user: User = Depends(get_current_active_user)
):
    """
    Refresh access token
    """
    tokens = AuthService.create_tokens(current_user.id)
    return tokens


@router.get("/check-username/{username}")
async def check_username_availability(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Check if a username is available for registration
    """
    try:
        # Validate username format first
        if not username or not username.strip():
            return {"available": False, "message": "Username cannot be empty"}
        
        if len(username.strip()) < 3:
            return {"available": False, "message": "Username must be at least 3 characters long"}
        
        if not username.replace('_', '').replace('-', '').isalnum():
            return {"available": False, "message": "Username can only contain letters, numbers, underscores, and hyphens"}
        
        # Check if username already exists (including deleted users)
        existing_user = AuthService.get_user_by_username(db, username.strip().lower(), include_deleted=True)
        if existing_user:
            return {"available": False, "message": "Username is already taken"}
        
        return {"available": True, "message": "Username is available"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check username availability"
        )


@router.get("/settings", response_model=UserSettings)
async def get_user_settings(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user settings
    """
    return UserSettings(
        role=current_user.role,
        institution=current_user.institution,
        dark_mode=current_user.dark_mode,
        interface_scale=current_user.interface_scale,
        default_analysis_model=current_user.default_analysis_model,
        email_notifications=current_user.email_notifications,
        push_notifications=current_user.push_notifications,
        analysis_notifications=current_user.analysis_notifications,
        report_notifications=current_user.report_notifications,
        data_retention_period=current_user.data_retention_period,
        anonymous_analytics=current_user.anonymous_analytics,
        data_sharing=current_user.data_sharing
    )


@router.put("/settings", response_model=UserSettings)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user settings
    """
    try:
        updated_user = AuthService.update_user_settings(db, current_user.id, settings_update)
        return UserSettings(
            role=updated_user.role,
            institution=updated_user.institution,
            dark_mode=updated_user.dark_mode,
            interface_scale=updated_user.interface_scale,
            default_analysis_model=updated_user.default_analysis_model,
            email_notifications=updated_user.email_notifications,
            push_notifications=updated_user.push_notifications,
            analysis_notifications=updated_user.analysis_notifications,
            report_notifications=updated_user.report_notifications,
            data_retention_period=updated_user.data_retention_period,
            anonymous_analytics=updated_user.anonymous_analytics,
            data_sharing=updated_user.data_sharing
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )


@router.put("/profile", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    """
    try:
        updated_user = AuthService.update_user_profile(db, current_user.id, user_update)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.delete("/account")
async def delete_user_account(
    deletion_data: AccountDeletion,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete user account - mark as deleted and anonymize personal data
    """
    try:
        # Validate that user confirmed deletion
        if not deletion_data.confirm_deletion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account deletion must be explicitly confirmed"
            )
        
        # Authenticate user with password before deletion
        user = AuthService.authenticate_user(db, current_user.username, deletion_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Account deletion requires password confirmation."
            )
        
        # Delete the user account
        AuthService.delete_user_account(db, current_user.id)
        
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )