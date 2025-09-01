"""
Validation utilities
"""

import re
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class CVValidationRules(BaseModel):
    """Validation rules for CV content"""
    min_word_count: int = 50
    max_word_count: int = 5000
    required_sections: List[str] = Field(default_factory=lambda: ["contact", "experience"])
    max_file_size_mb: int = 10


def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Check if it's a reasonable phone number length
    return 10 <= len(digits_only) <= 15


def validate_cv_content(cv_data: Dict[str, Any], rules: Optional[CVValidationRules] = None) -> Dict[str, Any]:
    """
    Validate CV content against specified rules
    
    Args:
        cv_data: Parsed CV data
        rules: Validation rules (uses defaults if not provided)
        
    Returns:
        Validation results dictionary
    """
    if rules is None:
        rules = CVValidationRules()
    
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "score": 0,
        "completeness": {}
    }
    
    try:
        raw_text = cv_data.get("raw_text", "")
        contact_info = cv_data.get("contact_info", {})
        structured_sections = cv_data.get("structured_sections", {})
        
        # Word count validation
        word_count = len(raw_text.split()) if raw_text else 0
        validation_results["completeness"]["word_count"] = word_count
        
        if word_count < rules.min_word_count:
            validation_results["errors"].append(f"CV too short: {word_count} words (minimum: {rules.min_word_count})")
            validation_results["is_valid"] = False
        elif word_count > rules.max_word_count:
            validation_results["warnings"].append(f"CV very long: {word_count} words (recommended max: {rules.max_word_count})")
        
        # Contact information validation
        contact_completeness = validate_contact_info(contact_info)
        validation_results["completeness"]["contact_info"] = contact_completeness
        
        if not contact_completeness["has_name"]:
            validation_results["errors"].append("Missing candidate name")
        
        if not contact_completeness["has_email"]:
            validation_results["warnings"].append("Missing email address")
        elif not validate_email(contact_completeness["email"]):
            validation_results["warnings"].append("Invalid email format")
        
        if contact_completeness["has_phone"] and not validate_phone(contact_completeness["phone"]):
            validation_results["warnings"].append("Invalid phone number format")
        
        # Section completeness validation
        section_completeness = validate_section_completeness(structured_sections)
        validation_results["completeness"]["sections"] = section_completeness
        
        missing_required = []
        for required_section in rules.required_sections:
            section_key = map_section_name(required_section)
            if not section_completeness.get(section_key, False):
                missing_required.append(required_section)
        
        if missing_required:
            validation_results["warnings"].append(f"Missing recommended sections: {', '.join(missing_required)}")
        
        # Calculate overall completeness score
        validation_results["score"] = calculate_completeness_score(validation_results["completeness"])
        
        # Content quality validation
        quality_issues = validate_content_quality(raw_text)
        validation_results["warnings"].extend(quality_issues)
        
        logger.info(f"CV validation completed. Score: {validation_results['score']}/100")
        return validation_results
        
    except Exception as e:
        logger.error(f"Error in CV validation: {str(e)}")
        validation_results["errors"].append(f"Validation error: {str(e)}")
        validation_results["is_valid"] = False
        return validation_results


def validate_contact_info(contact_info: Dict[str, Any]) -> Dict[str, Any]:
    """Validate contact information completeness and format"""
    return {
        "has_name": bool(contact_info.get("name")),
        "has_email": bool(contact_info.get("email")),
        "has_phone": bool(contact_info.get("phone")),
        "has_location": bool(contact_info.get("location")),
        "has_linkedin": bool(contact_info.get("linkedin")),
        "has_github": bool(contact_info.get("github")),
        "name": contact_info.get("name", ""),
        "email": contact_info.get("email", ""),
        "phone": contact_info.get("phone", ""),
        "completeness_score": sum([
            bool(contact_info.get("name")),
            bool(contact_info.get("email")),
            bool(contact_info.get("phone")),
            bool(contact_info.get("location"))
        ]) * 25  # 25 points per field
    }


def validate_section_completeness(structured_sections: Dict[str, str]) -> Dict[str, bool]:
    """Validate presence and quality of CV sections"""
    section_validation = {}
    
    for section_name, content in structured_sections.items():
        # Check if section has meaningful content (more than just whitespace)
        has_content = bool(content and content.strip() and len(content.strip()) > 20)
        section_validation[section_name] = has_content
    
    return section_validation


def map_section_name(required_section: str) -> str:
    """Map required section names to actual section names"""
    section_mapping = {
        "contact": "contact_info",
        "experience": "experience",
        "education": "education",
        "skills": "skills",
        "summary": "summary"
    }
    return section_mapping.get(required_section, required_section)


def calculate_completeness_score(completeness_data: Dict[str, Any]) -> int:
    """Calculate overall completeness score (0-100)"""
    scores = []
    
    # Word count score (30 points max)
    word_count = completeness_data.get("word_count", 0)
    word_score = min(30, word_count / 20)  # 1 point per 20 words, max 30
    scores.append(word_score)
    
    # Contact info score (30 points max)
    contact_score = completeness_data.get("contact_info", {}).get("completeness_score", 0)
    scores.append(min(30, contact_score))
    
    # Section completeness score (40 points max)
    sections = completeness_data.get("sections", {})
    section_score = sum(1 for has_content in sections.values() if has_content) * 8  # 8 points per section
    scores.append(min(40, section_score))
    
    return int(sum(scores))


def validate_content_quality(text: str) -> List[str]:
    """Validate content quality and return list of issues"""
    issues = []
    
    if not text:
        issues.append("No text content found")
        return issues
    
    # Check for excessive repetition
    words = text.lower().split()
    if len(words) > 0:
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only check words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Find overly repeated words
        total_words = len(words)
        for word, count in word_freq.items():
            if count > total_words * 0.05 and count > 10:  # More than 5% of total words and more than 10 times
                issues.append(f"Word '{word}' appears {count} times (possibly excessive repetition)")
    
    # Check for very short sentences (may indicate formatting issues)
    sentences = text.split('.')
    very_short_sentences = [s.strip() for s in sentences if len(s.strip()) < 10 and s.strip()]
    if len(very_short_sentences) > len(sentences) * 0.3:
        issues.append("Many very short sentences detected (possible formatting issues)")
    
    # Check for missing punctuation (indicates possible formatting issues)
    if len(re.findall(r'[.!?]', text)) < len(text.split()) * 0.1:
        issues.append("Very little punctuation detected (possible formatting issues)")
    
    # Check for excessive capitalization
    capital_letters = len(re.findall(r'[A-Z]', text))
    total_letters = len(re.findall(r'[A-Za-z]', text))
    if total_letters > 0 and capital_letters / total_letters > 0.3:
        issues.append("Excessive capitalization detected")
    
    return issues


def validate_job_requirements(job_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Validate job requirements data"""
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Check required skills
        required_skills = job_requirements.get("required_skills", [])
        if not required_skills:
            validation_results["warnings"].append("No required skills specified")
        elif len(required_skills) > 20:
            validation_results["warnings"].append("Very long required skills list (may affect matching accuracy)")
        
        # Check experience requirement
        min_experience = job_requirements.get("minimum_experience", 0)
        if min_experience < 0:
            validation_results["errors"].append("Minimum experience cannot be negative")
            validation_results["is_valid"] = False
        elif min_experience > 30:
            validation_results["warnings"].append("Very high experience requirement (30+ years)")
        
        # Check job description
        job_description = job_requirements.get("job_description", "")
        if not job_description:
            validation_results["warnings"].append("No job description provided (may limit matching accuracy)")
        elif len(job_description.split()) < 20:
            validation_results["warnings"].append("Very short job description (may limit matching accuracy)")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating job requirements: {str(e)}")
        validation_results["errors"].append(f"Validation error: {str(e)}")
        validation_results["is_valid"] = False
        return validation_results


def sanitize_input(text: str) -> str:
    """Sanitize text input for security"""
    if not text:
        return ""
    
    # Remove potential script tags and other dangerous content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Limit length
    if len(text) > 10000:
        text = text[:10000] + "..."
    
    return text


def validate_analysis_options(options: Dict[str, Any]) -> Dict[str, Any]:
    """Validate analysis options"""
    validation_results = {
        "is_valid": True,
        "errors": [],
        "sanitized_options": {}
    }
    
    valid_options = {
        "include_skills_analysis",
        "include_experience_analysis", 
        "include_education_analysis",
        "include_job_matching",
        "include_scoring"
    }
    
    try:
        for key, value in options.items():
            if key not in valid_options:
                validation_results["errors"].append(f"Unknown analysis option: {key}")
                continue
            
            if not isinstance(value, bool):
                validation_results["errors"].append(f"Analysis option '{key}' must be a boolean")
                continue
            
            validation_results["sanitized_options"][key] = value
        
        # Set defaults for missing options
        for option in valid_options:
            if option not in validation_results["sanitized_options"]:
                validation_results["sanitized_options"][option] = True
        
        if validation_results["errors"]:
            validation_results["is_valid"] = False
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating analysis options: {str(e)}")
        validation_results["errors"].append(f"Validation error: {str(e)}")
        validation_results["is_valid"] = False
        return validation_results