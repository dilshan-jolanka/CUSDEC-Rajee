"""
Scoring Engine for calculating overall CV scores and recommendations
"""

import logging
from typing import Dict, List, Any, Optional
import statistics

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Engine for calculating weighted scores and generating recommendations"""
    
    def __init__(self):
        """Initialize scoring engine"""
        self.default_weights = {
            "skills": 0.40,
            "experience": 0.30,
            "education": 0.20,
            "quality": 0.10
        }
        
        self.score_ranges = {
            "excellent": (90, 100),
            "very_good": (80, 89),
            "good": (70, 79),
            "fair": (60, 69),
            "poor": (0, 59)
        }
    
    async def calculate_overall_score(self, cv_analysis: Dict[str, Any], 
                                    job_requirements: Optional[Dict[str, Any]] = None,
                                    custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Calculate overall CV score based on analysis results
        
        Args:
            cv_analysis: Complete CV analysis results
            job_requirements: Optional job requirements for targeted scoring
            custom_weights: Optional custom weight distribution
            
        Returns:
            Comprehensive scoring results
        """
        try:
            weights = custom_weights or self.default_weights
            
            scoring_results = {
                "overall_score": 0.0,
                "component_scores": {},
                "score_breakdown": {},
                "score_grade": "",
                "percentile_rank": 0,
                "strengths": [],
                "improvement_areas": [],
                "recommendations": [],
                "confidence_level": 0.0
            }
            
            # Calculate component scores
            component_scores = await self._calculate_component_scores(cv_analysis, job_requirements)
            scoring_results["component_scores"] = component_scores
            
            # Calculate weighted overall score
            overall_score = 0.0
            score_breakdown = {}
            
            for component, score in component_scores.items():
                weight = weights.get(component, 0.0)
                weighted_score = score * weight
                overall_score += weighted_score
                
                score_breakdown[component] = {
                    "raw_score": score,
                    "weight": weight,
                    "weighted_score": round(weighted_score, 2)
                }
            
            scoring_results["overall_score"] = round(overall_score, 1)
            scoring_results["score_breakdown"] = score_breakdown
            
            # Determine score grade
            scoring_results["score_grade"] = self._determine_score_grade(overall_score)
            
            # Calculate confidence level
            scoring_results["confidence_level"] = self._calculate_confidence_level(cv_analysis)
            
            # Generate insights
            scoring_results["strengths"] = self._identify_scoring_strengths(component_scores)
            scoring_results["improvement_areas"] = self._identify_improvement_areas(component_scores)
            scoring_results["recommendations"] = await self._generate_scoring_recommendations(
                component_scores, cv_analysis, job_requirements
            )
            
            # Calculate percentile rank (simulated based on score distribution)
            scoring_results["percentile_rank"] = self._calculate_percentile_rank(overall_score)
            
            logger.info(f"Overall CV score calculated: {overall_score} ({scoring_results['score_grade']})")
            return scoring_results
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}")
            raise
    
    async def calculate_compatibility_percentage(self, cv_analysis: Dict[str, Any], 
                                               job_compatibility: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate job compatibility percentage with detailed analysis
        
        Args:
            cv_analysis: Complete CV analysis results
            job_compatibility: Job compatibility results from skill matcher
            
        Returns:
            Detailed compatibility assessment
        """
        try:
            compatibility_results = {
                "compatibility_percentage": 0.0,
                "match_level": "",
                "key_matches": [],
                "critical_gaps": [],
                "nice_to_have_gaps": [],
                "recommendation_priority": [],
                "estimated_preparation_time": "",
                "hiring_probability": ""
            }
            
            # Get base compatibility score
            base_compatibility = job_compatibility.get("overall_compatibility", 0.0)
            
            # Adjust based on additional factors
            adjustment_factors = self._calculate_compatibility_adjustments(cv_analysis)
            
            adjusted_compatibility = min(100.0, base_compatibility + adjustment_factors["total_adjustment"])
            compatibility_results["compatibility_percentage"] = round(adjusted_compatibility, 1)
            
            # Determine match level
            compatibility_results["match_level"] = self._determine_match_level(adjusted_compatibility)
            
            # Extract key information
            compatibility_results["key_matches"] = self._extract_key_matches(job_compatibility)
            compatibility_results["critical_gaps"] = self._extract_critical_gaps(job_compatibility)
            compatibility_results["nice_to_have_gaps"] = self._extract_nice_to_have_gaps(job_compatibility)
            
            # Generate recommendations with priority
            compatibility_results["recommendation_priority"] = self._prioritize_recommendations(
                job_compatibility, cv_analysis
            )
            
            # Estimate preparation time and hiring probability
            compatibility_results["estimated_preparation_time"] = self._estimate_preparation_time(
                compatibility_results["critical_gaps"]
            )
            compatibility_results["hiring_probability"] = self._estimate_hiring_probability(
                adjusted_compatibility
            )
            
            return compatibility_results
            
        except Exception as e:
            logger.error(f"Error calculating compatibility percentage: {str(e)}")
            raise
    
    async def generate_gap_analysis(self, cv_analysis: Dict[str, Any], 
                                  job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed gap analysis between CV and job requirements
        
        Args:
            cv_analysis: Complete CV analysis results
            job_requirements: Job requirements dictionary
            
        Returns:
            Detailed gap analysis
        """
        try:
            gap_analysis = {
                "skill_gaps": {},
                "experience_gaps": {},
                "education_gaps": {},
                "certification_gaps": [],
                "development_roadmap": [],
                "quick_wins": [],
                "long_term_goals": []
            }
            
            # Skill gaps analysis
            gap_analysis["skill_gaps"] = await self._analyze_skill_gaps(cv_analysis, job_requirements)
            
            # Experience gaps
            gap_analysis["experience_gaps"] = self._analyze_experience_gaps(cv_analysis, job_requirements)
            
            # Education gaps
            gap_analysis["education_gaps"] = self._analyze_education_gaps(cv_analysis, job_requirements)
            
            # Generate development roadmap
            gap_analysis["development_roadmap"] = self._create_development_roadmap(gap_analysis)
            
            # Identify quick wins and long-term goals
            gap_analysis["quick_wins"] = self._identify_quick_wins(gap_analysis)
            gap_analysis["long_term_goals"] = self._identify_long_term_goals(gap_analysis)
            
            return gap_analysis
            
        except Exception as e:
            logger.error(f"Error generating gap analysis: {str(e)}")
            raise
    
    async def _calculate_component_scores(self, cv_analysis: Dict[str, Any], 
                                        job_requirements: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate scores for each component"""
        component_scores = {}
        
        # Skills score
        skills_data = cv_analysis.get("skills_analysis", {})
        component_scores["skills"] = self._calculate_skills_score(skills_data)
        
        # Experience score
        experience_data = cv_analysis.get("experience_analysis", {})
        component_scores["experience"] = self._calculate_experience_score(experience_data)
        
        # Education score
        education_data = cv_analysis.get("education_analysis", {})
        component_scores["education"] = self._calculate_education_score(education_data)
        
        # Quality score (text quality, completeness, etc.)
        quality_data = cv_analysis.get("text_quality", {})
        component_scores["quality"] = self._calculate_quality_score(quality_data, cv_analysis)
        
        return component_scores
    
    def _calculate_skills_score(self, skills_data: Dict[str, Any]) -> float:
        """Calculate skills component score"""
        if not skills_data:
            return 0.0
        
        factors = []
        
        # Number of technical skills (max 40 points)
        technical_skills = skills_data.get("technical_skills", [])
        skill_count_score = min(40, len(technical_skills) * 2)
        factors.append(skill_count_score)
        
        # Skill diversity across categories (max 30 points)
        skill_categories = skills_data.get("skill_categories", {})
        category_count = len([cat for cat, skills in skill_categories.items() if skills])
        diversity_score = min(30, category_count * 5)
        factors.append(diversity_score)
        
        # Soft skills presence (max 15 points)
        soft_skills = skills_data.get("soft_skills", [])
        soft_skills_score = min(15, len(soft_skills) * 2)
        factors.append(soft_skills_score)
        
        # Skill frequency/expertise indicators (max 15 points)
        skill_frequency = skills_data.get("skill_frequency", {})
        frequency_score = min(15, len([s for s, f in skill_frequency.items() if f > 2]) * 3)
        factors.append(frequency_score)
        
        return sum(factors)
    
    def _calculate_experience_score(self, experience_data: Dict[str, Any]) -> float:
        """Calculate experience component score"""
        if not experience_data:
            return 0.0
        
        factors = []
        
        # Years of experience (max 50 points)
        total_years = experience_data.get("total_years", 0)
        years_score = min(50, total_years * 8)  # 8 points per year, max 50
        factors.append(years_score)
        
        # Experience quality (max 30 points)
        quality_score = experience_data.get("experience_quality_score", 0) * 0.3
        factors.append(quality_score)
        
        # Keywords and achievements (max 20 points)
        keywords_found = experience_data.get("keywords_found", [])
        keywords_score = min(20, len(keywords_found) * 2)
        factors.append(keywords_score)
        
        return sum(factors)
    
    def _calculate_education_score(self, education_data: Dict[str, Any]) -> float:
        """Calculate education component score"""
        if not education_data:
            return 30.0  # Base score for no formal education
        
        # Use the education level score from ML analyzer
        education_level_score = education_data.get("education_level_score", 0)
        
        # Adjust based on degrees
        degrees = education_data.get("degrees", [])
        degree_bonus = min(10, len(degrees) * 3)
        
        return min(100.0, education_level_score + degree_bonus)
    
    def _calculate_quality_score(self, quality_data: Dict[str, Any], cv_analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        if not quality_data:
            return 50.0  # Default score
        
        factors = []
        
        # Text quality from ML analyzer
        text_quality = quality_data.get("quality_score", 50)
        factors.append(text_quality * 0.4)
        
        # Completeness (presence of key sections)
        structured_sections = cv_analysis.get("structured_sections", {})
        completeness = sum(1 for section, content in structured_sections.items() 
                         if content and content.strip())
        completeness_score = min(30, completeness * 5)
        factors.append(completeness_score)
        
        # Contact information completeness
        contact_info = cv_analysis.get("contact_info", {})
        contact_completeness = sum(1 for key, value in contact_info.items() 
                                 if value and value.strip())
        contact_score = min(30, contact_completeness * 5)
        factors.append(contact_score)
        
        return sum(factors)
    
    def _determine_score_grade(self, score: float) -> str:
        """Determine letter grade based on score"""
        for grade, (min_score, max_score) in self.score_ranges.items():
            if min_score <= score <= max_score:
                return grade.replace("_", " ").title()
        return "Unknown"
    
    def _calculate_confidence_level(self, cv_analysis: Dict[str, Any]) -> float:
        """Calculate confidence level in the analysis"""
        confidence_factors = []
        
        # Text quality indicates confidence
        quality_data = cv_analysis.get("text_quality", {})
        word_count = quality_data.get("word_count", 0)
        if word_count > 500:
            confidence_factors.append(80)
        elif word_count > 200:
            confidence_factors.append(60)
        else:
            confidence_factors.append(30)
        
        # Structured sections presence
        structured_sections = cv_analysis.get("structured_sections", {})
        sections_with_content = sum(1 for content in structured_sections.values() 
                                  if content and content.strip())
        section_confidence = min(100, sections_with_content * 20)
        confidence_factors.append(section_confidence)
        
        # Contact information completeness
        contact_info = cv_analysis.get("contact_info", {})
        contact_fields = sum(1 for value in contact_info.values() if value and value.strip())
        contact_confidence = min(100, contact_fields * 25)
        confidence_factors.append(contact_confidence)
        
        return round(statistics.mean(confidence_factors), 1)
    
    def _identify_scoring_strengths(self, component_scores: Dict[str, float]) -> List[str]:
        """Identify strengths based on component scores"""
        strengths = []
        
        for component, score in component_scores.items():
            if score >= 80:
                strengths.append(f"Excellent {component} profile")
            elif score >= 70:
                strengths.append(f"Strong {component} background")
        
        return strengths
    
    def _identify_improvement_areas(self, component_scores: Dict[str, float]) -> List[str]:
        """Identify areas needing improvement"""
        improvement_areas = []
        
        for component, score in component_scores.items():
            if score < 60:
                improvement_areas.append(f"{component.title()} development needed")
            elif score < 70:
                improvement_areas.append(f"{component.title()} enhancement opportunity")
        
        return improvement_areas
    
    async def _generate_scoring_recommendations(self, component_scores: Dict[str, float],
                                              cv_analysis: Dict[str, Any],
                                              job_requirements: Optional[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on scoring analysis"""
        recommendations = []
        
        # Skills recommendations
        if component_scores.get("skills", 0) < 70:
            recommendations.append("Expand technical skill set and highlight existing expertise more prominently")
        
        # Experience recommendations
        if component_scores.get("experience", 0) < 70:
            recommendations.append("Emphasize achievements and quantifiable results in work experience")
        
        # Education recommendations
        if component_scores.get("education", 0) < 70:
            recommendations.append("Consider additional certifications or formal training")
        
        # Quality recommendations
        if component_scores.get("quality", 0) < 70:
            recommendations.append("Improve CV structure, formatting, and completeness")
        
        # Overall recommendations
        overall_score = sum(component_scores.values()) / len(component_scores)
        if overall_score < 70:
            recommendations.append("Focus on comprehensive CV improvement across all areas")
        
        return recommendations
    
    def _calculate_percentile_rank(self, score: float) -> int:
        """Calculate percentile rank (simulated distribution)"""
        # Simulated percentile calculation based on typical CV score distribution
        if score >= 90:
            return 95
        elif score >= 80:
            return 85
        elif score >= 70:
            return 70
        elif score >= 60:
            return 50
        elif score >= 50:
            return 30
        else:
            return 15
    
    def _calculate_compatibility_adjustments(self, cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjustments to base compatibility score"""
        adjustments = {
            "quality_adjustment": 0.0,
            "completeness_adjustment": 0.0,
            "experience_adjustment": 0.0,
            "total_adjustment": 0.0
        }
        
        # Quality adjustment
        quality_data = cv_analysis.get("text_quality", {})
        quality_score = quality_data.get("quality_score", 50)
        if quality_score > 80:
            adjustments["quality_adjustment"] = 5.0
        elif quality_score < 40:
            adjustments["quality_adjustment"] = -5.0
        
        # Completeness adjustment
        structured_sections = cv_analysis.get("structured_sections", {})
        complete_sections = sum(1 for content in structured_sections.values() 
                              if content and len(content.strip()) > 50)
        if complete_sections >= 4:
            adjustments["completeness_adjustment"] = 3.0
        elif complete_sections <= 1:
            adjustments["completeness_adjustment"] = -3.0
        
        # Calculate total adjustment
        adjustments["total_adjustment"] = sum([
            adjustments["quality_adjustment"],
            adjustments["completeness_adjustment"],
            adjustments["experience_adjustment"]
        ])
        
        return adjustments
    
    def _determine_match_level(self, compatibility_percentage: float) -> str:
        """Determine match level based on compatibility percentage"""
        if compatibility_percentage >= 90:
            return "Excellent Match"
        elif compatibility_percentage >= 80:
            return "Very Good Match"
        elif compatibility_percentage >= 70:
            return "Good Match"
        elif compatibility_percentage >= 60:
            return "Fair Match"
        else:
            return "Poor Match"
    
    def _extract_key_matches(self, job_compatibility: Dict[str, Any]) -> List[str]:
        """Extract key matching points"""
        matches = []
        
        # Add strengths from compatibility analysis
        strengths = job_compatibility.get("strengths", [])
        matches.extend(strengths[:3])  # Top 3 strengths
        
        return matches
    
    def _extract_critical_gaps(self, job_compatibility: Dict[str, Any]) -> List[str]:
        """Extract critical skill/experience gaps"""
        gaps = []
        
        # Add weaknesses from compatibility analysis
        weaknesses = job_compatibility.get("weaknesses", [])
        gaps.extend(weaknesses[:3])  # Top 3 weaknesses
        
        return gaps
    
    def _extract_nice_to_have_gaps(self, job_compatibility: Dict[str, Any]) -> List[str]:
        """Extract nice-to-have gaps"""
        # This would be based on preferred skills that are missing
        return ["Additional certifications", "More diverse project experience"]
    
    def _prioritize_recommendations(self, job_compatibility: Dict[str, Any], 
                                  cv_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on impact and effort"""
        recommendations = []
        
        # Get recommendations from job compatibility
        job_recommendations = job_compatibility.get("recommendations", [])
        
        for i, rec in enumerate(job_recommendations[:5]):  # Top 5 recommendations
            recommendations.append({
                "recommendation": rec,
                "priority": "High" if i < 2 else "Medium",
                "estimated_effort": "Medium",
                "expected_impact": "High" if i < 3 else "Medium"
            })
        
        return recommendations
    
    def _estimate_preparation_time(self, critical_gaps: List[str]) -> str:
        """Estimate time needed to address critical gaps"""
        gap_count = len(critical_gaps)
        
        if gap_count == 0:
            return "Ready to apply"
        elif gap_count <= 2:
            return "1-3 months preparation"
        elif gap_count <= 4:
            return "3-6 months preparation"
        else:
            return "6+ months preparation"
    
    def _estimate_hiring_probability(self, compatibility_percentage: float) -> str:
        """Estimate hiring probability based on compatibility"""
        if compatibility_percentage >= 85:
            return "Very High (80-90%)"
        elif compatibility_percentage >= 75:
            return "High (60-80%)"
        elif compatibility_percentage >= 65:
            return "Medium (40-60%)"
        elif compatibility_percentage >= 55:
            return "Low (20-40%)"
        else:
            return "Very Low (0-20%)"
    
    async def _analyze_skill_gaps(self, cv_analysis: Dict[str, Any], 
                                job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze skill gaps in detail"""
        # This would integrate with the skill matcher results
        return {
            "critical_missing": [],
            "preferred_missing": [],
            "skill_level_gaps": []
        }
    
    def _analyze_experience_gaps(self, cv_analysis: Dict[str, Any], 
                               job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze experience gaps"""
        experience_data = cv_analysis.get("experience_analysis", {})
        cv_years = experience_data.get("total_years", 0)
        required_years = job_requirements.get("minimum_experience", 0)
        
        return {
            "years_gap": max(0, required_years - cv_years),
            "domain_experience_missing": [],
            "leadership_experience_gap": cv_years < 3
        }
    
    def _analyze_education_gaps(self, cv_analysis: Dict[str, Any], 
                              job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze education gaps"""
        education_data = cv_analysis.get("education_analysis", {})
        
        return {
            "degree_level_gap": education_data.get("education_level_score", 0) < 60,
            "relevant_certifications_missing": [],
            "continuing_education_needed": True
        }
    
    def _create_development_roadmap(self, gap_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a development roadmap based on gap analysis"""
        roadmap = []
        
        # Add skill development steps
        skill_gaps = gap_analysis.get("skill_gaps", {})
        if skill_gaps:
            roadmap.append({
                "phase": "Phase 1: Skill Development",
                "duration": "1-3 months",
                "actions": ["Learn critical missing skills", "Practice with projects", "Get certifications"]
            })
        
        # Add experience building steps
        experience_gaps = gap_analysis.get("experience_gaps", {})
        if experience_gaps.get("years_gap", 0) > 0:
            roadmap.append({
                "phase": "Phase 2: Experience Building",
                "duration": "3-12 months",
                "actions": ["Seek relevant projects", "Volunteer for leadership", "Document achievements"]
            })
        
        return roadmap
    
    def _identify_quick_wins(self, gap_analysis: Dict[str, Any]) -> List[str]:
        """Identify quick wins for CV improvement"""
        return [
            "Update CV formatting and structure",
            "Add quantifiable achievements",
            "Highlight relevant keywords",
            "Complete online certifications"
        ]
    
    def _identify_long_term_goals(self, gap_analysis: Dict[str, Any]) -> List[str]:
        """Identify long-term development goals"""
        return [
            "Gain additional years of experience",
            "Develop leadership skills",
            "Build domain expertise",
            "Pursue advanced certifications"
        ]