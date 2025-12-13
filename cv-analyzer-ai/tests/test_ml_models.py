"""
Tests for ML models
"""

import pytest
from ml_models.skill_classifier import SkillClassifier
from ml_models.experience_scorer import ExperienceScorer
from ml_models.job_matcher import JobMatcher


@pytest.fixture
def skill_classifier():
    """Create SkillClassifier instance for testing"""
    return SkillClassifier()


@pytest.fixture
def experience_scorer():
    """Create ExperienceScorer instance for testing"""
    return ExperienceScorer()


@pytest.fixture
def job_matcher():
    """Create JobMatcher instance for testing"""
    return JobMatcher()


class TestSkillClassifier:
    """Test cases for SkillClassifier"""
    
    def test_classify_skill_exact_match(self, skill_classifier):
        """Test exact skill classification"""
        result = skill_classifier.classify_skill("python")
        assert result == "Programming Languages"
        
        result = skill_classifier.classify_skill("react")
        assert result == "Web Technologies"
        
        result = skill_classifier.classify_skill("mysql")
        assert result == "Databases"
    
    def test_classify_skill_case_insensitive(self, skill_classifier):
        """Test case insensitive skill classification"""
        result = skill_classifier.classify_skill("PYTHON")
        assert result == "Programming Languages"
        
        result = skill_classifier.classify_skill("React")
        assert result == "Web Technologies"
    
    def test_classify_skill_unknown(self, skill_classifier):
        """Test classification of unknown skill"""
        result = skill_classifier.classify_skill("unknown-technology")
        assert result == "Tools & Others"
    
    def test_classify_skills_batch(self, skill_classifier):
        """Test batch skill classification"""
        skills = ["python", "react", "unknown-skill"]
        results = skill_classifier.classify_skills_batch(skills)
        
        assert results["python"] == "Programming Languages"
        assert results["react"] == "Web Technologies"
        assert results["unknown-skill"] == "Tools & Others"
    
    def test_get_category_distribution(self, skill_classifier):
        """Test category distribution calculation"""
        skills = ["python", "java", "react", "angular", "mysql"]
        distribution = skill_classifier.get_category_distribution(skills)
        
        assert distribution["Programming Languages"] == 2  # python, java
        assert distribution["Web Technologies"] == 2      # react, angular
        assert distribution["Databases"] == 1             # mysql
    
    def test_extract_skills_from_text(self, skill_classifier):
        """Test skill extraction from text"""
        text = "I have experience with Python programming and React development. I also know MySQL database."
        skills = skill_classifier._extract_skills_from_text(text)
        
        expected_skills = ["python", "react", "mysql"]
        for skill in expected_skills:
            assert skill in skills


class TestExperienceScorer:
    """Test cases for ExperienceScorer"""
    
    def test_score_experience_empty_text(self, experience_scorer):
        """Test scoring empty experience text"""
        result = experience_scorer.score_experience_text("")
        
        assert result["overall_score"] == 0.0
        assert result["experience_level"] == "Entry Level"
        assert "No experience information found" in result["recommendations"]
    
    def test_score_experience_with_keywords(self, experience_scorer):
        """Test scoring experience with action keywords"""
        text = """
        Led a team of 5 developers to develop and implement a new web application.
        Managed the entire project lifecycle and successfully delivered the product.
        Improved system performance by 30% and reduced processing time.
        """
        
        result = experience_scorer.score_experience_text(text)
        
        assert result["overall_score"] > 50
        assert result["component_scores"]["keyword_score"] > 0
        assert result["component_scores"]["achievement_score"] > 0
        assert result["experience_level"] in ["Junior", "Mid-Level", "Senior", "Expert"]
    
    def test_score_experience_with_quantification(self, experience_scorer):
        """Test scoring experience with quantified achievements"""
        text = """
        Increased sales by 25% and managed a budget of $500,000.
        Led a team of 10 people and delivered 3 major projects.
        Reduced costs by $100K annually.
        """
        
        result = experience_scorer.score_experience_text(text)
        
        assert result["component_scores"]["quantification_score"] > 0
        assert result["component_scores"]["achievement_score"] > 0
    
    def test_extract_years_mentioned(self, experience_scorer):
        """Test extraction of years mentioned in text"""
        text = "I have 5 years of experience in software development and over 3 years in leadership roles."
        years = experience_scorer._extract_years_mentioned(text.lower())
        
        assert 5.0 in years
        assert 3.0 in years
    
    def test_leadership_indicators_count(self, experience_scorer):
        """Test counting leadership indicators"""
        text = "I led the team, managed projects, and supervised junior developers."
        count = experience_scorer._count_leadership_indicators(text.lower())
        
        assert count >= 3  # led, managed, supervised


class TestJobMatcher:
    """Test cases for JobMatcher"""
    
    def test_normalize_skill(self, job_matcher):
        """Test skill normalization"""
        assert job_matcher._normalize_skill("JavaScript") == "javascript"
        assert job_matcher._normalize_skill("JS") == "javascript"
        assert job_matcher._normalize_skill("ReactJS") == "react"
        assert job_matcher._normalize_skill("PostgreSQL") == "postgres"
    
    def test_find_skill_matches(self, job_matcher):
        """Test finding skill matches"""
        cv_skills = ["python", "javascript", "react", "node.js"]
        required_skills = ["python", "react", "vue"]
        
        matches = job_matcher._find_skill_matches(cv_skills, required_skills)
        
        assert "python" in matches
        assert "react" in matches
        assert "vue" not in matches
    
    def test_categorize_experience_level(self, job_matcher):
        """Test experience level categorization"""
        assert job_matcher._categorize_experience_level(0.5) == "Entry Level"
        assert job_matcher._categorize_experience_level(2.0) == "Junior"
        assert job_matcher._categorize_experience_level(5.0) == "Mid-Level"
        assert job_matcher._categorize_experience_level(10.0) == "Senior"
        assert job_matcher._categorize_experience_level(15.0) == "Expert"
    
    def test_categorize_education_level(self, job_matcher):
        """Test education level categorization"""
        assert "PhD" in job_matcher._categorize_education_level(100)
        assert "Master's" in job_matcher._categorize_education_level(85)
        assert "Bachelor's" in job_matcher._categorize_education_level(65)
        assert "High School" in job_matcher._categorize_education_level(30)
    
    @pytest.mark.asyncio
    async def test_calculate_job_match_score_empty_data(self, job_matcher):
        """Test job match calculation with empty data"""
        cv_data = {}
        job_requirements = {}
        
        result = await job_matcher.calculate_job_match_score(cv_data, job_requirements)
        
        assert "overall_match_score" in result
        assert "skill_match" in result
        assert "experience_match" in result
        assert "education_match" in result
    
    @pytest.mark.asyncio 
    async def test_calculate_job_match_score_with_data(self, job_matcher):
        """Test job match calculation with sample data"""
        cv_data = {
            "skills_analysis": {
                "technical_skills": ["python", "javascript", "react"],
                "soft_skills": ["communication", "teamwork"]
            },
            "experience_analysis": {
                "total_years": 5,
                "experience_quality_score": 80
            },
            "education_analysis": {
                "education_level_score": 75,
                "degrees": ["bachelor's"]
            }
        }
        
        job_requirements = {
            "required_skills": ["python", "react"],
            "preferred_skills": ["javascript", "vue"],
            "minimum_experience": 3,
            "job_description": "Python developer position"
        }
        
        result = await job_matcher.calculate_job_match_score(cv_data, job_requirements)
        
        assert result["overall_match_score"] > 0
        assert len(result["strengths"]) > 0 or len(result["gaps"]) > 0
        assert "skill_match" in result
        assert result["skill_match"]["match_score"] > 0


@pytest.mark.integration
class TestMLModelsIntegration:
    """Integration tests for ML models working together"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, skill_classifier, experience_scorer, job_matcher):
        """Test full ML pipeline integration"""
        # Sample CV data
        cv_text = """
        John Doe
        Senior Software Engineer
        
        Experience:
        Led development of web applications using Python and React.
        Managed a team of 5 developers for 3 years.
        Improved system performance by 40% and delivered 10+ projects successfully.
        
        Skills: Python, JavaScript, React, SQL, AWS, Leadership
        
        Education: Bachelor's in Computer Science
        """
        
        # Extract and classify skills
        skills = skill_classifier._extract_skills_from_text(cv_text)
        skill_categories = {}
        for skill in skills:
            category = skill_classifier.classify_skill(skill)
            if category not in skill_categories:
                skill_categories[category] = []
            skill_categories[category].append(skill)
        
        # Score experience
        experience_score = experience_scorer.score_experience_text(cv_text)
        
        # Prepare data for job matching
        cv_data = {
            "skills_analysis": {
                "technical_skills": skills,
                "skill_categories": skill_categories
            },
            "experience_analysis": {
                "total_years": 5,
                "experience_quality_score": experience_score["overall_score"]
            },
            "education_analysis": {
                "education_level_score": 75
            }
        }
        
        job_requirements = {
            "required_skills": ["python", "react"],
            "minimum_experience": 3
        }
        
        # Calculate job match
        match_result = await job_matcher.calculate_job_match_score(cv_data, job_requirements)
        
        # Assertions
        assert len(skills) > 0
        assert len(skill_categories) > 0
        assert experience_score["overall_score"] > 0
        assert match_result["overall_match_score"] > 0
        
        print(f"Skills found: {skills}")
        print(f"Skill categories: {skill_categories}")
        print(f"Experience score: {experience_score['overall_score']}")
        print(f"Job match score: {match_result['overall_match_score']}")


if __name__ == "__main__":
    pytest.main([__file__])