"""
Experience Scoring ML Model
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple, Any
import re
import logging

logger = logging.getLogger(__name__)


class ExperienceScorer:
    """ML model for scoring work experience quality and relevance"""
    
    def __init__(self):
        """Initialize experience scorer"""
        self.model = None
        self.experience_keywords = self._initialize_experience_keywords()
        self.achievement_keywords = self._initialize_achievement_keywords()
        self.responsibility_keywords = self._initialize_responsibility_keywords()
        
    def _initialize_experience_keywords(self) -> Dict[str, float]:
        """Initialize experience-related keywords with weights"""
        return {
            # Leadership keywords (high weight)
            "led": 3.0,
            "managed": 3.0,
            "supervised": 3.0,
            "directed": 3.0,
            "coordinated": 2.5,
            "mentored": 2.5,
            "guided": 2.0,
            
            # Development keywords (medium-high weight)
            "developed": 2.5,
            "created": 2.5,
            "built": 2.5,
            "designed": 2.5,
            "implemented": 2.5,
            "architected": 3.0,
            "engineered": 2.5,
            
            # Improvement keywords (high weight)
            "improved": 3.0,
            "optimized": 3.0,
            "enhanced": 2.5,
            "streamlined": 2.5,
            "automated": 3.0,
            "reduced": 2.0,
            "increased": 2.5,
            
            # Collaboration keywords (medium weight)
            "collaborated": 2.0,
            "worked": 1.5,
            "partnered": 2.0,
            "contributed": 1.5,
            "participated": 1.0,
            
            # Technical keywords (medium weight)
            "deployed": 2.0,
            "maintained": 1.5,
            "tested": 1.5,
            "debugged": 1.5,
            "integrated": 2.0,
            "migrated": 2.0,
            "configured": 1.5,
            
            # Project keywords (medium weight)
            "delivered": 2.0,
            "completed": 1.5,
            "launched": 2.0,
            "executed": 2.0,
            "planned": 1.5
        }
    
    def _initialize_achievement_keywords(self) -> List[str]:
        """Initialize achievement indicator keywords"""
        return [
            "achieved", "accomplished", "awarded", "recognized", "exceeded",
            "surpassed", "outperformed", "won", "earned", "received",
            "successful", "successfully", "excellence", "outstanding",
            "exceptional", "significant", "substantial", "major"
        ]
    
    def _initialize_responsibility_keywords(self) -> List[str]:
        """Initialize responsibility-level keywords"""
        return [
            "responsible", "accountable", "ownership", "lead", "senior",
            "principal", "chief", "head", "manager", "director", "vp",
            "vice president", "executive", "architect", "expert", "specialist"
        ]
    
    def score_experience_text(self, experience_text: str) -> Dict[str, Any]:
        """
        Score experience text based on various factors
        
        Args:
            experience_text: Text from experience section
            
        Returns:
            Dictionary with scoring breakdown
        """
        try:
            if not experience_text:
                return self._empty_score()
            
            text_lower = experience_text.lower()
            
            # Calculate different score components
            scores = {
                "keyword_score": self._calculate_keyword_score(text_lower),
                "achievement_score": self._calculate_achievement_score(text_lower),
                "responsibility_score": self._calculate_responsibility_score(text_lower),
                "quantification_score": self._calculate_quantification_score(text_lower),
                "technical_depth_score": self._calculate_technical_depth_score(text_lower),
                "length_completeness_score": self._calculate_length_score(experience_text)
            }
            
            # Calculate weighted overall score
            weights = {
                "keyword_score": 0.25,
                "achievement_score": 0.20,
                "responsibility_score": 0.20,
                "quantification_score": 0.15,
                "technical_depth_score": 0.15,
                "length_completeness_score": 0.05
            }
            
            overall_score = sum(scores[component] * weights[component] 
                              for component in scores.keys())
            
            # Normalize to 0-100 scale
            overall_score = min(100, max(0, overall_score))
            
            # Extract additional insights
            insights = self._extract_experience_insights(experience_text, text_lower)
            
            return {
                "overall_score": round(overall_score, 1),
                "component_scores": {k: round(v, 1) for k, v in scores.items()},
                "score_weights": weights,
                "insights": insights,
                "experience_level": self._determine_experience_level(overall_score),
                "recommendations": self._generate_experience_recommendations(scores)
            }
            
        except Exception as e:
            logger.error(f"Error scoring experience text: {str(e)}")
            return self._empty_score()
    
    def _calculate_keyword_score(self, text_lower: str) -> float:
        """Calculate score based on experience keywords"""
        score = 0.0
        keyword_count = 0
        
        for keyword, weight in self.experience_keywords.items():
            count = len(re.findall(rf'\\b{re.escape(keyword)}\\b', text_lower))
            if count > 0:
                score += count * weight
                keyword_count += count
        
        # Normalize based on text length and keyword density
        if keyword_count > 0:
            words_count = len(text_lower.split())
            density_factor = min(1.0, keyword_count / max(1, words_count / 50))  # Expect ~1 keyword per 50 words
            score = score * density_factor
        
        return min(100, score)
    
    def _calculate_achievement_score(self, text_lower: str) -> float:
        """Calculate score based on achievement keywords"""
        achievement_count = 0
        
        for keyword in self.achievement_keywords:
            count = len(re.findall(rf'\\b{re.escape(keyword)}\\b', text_lower))
            achievement_count += count
        
        # Score based on achievement density
        words_count = len(text_lower.split())
        if words_count > 0:
            density = achievement_count / (words_count / 100)  # Per 100 words
            return min(100, density * 20)  # Scale appropriately
        
        return 0.0
    
    def _calculate_responsibility_score(self, text_lower: str) -> float:
        """Calculate score based on responsibility-level keywords"""
        responsibility_score = 0.0
        
        for keyword in self.responsibility_keywords:
            if keyword in text_lower:
                # Different keywords have different weights
                if keyword in ["chief", "director", "vp", "vice president", "head"]:
                    responsibility_score += 20
                elif keyword in ["manager", "lead", "senior", "principal"]:
                    responsibility_score += 15
                elif keyword in ["responsible", "accountable", "ownership"]:
                    responsibility_score += 10
                else:
                    responsibility_score += 5
        
        return min(100, responsibility_score)
    
    def _calculate_quantification_score(self, text_lower: str) -> float:
        """Calculate score based on quantified achievements"""
        # Look for numbers that indicate quantified results
        quantification_patterns = [
            r'\\b\\d+%\\b',  # Percentages
            r'\\b\\d+\\s*(?:million|thousand|k|m)\\b',  # Large numbers
            r'\\$\\d+(?:,\\d+)*(?:\\.\\d+)?',  # Money amounts
            r'\\b\\d+(?:,\\d+)*\\+?\\s*(?:users|customers|clients|people|employees)\\b',  # User counts
            r'\\b\\d+(?:,\\d+)*\\s*(?:projects|applications|systems)\\b',  # Project counts
            r'\\b(?:increased|improved|reduced|decreased)\\s+.*?\\b\\d+%\\b',  # Improvement percentages
            r'\\b\\d+\\s*(?:hours?|days?|weeks?|months?)\\b'  # Time periods
        ]
        
        quantification_count = 0
        for pattern in quantification_patterns:
            matches = re.findall(pattern, text_lower)
            quantification_count += len(matches)
        
        # Score based on quantification density
        if quantification_count > 0:
            sentences = len(re.findall(r'[.!?]+', text_lower))
            if sentences > 0:
                density = quantification_count / sentences
                return min(100, density * 30)  # Scale appropriately
        
        return 0.0
    
    def _calculate_technical_depth_score(self, text_lower: str) -> float:
        """Calculate score based on technical depth indicators"""
        technical_indicators = [
            "architecture", "design", "framework", "algorithm", "optimization",
            "integration", "api", "database", "cloud", "deployment", "scalability",
            "performance", "security", "testing", "debugging", "monitoring",
            "methodology", "best practices", "standards", "protocols"
        ]
        
        technical_score = 0.0
        for indicator in technical_indicators:
            if indicator in text_lower:
                technical_score += 5
        
        return min(100, technical_score)
    
    def _calculate_length_score(self, experience_text: str) -> float:
        """Calculate score based on experience text length and completeness"""
        word_count = len(experience_text.split())
        
        # Optimal range is 100-500 words
        if word_count < 50:
            return word_count * 1.0  # Linear increase up to 50
        elif word_count <= 200:
            return 50 + (word_count - 50) * 0.33  # Slower increase 50-200
        elif word_count <= 500:
            return 100  # Optimal range
        else:
            # Slight penalty for very long text
            return max(80, 100 - (word_count - 500) * 0.01)
    
    def _extract_experience_insights(self, experience_text: str, text_lower: str) -> Dict[str, Any]:
        """Extract insights from experience text"""
        insights = {
            "years_mentioned": self._extract_years_mentioned(text_lower),
            "companies_mentioned": self._count_company_mentions(experience_text),
            "technical_skills_count": len(self._extract_technical_skills(text_lower)),
            "leadership_indicators": self._count_leadership_indicators(text_lower),
            "achievement_indicators": self._count_achievement_indicators(text_lower),
            "project_mentions": self._count_project_mentions(text_lower)
        }
        
        return insights
    
    def _extract_years_mentioned(self, text_lower: str) -> List[float]:
        """Extract years of experience mentioned in text"""
        year_patterns = [
            r'(\\d+(?:\\.\\d+)?)\\+?\\s*years?\\s*(?:of\\s*)?experience',
            r'over\\s+(\\d+(?:\\.\\d+)?)\\s*years?',
            r'(\\d+(?:\\.\\d+)?)\\s*years?\\s*in'
        ]
        
        years = []
        for pattern in year_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years.append(float(match))
                except ValueError:
                    pass
        
        return years
    
    def _count_company_mentions(self, text: str) -> int:
        """Count potential company mentions"""
        # Look for patterns that suggest company names
        company_patterns = [
            r'\\bat\\s+[A-Z][a-zA-Z\\s&,.-]+(?:Inc|LLC|Corp|Ltd|Company)',
            r'\\bworked\\s+(?:at|for)\\s+[A-Z][a-zA-Z\\s&,.-]+',
            r'\\bjoined\\s+[A-Z][a-zA-Z\\s&,.-]+'
        ]
        
        count = 0
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            count += len(matches)
        
        return count
    
    def _extract_technical_skills(self, text_lower: str) -> List[str]:
        """Extract technical skills mentioned in experience"""
        # Common technical skills to look for
        tech_skills = [
            "python", "java", "javascript", "react", "angular", "node.js",
            "sql", "mongodb", "aws", "docker", "kubernetes", "git",
            "machine learning", "data science", "api", "microservices"
        ]
        
        found_skills = []
        for skill in tech_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _count_leadership_indicators(self, text_lower: str) -> int:
        """Count leadership indicators in text"""
        leadership_words = ["led", "managed", "supervised", "directed", "coordinated", "mentored"]
        count = 0
        
        for word in leadership_words:
            count += len(re.findall(rf'\\b{re.escape(word)}\\b', text_lower))
        
        return count
    
    def _count_achievement_indicators(self, text_lower: str) -> int:
        """Count achievement indicators in text"""
        count = 0
        for keyword in self.achievement_keywords:
            count += len(re.findall(rf'\\b{re.escape(keyword)}\\b', text_lower))
        
        return count
    
    def _count_project_mentions(self, text_lower: str) -> int:
        """Count project mentions in text"""
        project_patterns = [
            r'\\bproject\\b',
            r'\\bprojects\\b',
            r'\\bworked on\\b',
            r'\\bdelivered\\b',
            r'\\blaunched\\b'
        ]
        
        count = 0
        for pattern in project_patterns:
            count += len(re.findall(pattern, text_lower))
        
        return count
    
    def _determine_experience_level(self, overall_score: float) -> str:
        """Determine experience level based on overall score"""
        if overall_score >= 85:
            return "Expert"
        elif overall_score >= 70:
            return "Senior"
        elif overall_score >= 55:
            return "Mid-Level"
        elif overall_score >= 35:
            return "Junior"
        else:
            return "Entry Level"
    
    def _generate_experience_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on score components"""
        recommendations = []
        
        if scores["achievement_score"] < 30:
            recommendations.append("Add more quantified achievements and results")
        
        if scores["responsibility_score"] < 40:
            recommendations.append("Highlight leadership and responsibility aspects")
        
        if scores["technical_depth_score"] < 50:
            recommendations.append("Include more technical details and methodologies")
        
        if scores["quantification_score"] < 25:
            recommendations.append("Add specific numbers, percentages, and metrics")
        
        if scores["keyword_score"] < 60:
            recommendations.append("Use more action verbs and impactful language")
        
        return recommendations
    
    def _empty_score(self) -> Dict[str, Any]:
        """Return empty score structure"""
        return {
            "overall_score": 0.0,
            "component_scores": {
                "keyword_score": 0.0,
                "achievement_score": 0.0,
                "responsibility_score": 0.0,
                "quantification_score": 0.0,
                "technical_depth_score": 0.0,
                "length_completeness_score": 0.0
            },
            "score_weights": {},
            "insights": {},
            "experience_level": "Entry Level",
            "recommendations": ["No experience information found"]
        }