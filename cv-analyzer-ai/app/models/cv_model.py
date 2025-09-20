"""
CV Analysis database model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class CVAnalysis(Base):
    """CV Analysis results model"""
    __tablename__ = "cv_analyses"

    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(10), nullable=False)
    
    # Analysis metadata
    analysis_id = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(20), default="processing")  # processing, completed, failed
    
    # Extracted personal information
    full_name = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(200), nullable=True)
    
    # Extracted content
    raw_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    
    # Skills analysis
    technical_skills = Column(JSON, nullable=True)  # List of technical skills
    soft_skills = Column(JSON, nullable=True)  # List of soft skills
    skill_categories = Column(JSON, nullable=True)  # Categorized skills
    
    # Experience analysis
    total_experience_years = Column(Float, nullable=True)
    experience_details = Column(JSON, nullable=True)  # Work history
    education_details = Column(JSON, nullable=True)  # Education history
    
    # Scoring
    overall_score = Column(Float, nullable=True)
    skill_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    
    # Job matching
    job_match_results = Column(JSON, nullable=True)
    compatibility_percentage = Column(Float, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="cv_analyses")


class CVTemplate(Base):
    """CV Template for scoring standards"""
    __tablename__ = "cv_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template criteria
    required_skills = Column(JSON, nullable=False)  # Required skills list
    preferred_skills = Column(JSON, nullable=True)  # Preferred skills list
    minimum_experience = Column(Float, default=0.0)  # Minimum years of experience
    education_requirements = Column(JSON, nullable=True)  # Education criteria
    
    # Scoring weights
    skill_weight = Column(Float, default=0.4)
    experience_weight = Column(Float, default=0.3)
    education_weight = Column(Float, default=0.2)
    other_weight = Column(Float, default=0.1)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())