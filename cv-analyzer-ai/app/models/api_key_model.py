"""
API Key database model
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class APIKey(Base):
    """API Key model for authentication and rate limiting"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    
    # Key information
    key_name = Column(String(100), nullable=False)
    key_value = Column(String(100), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Associated user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Key status and permissions
    is_active = Column(Boolean, default=True)
    permissions = Column(String(200), default="basic")  # basic, advanced, full
    
    # Rate limiting
    requests_per_minute = Column(Integer, default=100)
    requests_per_hour = Column(Integer, default=1000)
    requests_per_day = Column(Integer, default=10000)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    requests_today = Column(Integer, default=0)
    requests_this_hour = Column(Integer, default=0)
    requests_this_minute = Column(Integer, default=0)
    
    # Last usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_ip_address = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class APIUsage(Base):
    """API usage tracking for analytics"""
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    
    # Request information
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    
    # Request metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    
    # Response information
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    # Error tracking
    error_message = Column(String(500), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    api_key = relationship("APIKey")


class RateLimitLog(Base):
    """Rate limit violations log"""
    __tablename__ = "rate_limit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Request information
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    ip_address = Column(String(50), nullable=False)
    endpoint = Column(String(200), nullable=False)
    
    # Rate limit details
    limit_type = Column(String(20), nullable=False)  # minute, hour, day
    limit_value = Column(Integer, nullable=False)
    current_count = Column(Integer, nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())