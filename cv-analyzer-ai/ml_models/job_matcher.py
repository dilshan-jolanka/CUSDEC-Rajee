"""
Job Matching ML Model
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Any, Optional
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class JobMatcher:
    """ML model for matching CVs against job requirements"""
    
    def __init__(self):
        """Initialize job matcher"""
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            lowercase=True,
            stop_words='english'
        )
        
        # Skill importance weights
        self.skill_weights = {
            "critical": 1.0,
            "important": 0.7,
            "nice_to_have": 0.3
        }
        
        # Experience level mappings
        self.experience_levels = {
            "entry": (0, 2),
            "junior": (1, 4), 
            "mid": (3, 7),
            "senior": (5, 12),
            "expert": (8, 999)
        }
    
    def calculate_job_match_score(self, cv_data: Dict[str, Any], 
                                 job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive job match score
        
        Args:
            cv_data: CV analysis data
            job_requirements: Job requirements dictionary
            
        Returns:
            Detailed job match results
        """
        try:
            match_results = {
                "overall_match_score": 0.0,
                "skill_match": {},
                "experience_match": {},
                "education_match": {},
                "cultural_match": {},
                "match_breakdown": {},
                "strengths": [],
                "gaps": [],
                "recommendations": []
            }
            
            # Calculate component matches
            skill_match = self._calculate_skill_match(cv_data, job_requirements)
            experience_match = self._calculate_experience_match(cv_data, job_requirements)
            education_match = self._calculate_education_match(cv_data, job_requirements)
            cultural_match = self._calculate_cultural_match(cv_data, job_requirements)
            
            match_results["skill_match"] = skill_match
            match_results["experience_match"] = experience_match
            match_results["education_match"] = education_match
            match_results["cultural_match"] = cultural_match
            
            # Calculate weighted overall score
            weights = {
                "skills": 0.45,
                "experience": 0.25,
                "education": 0.15,
                "cultural": 0.15
            }
            
            overall_score = (
                skill_match["match_score"] * weights["skills"] +
                experience_match["match_score"] * weights["experience"] +
                education_match["match_score"] * weights["education"] +
                cultural_match["match_score"] * weights["cultural"]
            )
            
            match_results["overall_match_score"] = round(overall_score, 1)
            match_results["match_breakdown"] = {
                component: {
                    "score": match_results[f"{component}_match"]["match_score"],
                    "weight": weights[component],
                    "weighted_score": match_results[f"{component}_match"]["match_score"] * weights[component]
                }
                for component in weights.keys()
            }
            
            # Generate insights
            match_results["strengths"] = self._identify_match_strengths(match_results)
            match_results["gaps"] = self._identify_match_gaps(match_results)
            match_results["recommendations"] = self._generate_match_recommendations(match_results)
            
            return match_results
            
        except Exception as e:
            logger.error(f"Error calculating job match score: {str(e)}")
            return self._empty_match_results()
    
    def _calculate_skill_match(self, cv_data: Dict[str, Any], 
                              job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate skill matching score"""
        try:
            cv_skills = cv_data.get("skills_analysis", {})
            required_skills = job_requirements.get("required_skills", [])
            preferred_skills = job_requirements.get("preferred_skills", [])
            
            cv_technical_skills = cv_skills.get("technical_skills", [])
            cv_soft_skills = cv_skills.get("soft_skills", [])
            all_cv_skills = cv_technical_skills + cv_soft_skills
            
            # Normalize skills for comparison
            cv_skills_normalized = [self._normalize_skill(skill) for skill in all_cv_skills]
            required_normalized = [self._normalize_skill(skill) for skill in required_skills]
            preferred_normalized = [self._normalize_skill(skill) for skill in preferred_skills]
            
            # Find matches
            required_matches = self._find_skill_matches(cv_skills_normalized, required_normalized)
            preferred_matches = self._find_skill_matches(cv_skills_normalized, preferred_normalized)
            
            # Calculate scores
            required_score = len(required_matches) / len(required_skills) * 100 if required_skills else 100
            preferred_score = len(preferred_matches) / len(preferred_skills) * 100 if preferred_skills else 100
            
            # Weighted skill score (70% required, 30% preferred)
            skill_score = (required_score * 0.7) + (preferred_score * 0.3)
            
            return {
                "match_score": round(skill_score, 1),
                "required_matches": required_matches,
                "preferred_matches": preferred_matches,
                "missing_required": [skill for skill in required_skills 
                                   if self._normalize_skill(skill) not in required_matches],
                "missing_preferred": [skill for skill in preferred_skills 
                                    if self._normalize_skill(skill) not in preferred_matches],
                "extra_skills": [skill for skill in all_cv_skills 
                               if self._normalize_skill(skill) not in required_normalized + preferred_normalized],
                "skill_coverage": {
                    "required": f"{len(required_matches)}/{len(required_skills)}",
                    "preferred": f"{len(preferred_matches)}/{len(preferred_skills)}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating skill match: {str(e)}")
            return {"match_score": 0.0}
    
    def _calculate_experience_match(self, cv_data: Dict[str, Any], 
                                   job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate experience matching score"""
        try:
            experience_data = cv_data.get("experience_analysis", {})
            cv_years = experience_data.get("total_years", 0)
            required_years = job_requirements.get("minimum_experience", 0)
            
            # Calculate years match
            if required_years == 0:
                years_score = 80  # No requirement is neutral
            elif cv_years >= required_years:
                # Bonus for exceeding requirements
                excess_years = cv_years - required_years
                bonus = min(20, excess_years * 2)  # Up to 20 bonus points
                years_score = 80 + bonus
            else:
                # Penalty for not meeting requirements
                deficit = required_years - cv_years
                penalty = deficit * 10  # 10 points per missing year
                years_score = max(20, 80 - penalty)
            
            # Calculate experience quality
            experience_quality = experience_data.get("experience_quality_score", 50)
            
            # Calculate domain relevance (simplified)
            domain_relevance = self._calculate_domain_relevance(
                experience_data, job_requirements.get("job_description", "")
            )
            
            # Combined experience score
            experience_score = (years_score * 0.5) + (experience_quality * 0.3) + (domain_relevance * 0.2)
            
            return {
                "match_score": round(experience_score, 1),
                "years_match": {
                    "cv_years": cv_years,
                    "required_years": required_years,
                    "meets_requirement": cv_years >= required_years,
                    "score": round(years_score, 1)
                },
                "quality_score": round(experience_quality, 1),
                "domain_relevance": round(domain_relevance, 1),
                "experience_level": self._categorize_experience_level(cv_years)
            }
            
        except Exception as e:
            logger.error(f"Error calculating experience match: {str(e)}")
            return {"match_score": 0.0}
    
    def _calculate_education_match(self, cv_data: Dict[str, Any], 
                                  job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate education matching score"""
        try:
            education_data = cv_data.get("education_analysis", {})
            education_score = education_data.get("education_level_score", 0)
            degrees = education_data.get("degrees", [])
            
            required_education = job_requirements.get("education_requirements", [])
            
            # Base score from education level
            base_score = min(100, education_score)
            
            # Check for specific degree requirements
            degree_match_score = 100  # Default if no specific requirements
            if required_education:
                matches = self._find_education_matches(degrees, required_education)
                degree_match_score = (len(matches) / len(required_education)) * 100
            
            # Combined education score
            education_match_score = (base_score * 0.7) + (degree_match_score * 0.3)
            
            return {
                "match_score": round(education_match_score, 1),
                "education_level": self._categorize_education_level(education_score),
                "degrees_found": degrees,
                "required_education": required_education,
                "meets_requirements": degree_match_score >= 80
            }
            
        except Exception as e:
            logger.error(f"Error calculating education match: {str(e)}")
            return {"match_score": 0.0}
    
    def _calculate_cultural_match(self, cv_data: Dict[str, Any], 
                                 job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cultural fit based on soft skills and language"""
        try:
            skills_data = cv_data.get("skills_analysis", {})
            soft_skills = skills_data.get("soft_skills", [])
            language_data = cv_data.get("language_analysis", {})
            
            # Soft skills alignment
            desired_soft_skills = ["communication", "teamwork", "leadership", "problem solving"]
            soft_skill_matches = [skill for skill in soft_skills 
                                if any(desired in skill.lower() for desired in desired_soft_skills)]
            soft_skills_score = min(100, len(soft_skill_matches) * 25)
            
            # Language proficiency
            languages = language_data.get("languages", [])
            language_score = min(100, len(languages) * 30) if languages else 70  # Neutral for no language info
            
            # Communication indicators (from text quality)
            text_quality = cv_data.get("text_quality", {})
            communication_score = text_quality.get("quality_score", 50)
            
            # Combined cultural score
            cultural_score = (soft_skills_score * 0.4) + (language_score * 0.3) + (communication_score * 0.3)
            
            return {
                "match_score": round(cultural_score, 1),
                "soft_skills_match": soft_skill_matches,
                "language_proficiency": languages,
                "communication_quality": round(communication_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating cultural match: {str(e)}")
            return {"match_score": 50.0}
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name for comparison"""
        # Common normalizations
        normalizations = {
            'js': 'javascript',
            'ts': 'typescript', 
            'py': 'python',
            'reactjs': 'react',
            'react.js': 'react',
            'vuejs': 'vue',
            'vue.js': 'vue',
            'nodejs': 'node.js',
            'node': 'node.js',
            'postgresql': 'postgres',
            'mongo': 'mongodb'
        }
        
        skill_lower = skill.lower().strip()
        return normalizations.get(skill_lower, skill_lower)
    
    def _find_skill_matches(self, cv_skills: List[str], required_skills: List[str]) -> List[str]:
        """Find matching skills between CV and requirements"""
        matches = []
        
        for required_skill in required_skills:
            for cv_skill in cv_skills:
                # Exact match
                if cv_skill == required_skill:
                    matches.append(required_skill)
                    break
                # Partial match (one contains the other)
                elif (required_skill in cv_skill or cv_skill in required_skill) and len(cv_skill) > 2:
                    matches.append(required_skill)
                    break
        
        return matches
    
    def _calculate_domain_relevance(self, experience_data: Dict[str, Any], job_description: str) -> float:
        """Calculate domain relevance of experience"""
        if not job_description:
            return 50.0  # Neutral score
        
        experience_keywords = experience_data.get("keywords_found", [])
        
        # Extract keywords from job description
        job_keywords = self._extract_keywords_from_job_description(job_description)
        
        if not job_keywords or not experience_keywords:
            return 50.0
        
        # Calculate keyword overlap
        experience_set = set(keyword.lower() for keyword in experience_keywords)
        job_set = set(keyword.lower() for keyword in job_keywords)
        
        if not experience_set or not job_set:
            return 50.0
        
        intersection = experience_set.intersection(job_set)
        union = experience_set.union(job_set)
        
        relevance_score = (len(intersection) / len(union)) * 100 if union else 50.0
        return min(100, relevance_score)
    
    def _extract_keywords_from_job_description(self, job_description: str) -> List[str]:
        """Extract relevant keywords from job description"""
        # Simple keyword extraction (in production, use more sophisticated NLP)
        important_words = []
        
        # Remove common stop words and extract meaningful terms
        words = re.findall(r'\\b[a-zA-Z]{3,}\\b', job_description.lower())
        
        # Filter for technical and business terms
        tech_business_indicators = [
            'develop', 'design', 'implement', 'manage', 'lead', 'create',
            'build', 'optimize', 'analyze', 'strategy', 'solution',
            'system', 'platform', 'application', 'service', 'product'
        ]
        
        word_freq = Counter(words)
        for word, freq in word_freq.most_common(20):
            if word in tech_business_indicators or freq > 2:
                important_words.append(word)
        
        return important_words
    
    def _categorize_experience_level(self, years: float) -> str:
        """Categorize experience level"""
        if years < 1:
            return "Entry Level"
        elif years < 3:
            return "Junior"
        elif years < 7:
            return "Mid-Level"
        elif years < 12:
            return "Senior"
        else:
            return "Expert"
    
    def _categorize_education_level(self, education_score: float) -> str:
        """Categorize education level"""
        if education_score >= 100:
            return "Advanced Degree (PhD/Doctorate)"
        elif education_score >= 80:
            return "Graduate Degree (Master's/MBA)"
        elif education_score >= 60:
            return "Bachelor's Degree"
        elif education_score >= 40:
            return "Associate Degree/Diploma"
        else:
            return "High School/Other"
    
    def _find_education_matches(self, cv_degrees: List[str], required_education: List[str]) -> List[str]:
        """Find education matches"""
        matches = []
        
        cv_degrees_lower = [degree.lower() for degree in cv_degrees]
        
        for req_edu in required_education:
            req_edu_lower = req_edu.lower()
            
            # Check for matches
            for cv_degree in cv_degrees_lower:
                if req_edu_lower in cv_degree or cv_degree in req_edu_lower:
                    matches.append(req_edu)
                    break
        
        return matches
    
    def _identify_match_strengths(self, match_results: Dict[str, Any]) -> List[str]:
        """Identify candidate's strengths for this job"""
        strengths = []
        
        # Check each component
        for component in ["skill", "experience", "education", "cultural"]:
            match_key = f"{component}_match"
            if match_key in match_results:
                score = match_results[match_key].get("match_score", 0)
                if score >= 80:
                    strengths.append(f"Strong {component} alignment ({score}%)")
                elif score >= 70:
                    strengths.append(f"Good {component} match ({score}%)")
        
        # Specific strengths
        skill_match = match_results.get("skill_match", {})
        if len(skill_match.get("required_matches", [])) >= 3:
            strengths.append("Meets most critical skill requirements")
        
        experience_match = match_results.get("experience_match", {})
        if experience_match.get("years_match", {}).get("meets_requirement", False):
            strengths.append("Meets experience requirements")
        
        return strengths
    
    def _identify_match_gaps(self, match_results: Dict[str, Any]) -> List[str]:
        """Identify gaps between candidate and job requirements"""
        gaps = []
        
        # Skill gaps
        skill_match = match_results.get("skill_match", {})
        missing_required = skill_match.get("missing_required", [])
        if missing_required:
            gaps.append(f"Missing required skills: {', '.join(missing_required[:3])}")
        
        # Experience gaps
        experience_match = match_results.get("experience_match", {})
        years_match = experience_match.get("years_match", {})
        if not years_match.get("meets_requirement", True):
            cv_years = years_match.get("cv_years", 0)
            required_years = years_match.get("required_years", 0)
            gap_years = required_years - cv_years
            gaps.append(f"Experience gap: {gap_years} years short of requirement")
        
        # Education gaps
        education_match = match_results.get("education_match", {})
        if not education_match.get("meets_requirements", True):
            gaps.append("Education requirements not fully met")
        
        return gaps
    
    def _generate_match_recommendations(self, match_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations to improve job match"""
        recommendations = []
        
        # Skill recommendations
        skill_match = match_results.get("skill_match", {})
        missing_required = skill_match.get("missing_required", [])
        if missing_required:
            recommendations.append(f"Develop skills in: {', '.join(missing_required[:3])}")
        
        # Experience recommendations
        experience_match = match_results.get("experience_match", {})
        if experience_match.get("match_score", 0) < 70:
            recommendations.append("Gain more relevant work experience")
        
        # Education recommendations  
        education_match = match_results.get("education_match", {})
        if education_match.get("match_score", 0) < 70:
            recommendations.append("Consider additional certifications or formal education")
        
        # Cultural recommendations
        cultural_match = match_results.get("cultural_match", {})
        if cultural_match.get("match_score", 0) < 70:
            recommendations.append("Highlight soft skills and communication abilities")
        
        return recommendations
    
    def _empty_match_results(self) -> Dict[str, Any]:
        """Return empty match results"""
        return {
            "overall_match_score": 0.0,
            "skill_match": {"match_score": 0.0},
            "experience_match": {"match_score": 0.0},
            "education_match": {"match_score": 0.0},
            "cultural_match": {"match_score": 0.0},
            "match_breakdown": {},
            "strengths": [],
            "gaps": ["Unable to calculate match - insufficient data"],
            "recommendations": ["Ensure complete CV and job requirement information"]
        }