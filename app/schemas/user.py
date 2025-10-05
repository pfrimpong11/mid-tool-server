from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


# Shared properties
class UserBase(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip().title()
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.strip().lower()


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str
    confirm_password: str
    gdpr_consent: bool
    marketing_consent: Optional[bool] = False
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


# Properties to receive via API on update
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None


# Settings-related schemas
class UserSettingsUpdate(BaseModel):
    # Profile settings
    role: Optional[str] = None
    institution: Optional[str] = None
    
    # Preferences
    dark_mode: Optional[bool] = None
    interface_scale: Optional[str] = None
    default_analysis_model: Optional[str] = None
    
    # Notification settings
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    analysis_notifications: Optional[bool] = None
    report_notifications: Optional[bool] = None
    
    # Privacy settings
    data_retention_period: Optional[str] = None
    anonymous_analytics: Optional[bool] = None
    data_sharing: Optional[bool] = None


class UserSettings(BaseModel):
    # Profile settings
    role: Optional[str]
    institution: Optional[str]
    
    # Preferences
    dark_mode: bool
    interface_scale: str
    default_analysis_model: str
    
    # Notification settings
    email_notifications: bool
    push_notifications: bool
    analysis_notifications: bool
    report_notifications: bool
    
    # Privacy settings
    data_retention_period: str
    anonymous_analytics: bool
    data_sharing: bool


# Account deletion schema
class AccountDeletion(BaseModel):
    password: str
    confirm_deletion: bool = False  # User must explicitly confirm
    
    @validator('password')
    def validate_password(cls, v):
        if not v or not v.strip():
            raise ValueError('Password is required for account deletion')
        return v


# Properties to return via API
class User(UserBase):
    id: int
    phone_number: Optional[str]
    is_active: bool
    is_verified: bool
    gdpr_consent: bool
    gdpr_consent_date: Optional[datetime]
    marketing_consent: bool
    marketing_consent_date: Optional[datetime]
    # Profile settings
    role: Optional[str]
    institution: Optional[str]
    # Preferences
    dark_mode: bool
    interface_scale: str
    default_analysis_model: str
    # Notification settings
    email_notifications: bool
    push_notifications: bool
    analysis_notifications: bool
    report_notifications: bool
    # Privacy settings
    data_retention_period: str
    anonymous_analytics: bool
    data_sharing: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Additional schemas for authentication
class UserLogin(BaseModel):
    username_or_email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v