"""
CV Analyzer API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import uuid
import asyncio
from datetime import datetime
import logging
import os
import aiofiles

from app.config.database import get_db
from app.config.settings import get_settings
from app.models.cv_model import CVAnalysis
from app.models.api_key_model import APIKey
from app.api.auth import verify_api_key
from app.services.cv_parser import CVParser
from app.services.ml_analyzer import MLAnalyzer
from app.services.skill_matcher import SkillMatcher
from app.services.scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Initialize services
cv_parser = CVParser()
ml_analyzer = MLAnalyzer()
skill_matcher = SkillMatcher()
scoring_engine = ScoringEngine()


# Pydantic models for request/response
class JobRequirements(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    minimum_experience: int = 0
    education_requirements: List[str] = Field(default_factory=list)
    job_description: Optional[str] = None


class CVAnalysisRequest(BaseModel):
    job_requirements: Optional[JobRequirements] = None
    analysis_options: Optional[Dict[str, bool]] = Field(default_factory=lambda: {
        "include_skills_analysis": True,
        "include_experience_analysis": True,
        "include_education_analysis": True,
        "include_job_matching": False,
        "include_scoring": True
    })


class BatchAnalysisRequest(BaseModel):
    job_requirements: Optional[JobRequirements] = None
    analysis_options: Optional[Dict[str, bool]] = Field(default_factory=lambda: {
        "include_skills_analysis": True,
        "include_experience_analysis": True,
        "include_education_analysis": True,
        "include_job_matching": False,
        "include_scoring": True
    })


class CVAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    filename: str
    
    # Extracted information
    personal_info: Optional[Dict[str, Any]] = None
    skills_analysis: Optional[Dict[str, Any]] = None
    experience_analysis: Optional[Dict[str, Any]] = None
    education_analysis: Optional[Dict[str, Any]] = None
    
    # Scoring and matching
    overall_score: Optional[Dict[str, Any]] = None
    job_compatibility: Optional[Dict[str, Any]] = None
    
    # Metadata
    processing_time_seconds: Optional[float] = None
    created_at: datetime
    

class BatchAnalysisResponse(BaseModel):
    batch_id: str
    total_files: int
    completed: int
    failed: int
    results: List[CVAnalysisResponse]
    processing_time_seconds: float


# Utility functions
async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return file path"""
    # Create uploads directory if it doesn't exist
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return file_path


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file size
    if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )


async def perform_cv_analysis(file_content: bytes, filename: str, 
                            analysis_options: Dict[str, bool],
                            job_requirements: Optional[JobRequirements] = None) -> Dict[str, Any]:
    """Perform complete CV analysis"""
    start_time = datetime.now()
    
    try:
        # Step 1: Parse CV content
        logger.info(f"Starting CV parsing for {filename}")
        parsed_cv = await cv_parser.parse_cv(file_content, filename)
        
        # Step 2: ML Analysis
        ml_analysis = {}
        if analysis_options.get("include_skills_analysis", True) or \
           analysis_options.get("include_experience_analysis", True) or \
           analysis_options.get("include_education_analysis", True):
            logger.info(f"Starting ML analysis for {filename}")
            ml_analysis = await ml_analyzer.analyze_cv_content(parsed_cv)
        
        # Step 3: Job Matching (if requested and job requirements provided)
        job_compatibility = {}
        if analysis_options.get("include_job_matching", False) and job_requirements:
            logger.info(f"Starting job matching for {filename}")
            cv_skills = ml_analysis.get("skills_analysis", {})
            job_requirements_dict = job_requirements.dict()
            
            # Skill matching
            skill_results = await skill_matcher.match_skills(cv_skills, job_requirements_dict)
            
            # Overall job compatibility
            job_compatibility = await skill_matcher.calculate_job_compatibility(
                ml_analysis, job_requirements.job_description or ""
            )
            job_compatibility["skill_matching"] = skill_results
        
        # Step 4: Scoring (if requested)
        overall_scoring = {}
        if analysis_options.get("include_scoring", True):
            logger.info(f"Starting scoring for {filename}")
            job_req_dict = job_requirements.dict() if job_requirements else None
            overall_scoring = await scoring_engine.calculate_overall_score(
                ml_analysis, job_req_dict
            )
            
            # Calculate compatibility percentage if job requirements provided
            if job_compatibility:
                compatibility_results = await scoring_engine.calculate_compatibility_percentage(
                    ml_analysis, job_compatibility
                )
                overall_scoring["compatibility"] = compatibility_results
        
        # Compile results
        processing_time = (datetime.now() - start_time).total_seconds()
        
        results = {
            "filename": filename,
            "file_info": {
                "file_type": parsed_cv.get("file_type"),
                "file_size": len(file_content),
                "total_pages": parsed_cv.get("total_pages", 0)
            },
            "personal_info": parsed_cv.get("contact_info", {}),
            "raw_text_preview": parsed_cv.get("raw_text", "")[:500] + "..." if parsed_cv.get("raw_text", "") else "",
            "structured_sections": parsed_cv.get("structured_sections", {}),
            "processing_time_seconds": round(processing_time, 2)
        }
        
        # Add optional analysis results
        if analysis_options.get("include_skills_analysis", True):
            results["skills_analysis"] = ml_analysis.get("skills_analysis", {})
        
        if analysis_options.get("include_experience_analysis", True):
            results["experience_analysis"] = ml_analysis.get("experience_analysis", {})
        
        if analysis_options.get("include_education_analysis", True):
            results["education_analysis"] = ml_analysis.get("education_analysis", {})
        
        if analysis_options.get("include_scoring", True):
            results["overall_score"] = overall_scoring
        
        if analysis_options.get("include_job_matching", False) and job_requirements:
            results["job_compatibility"] = job_compatibility
        
        # Add additional ML analysis results
        results["text_quality"] = ml_analysis.get("text_quality", {})
        results["language_analysis"] = ml_analysis.get("language_analysis", {})
        results["sentiment_analysis"] = ml_analysis.get("sentiment_analysis", {})
        results["named_entities"] = ml_analysis.get("named_entities", {})
        
        logger.info(f"CV analysis completed for {filename} in {processing_time:.2f} seconds")
        return results
        
    except Exception as e:
        logger.error(f"Error in CV analysis for {filename}: {str(e)}")
        raise


# API Endpoints
@router.post("/analyze-cv", response_model=CVAnalysisResponse)
async def analyze_cv(
    file: UploadFile = File(...),
    job_requirements: Optional[str] = Form(None),
    analysis_options: Optional[str] = Form(None),
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Analyze a single CV file
    
    Upload a CV file (PDF/DOCX) and get comprehensive analysis including:
    - Personal information extraction
    - Skills analysis and categorization
    - Experience analysis and scoring
    - Education background assessment
    - Overall scoring and recommendations
    - Optional job matching (if job requirements provided)
    """
    try:
        # Validate file
        validate_file(file)
        
        # Parse optional parameters
        job_req = None
        if job_requirements:
            try:
                import json
                job_req_data = json.loads(job_requirements)
                job_req = JobRequirements(**job_req_data)
            except Exception as e:
                logger.warning(f"Invalid job requirements format: {e}")
        
        analysis_opts = {
            "include_skills_analysis": True,
            "include_experience_analysis": True,
            "include_education_analysis": True,
            "include_job_matching": job_req is not None,
            "include_scoring": True
        }
        if analysis_options:
            try:
                import json
                opts_data = json.loads(analysis_options)
                analysis_opts.update(opts_data)
            except Exception as e:
                logger.warning(f"Invalid analysis options format: {e}")
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Read file content
        file_content = await file.read()
        
        # Save CV analysis record to database
        cv_analysis = CVAnalysis(
            analysis_id=analysis_id,
            filename=file.filename,
            file_size=len(file_content),
            file_type=os.path.splitext(file.filename)[1].lower(),
            status="processing",
            user_id=api_key.user_id
        )
        
        db.add(cv_analysis)
        db.commit()
        
        try:
            # Perform analysis
            analysis_results = await perform_cv_analysis(
                file_content, file.filename, analysis_opts, job_req
            )
            
            # Update database record with results
            cv_analysis.status = "completed"
            cv_analysis.full_name = analysis_results.get("personal_info", {}).get("name")
            cv_analysis.email = analysis_results.get("personal_info", {}).get("email")
            cv_analysis.phone = analysis_results.get("personal_info", {}).get("phone")
            cv_analysis.location = analysis_results.get("personal_info", {}).get("location")
            cv_analysis.raw_text = analysis_results.get("raw_text_preview")
            cv_analysis.structured_data = analysis_results.get("structured_sections")
            cv_analysis.technical_skills = analysis_results.get("skills_analysis", {}).get("technical_skills")
            cv_analysis.soft_skills = analysis_results.get("skills_analysis", {}).get("soft_skills")
            cv_analysis.skill_categories = analysis_results.get("skills_analysis", {}).get("skill_categories")
            cv_analysis.total_experience_years = analysis_results.get("experience_analysis", {}).get("total_years")
            cv_analysis.experience_details = analysis_results.get("experience_analysis")
            cv_analysis.education_details = analysis_results.get("education_analysis")
            
            # Overall scores
            overall_score = analysis_results.get("overall_score", {})
            cv_analysis.overall_score = overall_score.get("overall_score")
            cv_analysis.skill_score = overall_score.get("component_scores", {}).get("skills")
            cv_analysis.experience_score = overall_score.get("component_scores", {}).get("experience")
            cv_analysis.education_score = overall_score.get("component_scores", {}).get("education")
            
            # Job matching results
            if analysis_results.get("job_compatibility"):
                cv_analysis.job_match_results = analysis_results["job_compatibility"]
                cv_analysis.compatibility_percentage = analysis_results["job_compatibility"].get("overall_compatibility")
                cv_analysis.missing_skills = analysis_results["job_compatibility"].get("skill_matching", {}).get("missing_skills")
                cv_analysis.recommendations = analysis_results["job_compatibility"].get("recommendations")
            
            db.commit()
            
            # Update API usage
            api_key.total_requests += 1
            api_key.requests_today += 1
            api_key.requests_this_hour += 1
            api_key.requests_this_minute += 1
            db.commit()
            
            # Prepare response
            response = CVAnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                filename=file.filename,
                personal_info=analysis_results.get("personal_info"),
                skills_analysis=analysis_results.get("skills_analysis"),
                experience_analysis=analysis_results.get("experience_analysis"),
                education_analysis=analysis_results.get("education_analysis"),
                overall_score=analysis_results.get("overall_score"),
                job_compatibility=analysis_results.get("job_compatibility"),
                processing_time_seconds=analysis_results.get("processing_time_seconds"),
                created_at=cv_analysis.created_at
            )
            
            return response
            
        except Exception as e:
            # Update status to failed
            cv_analysis.status = "failed"
            db.commit()
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV analysis failed: {str(e)}"
        )


@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_cvs(
    files: List[UploadFile] = File(...),
    job_requirements: Optional[str] = Form(None),
    analysis_options: Optional[str] = Form(None),
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Analyze multiple CV files in batch
    
    Upload multiple CV files and get analysis for each file.
    Useful for processing multiple candidates at once.
    """
    try:
        if len(files) > 50:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 files allowed in batch processing"
            )
        
        # Parse parameters
        job_req = None
        if job_requirements:
            try:
                import json
                job_req_data = json.loads(job_requirements)
                job_req = JobRequirements(**job_req_data)
            except Exception as e:
                logger.warning(f"Invalid job requirements format: {e}")
        
        analysis_opts = {
            "include_skills_analysis": True,
            "include_experience_analysis": True,
            "include_education_analysis": True,
            "include_job_matching": job_req is not None,
            "include_scoring": True
        }
        if analysis_options:
            try:
                import json
                opts_data = json.loads(analysis_options)
                analysis_opts.update(opts_data)
            except Exception as e:
                logger.warning(f"Invalid analysis options format: {e}")
        
        batch_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        results = []
        completed = 0
        failed = 0
        
        # Process each file
        for file in files:
            try:
                validate_file(file)
                file_content = await file.read()
                
                # Generate analysis ID for this file
                analysis_id = str(uuid.uuid4())
                
                # Create database record
                cv_analysis = CVAnalysis(
                    analysis_id=analysis_id,
                    filename=file.filename,
                    file_size=len(file_content),
                    file_type=os.path.splitext(file.filename)[1].lower(),
                    status="processing",
                    user_id=api_key.user_id
                )
                db.add(cv_analysis)
                db.commit()
                
                try:
                    # Perform analysis
                    analysis_results = await perform_cv_analysis(
                        file_content, file.filename, analysis_opts, job_req
                    )
                    
                    # Update database record
                    cv_analysis.status = "completed"
                    cv_analysis.full_name = analysis_results.get("personal_info", {}).get("name")
                    cv_analysis.email = analysis_results.get("personal_info", {}).get("email")
                    cv_analysis.structured_data = analysis_results.get("structured_sections")
                    cv_analysis.technical_skills = analysis_results.get("skills_analysis", {}).get("technical_skills")
                    cv_analysis.total_experience_years = analysis_results.get("experience_analysis", {}).get("total_years")
                    
                    overall_score = analysis_results.get("overall_score", {})
                    cv_analysis.overall_score = overall_score.get("overall_score")
                    
                    if analysis_results.get("job_compatibility"):
                        cv_analysis.compatibility_percentage = analysis_results["job_compatibility"].get("overall_compatibility")
                    
                    db.commit()
                    
                    # Add to results
                    results.append(CVAnalysisResponse(
                        analysis_id=analysis_id,
                        status="completed",
                        filename=file.filename,
                        personal_info=analysis_results.get("personal_info"),
                        skills_analysis=analysis_results.get("skills_analysis"),
                        experience_analysis=analysis_results.get("experience_analysis"),
                        education_analysis=analysis_results.get("education_analysis"),
                        overall_score=analysis_results.get("overall_score"),
                        job_compatibility=analysis_results.get("job_compatibility"),
                        processing_time_seconds=analysis_results.get("processing_time_seconds"),
                        created_at=cv_analysis.created_at
                    ))
                    
                    completed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    cv_analysis.status = "failed"
                    db.commit()
                    
                    results.append(CVAnalysisResponse(
                        analysis_id=analysis_id,
                        status="failed",
                        filename=file.filename,
                        created_at=cv_analysis.created_at
                    ))
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error validating file {file.filename}: {str(e)}")
                failed += 1
                continue
        
        # Update API usage
        api_key.total_requests += len(files)
        api_key.requests_today += len(files)
        api_key.requests_this_hour += len(files)
        db.commit()
        
        total_processing_time = (datetime.now() - start_time).total_seconds()
        
        return BatchAnalysisResponse(
            batch_id=batch_id,
            total_files=len(files),
            completed=completed,
            failed=failed,
            results=results,
            processing_time_seconds=round(total_processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get analysis results by analysis ID"""
    try:
        cv_analysis = db.query(CVAnalysis).filter(
            CVAnalysis.analysis_id == analysis_id,
            CVAnalysis.user_id == api_key.user_id
        ).first()
        
        if not cv_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return {
            "analysis_id": cv_analysis.analysis_id,
            "status": cv_analysis.status,
            "filename": cv_analysis.filename,
            "personal_info": {
                "name": cv_analysis.full_name,
                "email": cv_analysis.email,
                "phone": cv_analysis.phone,
                "location": cv_analysis.location
            },
            "skills": {
                "technical_skills": cv_analysis.technical_skills,
                "soft_skills": cv_analysis.soft_skills,
                "skill_categories": cv_analysis.skill_categories
            },
            "experience": {
                "total_years": cv_analysis.total_experience_years,
                "details": cv_analysis.experience_details
            },
            "education": cv_analysis.education_details,
            "scores": {
                "overall_score": cv_analysis.overall_score,
                "skill_score": cv_analysis.skill_score,
                "experience_score": cv_analysis.experience_score,
                "education_score": cv_analysis.education_score,
                "compatibility_percentage": cv_analysis.compatibility_percentage
            },
            "job_matching": {
                "results": cv_analysis.job_match_results,
                "missing_skills": cv_analysis.missing_skills,
                "recommendations": cv_analysis.recommendations
            },
            "metadata": {
                "file_size": cv_analysis.file_size,
                "file_type": cv_analysis.file_type,
                "created_at": cv_analysis.created_at,
                "updated_at": cv_analysis.updated_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis results"
        )


@router.post("/match-job")
async def match_cv_against_job(
    analysis_id: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form(...),
    preferred_skills: Optional[str] = Form(None),
    minimum_experience: int = Form(0),
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Match an existing CV analysis against a specific job description
    
    Requires an existing analysis_id from a previous CV analysis.
    Performs job matching and compatibility assessment.
    """
    try:
        # Get existing CV analysis
        cv_analysis = db.query(CVAnalysis).filter(
            CVAnalysis.analysis_id == analysis_id,
            CVAnalysis.user_id == api_key.user_id,
            CVAnalysis.status == "completed"
        ).first()
        
        if not cv_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Completed CV analysis not found"
            )
        
        # Parse job requirements
        try:
            import json
            required_skills_list = json.loads(required_skills) if required_skills else []
            preferred_skills_list = json.loads(preferred_skills) if preferred_skills else []
        except:
            required_skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
            preferred_skills_list = [s.strip() for s in (preferred_skills or "").split(",") if s.strip()]
        
        job_requirements = {
            "required_skills": required_skills_list,
            "preferred_skills": preferred_skills_list,
            "minimum_experience": minimum_experience,
            "job_description": job_description
        }
        
        # Reconstruct CV analysis data for skill matching
        cv_analysis_data = {
            "skills_analysis": {
                "technical_skills": cv_analysis.technical_skills or [],
                "soft_skills": cv_analysis.soft_skills or [],
                "skill_categories": cv_analysis.skill_categories or {}
            },
            "experience_analysis": {
                "total_years": cv_analysis.total_experience_years or 0,
                "experience_details": cv_analysis.experience_details or {}
            },
            "education_analysis": cv_analysis.education_details or {}
        }
        
        # Perform job matching
        cv_skills = cv_analysis_data["skills_analysis"]
        skill_results = await skill_matcher.match_skills(cv_skills, job_requirements)
        
        # Calculate job compatibility
        job_compatibility = await skill_matcher.calculate_job_compatibility(
            cv_analysis_data, job_description
        )
        job_compatibility["skill_matching"] = skill_results
        
        # Calculate compatibility percentage
        compatibility_results = await scoring_engine.calculate_compatibility_percentage(
            cv_analysis_data, job_compatibility
        )
        
        # Update database with job matching results
        cv_analysis.job_match_results = job_compatibility
        cv_analysis.compatibility_percentage = compatibility_results["compatibility_percentage"]
        cv_analysis.missing_skills = skill_results.get("missing_skills")
        cv_analysis.recommendations = job_compatibility.get("recommendations")
        db.commit()
        
        # Update API usage
        api_key.total_requests += 1
        api_key.requests_today += 1
        db.commit()
        
        return {
            "analysis_id": analysis_id,
            "job_matching_results": {
                "compatibility_percentage": compatibility_results["compatibility_percentage"],
                "match_level": compatibility_results["match_level"],
                "skill_matching": skill_results,
                "job_compatibility": job_compatibility,
                "detailed_compatibility": compatibility_results
            },
            "summary": {
                "overall_match": compatibility_results["match_level"],
                "key_strengths": job_compatibility.get("strengths", [])[:3],
                "main_gaps": job_compatibility.get("weaknesses", [])[:3],
                "recommendations": job_compatibility.get("recommendations", [])[:5]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in job matching: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job matching failed: {str(e)}"
        )