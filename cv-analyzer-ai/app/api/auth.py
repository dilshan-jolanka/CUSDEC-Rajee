"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import secrets
import hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.config.database import get_db
from app.config.settings import get_settings
from app.models.user_model import User
from app.models.api_key_model import APIKey

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    company_name: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class APIKeyCreate(BaseModel):
    key_name: str
    permissions: str = "basic"


class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    key_value: str
    key_prefix: str
    permissions: str
    is_active: bool
    requests_per_minute: int
    requests_per_hour: int
    created_at: datetime


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    company_name: Optional[str]
    account_type: str
    is_active: bool
    total_analyses: int
    created_at: datetime


# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_api_key() -> tuple[str, str]:
    """Generate API key and its prefix"""
    # Generate a secure random API key
    api_key = secrets.token_urlsafe(32)
    key_prefix = api_key[:8]  # First 8 characters for identification
    return api_key, key_prefix


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> APIKey:
    """Verify API key and return associated key object"""
    if not credentials.credentials.startswith("cvai_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    api_key = db.query(APIKey).filter(
        APIKey.key_value == credentials.credentials,
        APIKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    # Update last used timestamp
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    return api_key


# API Endpoints
@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            company_name=user_data.company_name,
            phone=user_data.phone,
            hashed_password=hashed_password,
            is_active=True,
            account_type="basic"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered: {user_data.username}")
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login")
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    try:
        # Verify user credentials
        user = db.query(User).filter(User.username == user_credentials.username).first()
        
        if not user or not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User logged in: {user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the authenticated user"""
    try:
        # Generate API key
        api_key_value, key_prefix = generate_api_key()
        api_key_value = f"cvai_{api_key_value}"  # Add prefix for identification
        
        # Create API key record
        new_api_key = APIKey(
            key_name=key_data.key_name,
            key_value=api_key_value,
            key_prefix=key_prefix,
            user_id=current_user.id,
            permissions=key_data.permissions,
            is_active=True
        )
        
        db.add(new_api_key)
        db.commit()
        db.refresh(new_api_key)
        
        logger.info(f"New API key created for user {current_user.username}: {key_data.key_name}")
        return new_api_key
        
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the authenticated user"""
    try:
        api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
        
        # Return keys without the actual key value for security
        return [
            {
                "id": key.id,
                "key_name": key.key_name,
                "key_prefix": f"cvai_{key.key_prefix}....",
                "permissions": key.permissions,
                "is_active": key.is_active,
                "total_requests": key.total_requests,
                "last_used_at": key.last_used_at,
                "created_at": key.created_at
            }
            for key in api_keys
        ]
        
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    try:
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        db.delete(api_key)
        db.commit()
        
        logger.info(f"API key deleted: {api_key.key_name} by user {current_user.username}")
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@router.put("/api-keys/{key_id}/toggle")
async def toggle_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle API key active status"""
    try:
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        api_key.is_active = not api_key.is_active
        db.commit()
        
        status_text = "activated" if api_key.is_active else "deactivated"
        logger.info(f"API key {status_text}: {api_key.key_name} by user {current_user.username}")
        
        return {
            "message": f"API key {status_text} successfully",
            "is_active": api_key.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling API key: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle API key"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


@router.get("/validate-key")
async def validate_api_key(api_key: APIKey = Depends(verify_api_key)):
    """Validate API key (useful for testing)"""
    return {
        "valid": True,
        "key_name": api_key.key_name,
        "permissions": api_key.permissions,
        "user_id": api_key.user_id,
        "requests_remaining": {
            "per_minute": api_key.requests_per_minute - api_key.requests_this_minute,
            "per_hour": api_key.requests_per_hour - api_key.requests_this_hour,
            "per_day": api_key.requests_per_day - api_key.requests_today
        }
    }