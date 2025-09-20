"""
User database model
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class User(Base):
    """User model for client management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    company_name = Column(String(200), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Account type and permissions
    account_type = Column(String(20), default="basic")  # basic, premium, enterprise
    max_analyses_per_month = Column(Integer, default=100)
    
    # Usage tracking
    total_analyses = Column(Integer, default=0)
    analyses_this_month = Column(Integer, default=0)
    last_analysis_date = Column(DateTime(timezone=True), nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    cv_analyses = relationship("CVAnalysis", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())