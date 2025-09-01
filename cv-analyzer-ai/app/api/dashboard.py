"""
Dashboard API endpoints for analytics and usage statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.config.database import get_db
from app.models.cv_model import CVAnalysis
from app.models.api_key_model import APIKey, APIUsage
from app.models.user_model import User
from app.api.auth import get_current_user, verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


# API Endpoints
@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user dashboard statistics"""
    try:
        # Basic user stats
        total_analyses = db.query(CVAnalysis).filter(CVAnalysis.user_id == current_user.id).count()
        
        # Recent analyses (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_analyses = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.created_at >= thirty_days_ago
        ).count()
        
        # Completed vs failed analyses
        completed_analyses = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.status == "completed"
        ).count()
        
        failed_analyses = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.status == "failed"
        ).count()
        
        # Success rate
        success_rate = (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0
        
        # Average scores
        avg_scores = db.query(
            func.avg(CVAnalysis.overall_score),
            func.avg(CVAnalysis.skill_score),
            func.avg(CVAnalysis.experience_score),
            func.avg(CVAnalysis.education_score),
            func.avg(CVAnalysis.compatibility_percentage)
        ).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.status == "completed"
        ).first()
        
        # API key usage
        api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
        total_api_requests = sum(key.total_requests for key in api_keys)
        
        return {
            "user_info": {
                "username": current_user.username,
                "account_type": current_user.account_type,
                "member_since": current_user.created_at,
                "last_activity": current_user.last_login
            },
            "usage_stats": {
                "total_analyses": total_analyses,
                "recent_analyses_30d": recent_analyses,
                "completed_analyses": completed_analyses,
                "failed_analyses": failed_analyses,
                "success_rate": round(success_rate, 1),
                "total_api_requests": total_api_requests,
                "monthly_limit": current_user.max_analyses_per_month,
                "monthly_usage": current_user.analyses_this_month
            },
            "performance_metrics": {
                "average_overall_score": round(avg_scores[0] or 0, 1),
                "average_skill_score": round(avg_scores[1] or 0, 1),
                "average_experience_score": round(avg_scores[2] or 0, 1),
                "average_education_score": round(avg_scores[3] or 0, 1),
                "average_compatibility": round(avg_scores[4] or 0, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/recent-analyses")
async def get_recent_analyses(
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent CV analyses for the user"""
    try:
        analyses = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id
        ).order_by(desc(CVAnalysis.created_at)).limit(limit).all()
        
        results = []
        for analysis in analyses:
            results.append({
                "analysis_id": analysis.analysis_id,
                "filename": analysis.filename,
                "status": analysis.status,
                "candidate_name": analysis.full_name,
                "overall_score": analysis.overall_score,
                "compatibility_percentage": analysis.compatibility_percentage,
                "created_at": analysis.created_at
            })
        
        return {
            "recent_analyses": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent analyses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent analyses"
        )


@router.get("/analytics")
async def get_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for the specified period"""
    try:
        # Calculate date range
        period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        start_date = datetime.utcnow() - timedelta(days=period_days[period])
        
        # Analyses over time
        daily_analyses = db.query(
            func.date(CVAnalysis.created_at).label('date'),
            func.count(CVAnalysis.id).label('count')
        ).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.created_at >= start_date
        ).group_by(func.date(CVAnalysis.created_at)).all()
        
        # Score distribution
        score_ranges = [
            (90, 100, "Excellent"),
            (80, 89, "Very Good"),
            (70, 79, "Good"),
            (60, 69, "Fair"),
            (0, 59, "Poor")
        ]
        
        score_distribution = {}
        for min_score, max_score, label in score_ranges:
            count = db.query(CVAnalysis).filter(
                CVAnalysis.user_id == current_user.id,
                CVAnalysis.overall_score.between(min_score, max_score),
                CVAnalysis.created_at >= start_date
            ).count()
            score_distribution[label] = count
        
        # Top skills found
        all_analyses = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.technical_skills.isnot(None),
            CVAnalysis.created_at >= start_date
        ).all()
        
        skill_counts = {}
        for analysis in all_analyses:
            if analysis.technical_skills:
                for skill in analysis.technical_skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Experience distribution
        experience_ranges = [
            (0, 1, "0-1 years"),
            (1, 3, "1-3 years"), 
            (3, 5, "3-5 years"),
            (5, 10, "5-10 years"),
            (10, 999, "10+ years")
        ]
        
        experience_distribution = {}
        for min_exp, max_exp, label in experience_ranges:
            count = db.query(CVAnalysis).filter(
                CVAnalysis.user_id == current_user.id,
                CVAnalysis.total_experience_years.between(min_exp, max_exp),
                CVAnalysis.created_at >= start_date
            ).count()
            experience_distribution[label] = count
        
        return {
            "period": period,
            "date_range": {
                "start_date": start_date,
                "end_date": datetime.utcnow()
            },
            "daily_analyses": [
                {"date": str(date), "count": count} 
                for date, count in daily_analyses
            ],
            "score_distribution": score_distribution,
            "top_skills": [
                {"skill": skill, "count": count}
                for skill, count in top_skills
            ],
            "experience_distribution": experience_distribution
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/api-usage")
async def get_api_usage(
    api_key_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API usage statistics"""
    try:
        # Get user's API keys
        query = db.query(APIKey).filter(APIKey.user_id == current_user.id)
        if api_key_id:
            query = query.filter(APIKey.id == api_key_id)
        
        api_keys = query.all()
        
        if not api_keys:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        usage_stats = []
        for key in api_keys:
            # Get recent usage for this key
            recent_usage = db.query(APIUsage).filter(
                APIUsage.api_key_id == key.id,
                APIUsage.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            # Calculate usage metrics
            total_requests_30d = len(recent_usage)
            avg_response_time = sum(u.response_time_ms for u in recent_usage if u.response_time_ms) / max(1, len(recent_usage))
            error_rate = sum(1 for u in recent_usage if u.status_code >= 400) / max(1, len(recent_usage)) * 100
            
            # Endpoint usage
            endpoint_usage = {}
            for usage in recent_usage:
                endpoint_usage[usage.endpoint] = endpoint_usage.get(usage.endpoint, 0) + 1
            
            usage_stats.append({
                "api_key": {
                    "id": key.id,
                    "name": key.key_name,
                    "prefix": f"cvai_{key.key_prefix}....",
                    "permissions": key.permissions,
                    "is_active": key.is_active
                },
                "usage_metrics": {
                    "total_requests": key.total_requests,
                    "requests_30d": total_requests_30d,
                    "requests_today": key.requests_today,
                    "requests_this_hour": key.requests_this_hour,
                    "last_used": key.last_used_at
                },
                "performance_metrics": {
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "error_rate_percent": round(error_rate, 2)
                },
                "rate_limits": {
                    "per_minute": {
                        "limit": key.requests_per_minute,
                        "current": key.requests_this_minute
                    },
                    "per_hour": {
                        "limit": key.requests_per_hour,
                        "current": key.requests_this_hour
                    },
                    "per_day": {
                        "limit": key.requests_per_day,
                        "current": key.requests_today
                    }
                },
                "endpoint_usage": endpoint_usage
            })
        
        return {
            "api_usage": usage_stats,
            "summary": {
                "total_keys": len(api_keys),
                "active_keys": sum(1 for key in api_keys if key.is_active),
                "total_requests": sum(key.total_requests for key in api_keys)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API usage statistics"
        )


@router.get("/top-performers")
async def get_top_performers(
    metric: str = Query("overall_score", regex="^(overall_score|compatibility_percentage|skill_score)$"),
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top performing CVs based on specified metric"""
    try:
        # Map metric to column
        metric_column = getattr(CVAnalysis, metric)
        
        # Get top performers
        top_cvs = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.status == "completed",
            metric_column.isnot(None)
        ).order_by(desc(metric_column)).limit(limit).all()
        
        results = []
        for cv in top_cvs:
            results.append({
                "analysis_id": cv.analysis_id,
                "filename": cv.filename,
                "candidate_name": cv.full_name,
                "email": cv.email,
                "metric_value": getattr(cv, metric),
                "overall_score": cv.overall_score,
                "compatibility_percentage": cv.compatibility_percentage,
                "total_experience_years": cv.total_experience_years,
                "top_skills": (cv.technical_skills or [])[:5],
                "created_at": cv.created_at
            })
        
        return {
            "metric": metric,
            "top_performers": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting top performers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top performers"
        )


@router.get("/skill-insights")
async def get_skill_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get insights about skills across all analyzed CVs"""
    try:
        # Get all completed analyses
        analyses = db.query(CVAnalysis).filter(
            CVAnalysis.user_id == current_user.id,
            CVAnalysis.status == "completed",
            CVAnalysis.technical_skills.isnot(None)
        ).all()
        
        if not analyses:
            return {
                "message": "No completed analyses found",
                "skill_insights": {}
            }
        
        # Aggregate skill data
        all_skills = {}
        skill_categories = {}
        experience_by_skill = {}
        
        for analysis in analyses:
            # Count skills
            if analysis.technical_skills:
                for skill in analysis.technical_skills:
                    all_skills[skill] = all_skills.get(skill, 0) + 1
                    
                    # Track experience levels for each skill
                    if skill not in experience_by_skill:
                        experience_by_skill[skill] = []
                    if analysis.total_experience_years:
                        experience_by_skill[skill].append(analysis.total_experience_years)
            
            # Count skill categories
            if analysis.skill_categories:
                for category, skills in analysis.skill_categories.items():
                    if skills:
                        skill_categories[category] = skill_categories.get(category, 0) + len(skills)
        
        # Get most common skills
        most_common_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Calculate average experience by skill (for skills that appear frequently)
        skill_experience_avg = {}
        for skill, experiences in experience_by_skill.items():
            if len(experiences) >= 3:  # Only for skills with at least 3 data points
                skill_experience_avg[skill] = sum(experiences) / len(experiences)
        
        # Most valuable skills (high experience + high frequency)
        valuable_skills = []
        for skill, count in most_common_skills[:15]:
            if skill in skill_experience_avg:
                value_score = count * skill_experience_avg[skill]
                valuable_skills.append({
                    "skill": skill,
                    "frequency": count,
                    "avg_experience": round(skill_experience_avg[skill], 1),
                    "value_score": round(value_score, 1)
                })
        
        valuable_skills.sort(key=lambda x: x["value_score"], reverse=True)
        
        return {
            "total_analyses": len(analyses),
            "unique_skills_found": len(all_skills),
            "most_common_skills": [
                {"skill": skill, "count": count, "percentage": round(count/len(analyses)*100, 1)}
                for skill, count in most_common_skills
            ],
            "skill_categories": [
                {"category": cat, "total_mentions": count}
                for cat, count in sorted(skill_categories.items(), key=lambda x: x[1], reverse=True)
            ],
            "most_valuable_skills": valuable_skills[:10],
            "skill_insights": {
                "avg_skills_per_cv": round(sum(len(analysis.technical_skills or []) for analysis in analyses) / len(analyses), 1),
                "most_experienced_candidates": [
                    {
                        "candidate": analysis.full_name or analysis.filename,
                        "experience_years": analysis.total_experience_years,
                        "skill_count": len(analysis.technical_skills or [])
                    }
                    for analysis in sorted(analyses, key=lambda x: x.total_experience_years or 0, reverse=True)[:5]
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting skill insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill insights"
        )