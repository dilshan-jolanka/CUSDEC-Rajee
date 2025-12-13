"""
Skill Matcher Service for matching CV skills with job requirements
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SkillMatcher:
    """Service for matching and scoring skills against job requirements"""
    
    def __init__(self):
        """Initialize skill matcher"""
        self.skill_synonyms = self._initialize_skill_synonyms()
        self.skill_weights = self._initialize_skill_weights()
        
    async def match_skills(self, cv_skills: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match CV skills against job requirements
        
        Args:
            cv_skills: Skills extracted from CV
            job_requirements: Job requirements and preferred skills
            
        Returns:
            Skill matching results
        """
        try:
            matching_results = {
                "matched_skills": [],
                "missing_skills": [],
                "skill_match_score": 0.0,
                "match_percentage": 0.0,
                "skill_gaps": [],
                "recommendations": [],
                "category_scores": {}
            }
            
            required_skills = job_requirements.get("required_skills", [])
            preferred_skills = job_requirements.get("preferred_skills", [])
            
            cv_technical_skills = cv_skills.get("technical_skills", [])
            cv_soft_skills = cv_skills.get("soft_skills", [])
            cv_skill_categories = cv_skills.get("skill_categories", {})
            
            all_cv_skills = cv_technical_skills + cv_soft_skills
            all_required_skills = required_skills + preferred_skills
            
            # Match skills
            matched_skills = self._find_matching_skills(all_cv_skills, required_skills)
            matched_preferred = self._find_matching_skills(all_cv_skills, preferred_skills)
            
            matching_results["matched_skills"] = matched_skills + matched_preferred
            
            # Find missing skills
            missing_required = self._find_missing_skills(all_cv_skills, required_skills)
            missing_preferred = self._find_missing_skills(all_cv_skills, preferred_skills)
            
            matching_results["missing_skills"] = {
                "required": missing_required,
                "preferred": missing_preferred
            }
            
            # Calculate scores
            required_match_score = len(matched_skills) / len(required_skills) if required_skills else 1.0
            preferred_match_score = len(matched_preferred) / len(preferred_skills) if preferred_skills else 0.5
            
            # Weighted score: 70% required, 30% preferred
            overall_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)
            matching_results["skill_match_score"] = round(overall_score * 100, 2)
            matching_results["match_percentage"] = round(overall_score * 100, 1)
            
            # Category-wise scoring
            matching_results["category_scores"] = self._calculate_category_scores(
                cv_skill_categories, required_skills + preferred_skills
            )
            
            # Generate recommendations
            matching_results["recommendations"] = self._generate_skill_recommendations(
                missing_required, missing_preferred, cv_skill_categories
            )
            
            # Skill gap analysis
            matching_results["skill_gaps"] = self._analyze_skill_gaps(
                missing_required, missing_preferred, cv_skill_categories
            )
            
            logger.info(f"Skill matching completed. Score: {matching_results['skill_match_score']}%")
            return matching_results
            
        except Exception as e:
            logger.error(f"Error in skill matching: {str(e)}")
            raise
    
    async def calculate_job_compatibility(self, cv_analysis: Dict[str, Any], 
                                        job_description: str) -> Dict[str, Any]:
        """
        Calculate overall job compatibility based on CV analysis
        
        Args:
            cv_analysis: Complete CV analysis results
            job_description: Job description text
            
        Returns:
            Job compatibility assessment
        """
        try:
            # Extract job requirements from description
            job_requirements = self._extract_job_requirements(job_description)
            
            compatibility_results = {
                "overall_compatibility": 0.0,
                "skill_compatibility": 0.0,
                "experience_compatibility": 0.0,
                "education_compatibility": 0.0,
                "compatibility_breakdown": {},
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
            
            # Get skill matching results
            cv_skills = cv_analysis.get("skills_analysis", {})
            skill_results = await self.match_skills(cv_skills, job_requirements)
            compatibility_results["skill_compatibility"] = skill_results["skill_match_score"]
            
            # Experience compatibility
            experience_data = cv_analysis.get("experience_analysis", {})
            experience_compatibility = self._calculate_experience_compatibility(
                experience_data, job_requirements
            )
            compatibility_results["experience_compatibility"] = experience_compatibility
            
            # Education compatibility
            education_data = cv_analysis.get("education_analysis", {})
            education_compatibility = self._calculate_education_compatibility(
                education_data, job_requirements
            )
            compatibility_results["education_compatibility"] = education_compatibility
            
            # Overall compatibility (weighted average)
            weights = {"skills": 0.5, "experience": 0.3, "education": 0.2}
            overall_score = (
                compatibility_results["skill_compatibility"] * weights["skills"] +
                compatibility_results["experience_compatibility"] * weights["experience"] +
                compatibility_results["education_compatibility"] * weights["education"]
            )
            compatibility_results["overall_compatibility"] = round(overall_score, 1)
            
            # Breakdown
            compatibility_results["compatibility_breakdown"] = {
                "skills": {"score": compatibility_results["skill_compatibility"], "weight": weights["skills"]},
                "experience": {"score": compatibility_results["experience_compatibility"], "weight": weights["experience"]},
                "education": {"score": compatibility_results["education_compatibility"], "weight": weights["education"]}
            }
            
            # Generate strengths and weaknesses
            compatibility_results["strengths"] = self._identify_strengths(cv_analysis, skill_results)
            compatibility_results["weaknesses"] = self._identify_weaknesses(cv_analysis, skill_results)
            
            # Generate recommendations
            compatibility_results["recommendations"] = self._generate_improvement_recommendations(
                compatibility_results["compatibility_breakdown"], skill_results
            )
            
            return compatibility_results
            
        except Exception as e:
            logger.error(f"Error calculating job compatibility: {str(e)}")
            raise
    
    def _find_matching_skills(self, cv_skills: List[str], required_skills: List[str]) -> List[Dict[str, Any]]:
        """Find matching skills between CV and requirements"""
        matches = []
        
        for required_skill in required_skills:
            best_match = None
            best_score = 0.0
            
            for cv_skill in cv_skills:
                # Direct match
                if cv_skill.lower() == required_skill.lower():
                    best_match = cv_skill
                    best_score = 1.0
                    break
                
                # Synonym match
                if self._are_skill_synonyms(cv_skill, required_skill):
                    if SequenceMatcher(None, cv_skill.lower(), required_skill.lower()).ratio() > best_score:
                        best_match = cv_skill
                        best_score = 0.9
                
                # Fuzzy match
                similarity = SequenceMatcher(None, cv_skill.lower(), required_skill.lower()).ratio()
                if similarity > 0.8 and similarity > best_score:
                    best_match = cv_skill
                    best_score = similarity
            
            if best_match and best_score >= 0.8:
                matches.append({
                    "required_skill": required_skill,
                    "matched_skill": best_match,
                    "match_score": round(best_score, 2)
                })
        
        return matches
    
    def _find_missing_skills(self, cv_skills: List[str], required_skills: List[str]) -> List[str]:
        """Find skills that are required but missing from CV"""
        cv_skills_lower = [skill.lower() for skill in cv_skills]
        missing = []
        
        for required_skill in required_skills:
            found = False
            
            # Check for direct match
            if required_skill.lower() in cv_skills_lower:
                found = True
            else:
                # Check for synonym match
                for cv_skill in cv_skills:
                    if self._are_skill_synonyms(cv_skill, required_skill):
                        found = True
                        break
                    
                    # Check fuzzy match
                    if SequenceMatcher(None, cv_skill.lower(), required_skill.lower()).ratio() > 0.8:
                        found = True
                        break
            
            if not found:
                missing.append(required_skill)
        
        return missing
    
    def _are_skill_synonyms(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are synonyms"""
        skill1_lower = skill1.lower()
        skill2_lower = skill2.lower()
        
        for skill_group in self.skill_synonyms:
            if skill1_lower in skill_group and skill2_lower in skill_group:
                return True
        
        return False
    
    def _calculate_category_scores(self, cv_categories: Dict[str, List[str]], 
                                 required_skills: List[str]) -> Dict[str, float]:
        """Calculate scores for each skill category"""
        category_scores = {}
        
        for category, cv_skills in cv_categories.items():
            if not cv_skills:
                category_scores[category] = 0.0
                continue
            
            matches = 0
            total_required = 0
            
            for required_skill in required_skills:
                # Check if this required skill belongs to current category
                if any(SequenceMatcher(None, cv_skill.lower(), required_skill.lower()).ratio() > 0.8 
                       for cv_skill in cv_skills):
                    matches += 1
                    total_required += 1
                elif self._skill_belongs_to_category(required_skill, category):
                    total_required += 1
            
            if total_required > 0:
                category_scores[category] = round((matches / total_required) * 100, 1)
            else:
                category_scores[category] = 50.0  # Neutral score if no relevant requirements
        
        return category_scores
    
    def _skill_belongs_to_category(self, skill: str, category: str) -> bool:
        """Check if a skill belongs to a specific category"""
        # This would typically use a more sophisticated categorization
        category_keywords = {
            "Programming Languages": ["python", "java", "javascript", "c++", "php", "ruby"],
            "Web Technologies": ["html", "css", "react", "angular", "vue", "node"],
            "Databases": ["sql", "mysql", "postgresql", "mongodb", "redis"],
            "Cloud & DevOps": ["aws", "azure", "docker", "kubernetes", "jenkins"],
            "Data Science & ML": ["machine learning", "data science", "pandas", "tensorflow"],
        }
        
        keywords = category_keywords.get(category, [])
        return any(keyword in skill.lower() for keyword in keywords)
    
    def _extract_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Extract requirements from job description text"""
        requirements = {
            "required_skills": [],
            "preferred_skills": [],
            "minimum_experience": 0,
            "education_requirements": [],
            "certifications": []
        }
        
        job_description_lower = job_description.lower()
        
        # Extract years of experience
        experience_patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            r"minimum\s*(\d+)\s*years?",
            r"at\s*least\s*(\d+)\s*years?"
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, job_description_lower)
            if matches:
                requirements["minimum_experience"] = max([int(match) for match in matches])
                break
        
        # Extract skills (this is a simplified version)
        # In a real implementation, this would be more sophisticated
        common_skills = [
            "python", "java", "javascript", "react", "angular", "node.js", "sql",
            "aws", "docker", "kubernetes", "machine learning", "data science"
        ]
        
        for skill in common_skills:
            if skill in job_description_lower:
                if any(word in job_description_lower for word in ["required", "must", "essential"]):
                    requirements["required_skills"].append(skill.title())
                else:
                    requirements["preferred_skills"].append(skill.title())
        
        return requirements
    
    def _calculate_experience_compatibility(self, experience_data: Dict[str, Any], 
                                          job_requirements: Dict[str, Any]) -> float:
        """Calculate experience compatibility score"""
        cv_experience = experience_data.get("total_years", 0)
        required_experience = job_requirements.get("minimum_experience", 0)
        
        if required_experience == 0:
            return 75.0  # Neutral score if no requirement
        
        if cv_experience >= required_experience:
            # Bonus for exceeding requirements
            excess_years = cv_experience - required_experience
            bonus = min(25, excess_years * 5)  # Up to 25 bonus points
            return min(100.0, 75.0 + bonus)
        else:
            # Penalty for not meeting requirements
            deficit = required_experience - cv_experience
            penalty = deficit * 15  # 15 points per missing year
            return max(0.0, 75.0 - penalty)
    
    def _calculate_education_compatibility(self, education_data: Dict[str, Any], 
                                         job_requirements: Dict[str, Any]) -> float:
        """Calculate education compatibility score"""
        education_score = education_data.get("education_level_score", 0)
        
        # Convert internal education score to compatibility percentage
        if education_score >= 100:  # PhD/Doctorate
            return 100.0
        elif education_score >= 80:  # Master's
            return 90.0
        elif education_score >= 60:  # Bachelor's
            return 75.0
        elif education_score >= 40:  # Other degree/diploma
            return 60.0
        else:
            return 30.0
    
    def _identify_strengths(self, cv_analysis: Dict[str, Any], 
                          skill_results: Dict[str, Any]) -> List[str]:
        """Identify candidate's strengths"""
        strengths = []
        
        # High skill match
        if skill_results.get("skill_match_score", 0) >= 80:
            strengths.append("Strong technical skill alignment with job requirements")
        
        # Experience
        experience_years = cv_analysis.get("experience_analysis", {}).get("total_years", 0)
        if experience_years >= 5:
            strengths.append(f"Extensive experience ({experience_years} years)")
        
        # Education
        education_score = cv_analysis.get("education_analysis", {}).get("education_level_score", 0)
        if education_score >= 80:
            strengths.append("Advanced educational background")
        
        # Diverse skills
        total_skills = cv_analysis.get("skills_analysis", {}).get("total_skills_found", 0)
        if total_skills >= 15:
            strengths.append("Diverse technical skill set")
        
        return strengths
    
    def _identify_weaknesses(self, cv_analysis: Dict[str, Any], 
                           skill_results: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement"""
        weaknesses = []
        
        # Low skill match
        if skill_results.get("skill_match_score", 0) < 60:
            weaknesses.append("Limited alignment with required technical skills")
        
        # Missing critical skills
        missing_required = skill_results.get("missing_skills", {}).get("required", [])
        if len(missing_required) > 3:
            weaknesses.append(f"Missing several critical skills: {', '.join(missing_required[:3])}")
        
        # Limited experience
        experience_years = cv_analysis.get("experience_analysis", {}).get("total_years", 0)
        if experience_years < 2:
            weaknesses.append("Limited professional experience")
        
        return weaknesses
    
    def _generate_skill_recommendations(self, missing_required: List[str], 
                                      missing_preferred: List[str],
                                      cv_categories: Dict[str, List[str]]) -> List[str]:
        """Generate skill-based recommendations"""
        recommendations = []
        
        if missing_required:
            top_missing = missing_required[:3]
            recommendations.append(f"Priority: Learn {', '.join(top_missing)} to meet job requirements")
        
        if missing_preferred:
            top_preferred = missing_preferred[:2]
            recommendations.append(f"Consider learning {', '.join(top_preferred)} to stand out")
        
        # Category-specific recommendations
        weak_categories = [cat for cat, skills in cv_categories.items() if len(skills) < 3]
        if weak_categories:
            recommendations.append(f"Strengthen skills in: {', '.join(weak_categories[:2])}")
        
        return recommendations
    
    def _analyze_skill_gaps(self, missing_required: List[str], missing_preferred: List[str],
                          cv_categories: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Analyze skill gaps in detail"""
        gaps = []
        
        for skill in missing_required:
            gaps.append({
                "skill": skill,
                "gap_type": "critical",
                "priority": "high",
                "category": self._categorize_skill(skill)
            })
        
        for skill in missing_preferred:
            gaps.append({
                "skill": skill,
                "gap_type": "enhancement",
                "priority": "medium",
                "category": self._categorize_skill(skill)
            })
        
        return gaps
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill"""
        skill_lower = skill.lower()
        
        if any(lang in skill_lower for lang in ["python", "java", "javascript", "c++"]):
            return "Programming Languages"
        elif any(web in skill_lower for web in ["html", "css", "react", "angular"]):
            return "Web Technologies"
        elif any(db in skill_lower for db in ["sql", "mysql", "mongodb"]):
            return "Databases"
        elif any(cloud in skill_lower for cloud in ["aws", "azure", "docker"]):
            return "Cloud & DevOps"
        else:
            return "Other"
    
    def _generate_improvement_recommendations(self, compatibility_breakdown: Dict[str, Any],
                                            skill_results: Dict[str, Any]) -> List[str]:
        """Generate overall improvement recommendations"""
        recommendations = []
        
        for area, data in compatibility_breakdown.items():
            if data["score"] < 70:
                if area == "skills":
                    recommendations.append("Focus on developing the missing technical skills")
                elif area == "experience":
                    recommendations.append("Gain more relevant work experience or highlight transferable skills")
                elif area == "education":
                    recommendations.append("Consider additional certifications or formal education")
        
        return recommendations
    
    def _initialize_skill_synonyms(self) -> List[List[str]]:
        """Initialize skill synonym groups"""
        return [
            ["javascript", "js", "ecmascript"],
            ["typescript", "ts"],
            ["python", "py"],
            ["react", "reactjs", "react.js"],
            ["angular", "angularjs"],
            ["vue", "vuejs", "vue.js"],
            ["node", "nodejs", "node.js"],
            ["postgresql", "postgres"],
            ["mongodb", "mongo"],
            ["machine learning", "ml", "artificial intelligence", "ai"],
            ["aws", "amazon web services"],
            ["gcp", "google cloud platform", "google cloud"],
            ["kubernetes", "k8s"],
            ["docker", "containerization"],
        ]
    
    def _initialize_skill_weights(self) -> Dict[str, float]:
        """Initialize weights for different skill categories"""
        return {
            "Programming Languages": 1.0,
            "Web Technologies": 0.9,
            "Databases": 0.8,
            "Cloud & DevOps": 0.8,
            "Data Science & ML": 0.9,
            "Mobile Development": 0.7,
            "Tools & Others": 0.6
        }