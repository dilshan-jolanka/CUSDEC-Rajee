"""
Helper utilities and common functions
"""

import uuid
import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())


def generate_api_key(prefix: str = "cvai") -> tuple[str, str]:
    """
    Generate a secure API key with prefix
    
    Returns:
        Tuple of (full_api_key, key_prefix)
    """
    # Generate secure random key
    key_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}_{key_part}"
    key_prefix = key_part[:8]  # First 8 characters for identification
    
    return full_key, key_prefix


def hash_password(password: str) -> str:
    """Hash password using SHA-256 (in production, use bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename to prevent path traversal attacks"""
    # Remove any directory path components
    filename = original_filename.split('/')[-1].split('\\')[-1]
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Add timestamp and random component for uniqueness
    timestamp = int(datetime.now().timestamp())
    random_part = secrets.token_hex(4)
    
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    secure_filename = f"{name}_{timestamp}_{random_part}"
    
    if ext:
        secure_filename += f".{ext}"
    
    return secure_filename


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Normalize quotes and apostrophes
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r'['']', "'", text)
    
    return text


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(email_pattern, text)))


def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    phone_patterns = [
        r'\+?\d{1,4}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}',
        r'\(\d{3}\)[\s.-]?\d{3}[\s.-]?\d{4}',
        r'\d{3}[\s.-]?\d{3}[\s.-]?\d{4}'
    ]
    
    phone_numbers = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean up the phone number
            cleaned = re.sub(r'[^\d+]', '', match)
            if len(cleaned) >= 10:  # Valid phone number length
                phone_numbers.append(match.strip())
    
    return list(set(phone_numbers))


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity"""
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for consistent matching"""
    if not skill:
        return ""
    
    # Convert to lowercase
    skill = skill.lower().strip()
    
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
        'mongo': 'mongodb',
        'k8s': 'kubernetes',
        'aws': 'amazon web services',
        'gcp': 'google cloud platform'
    }
    
    return normalizations.get(skill, skill)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def parse_experience_years(text: str) -> float:
    """Parse experience years from text"""
    if not text:
        return 0.0
    
    # Patterns to match years of experience
    patterns = [
        r'(\d+(?:\.\d+)?)\+?\s*years?\s*(?:of\s*)?experience',
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*years?',
        r'over\s+(\d+(?:\.\d+)?)\s*years?',
        r'(\d+(?:\.\d+)?)\s*years?\s*in',
        r'(\d+(?:\.\d+)?)\s*yrs?\s*(?:of\s*)?experience'
    ]
    
    years = 0.0
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                # Range pattern (e.g., "5-7 years")
                years = max(years, sum(float(x) for x in match if x) / len(match))
            else:
                years = max(years, float(match))
    
    return years


def categorize_experience_level(years: float) -> str:
    """Categorize experience level based on years"""
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


def calculate_readability_score(text: str) -> float:
    """Calculate a simple readability score (0-100)"""
    if not text:
        return 0.0
    
    sentences = len(re.findall(r'[.!?]+', text))
    words = len(text.split())
    
    if sentences == 0:
        return 0.0
    
    avg_sentence_length = words / sentences
    
    # Simple readability calculation (higher is better)
    # Penalize very long or very short sentences
    if avg_sentence_length < 5:
        score = 40
    elif avg_sentence_length < 15:
        score = 80
    elif avg_sentence_length < 25:
        score = 100
    else:
        score = max(20, 100 - (avg_sentence_length - 25) * 2)
    
    return min(100, max(0, score))


def extract_years_from_date_range(date_range: str) -> float:
    """Extract years from date range text (e.g., 'Jan 2020 - Present')"""
    if not date_range:
        return 0.0
    
    # Common date patterns
    date_patterns = [
        r'(\d{4})\s*-\s*(\d{4})',  # 2020-2023
        r'(\d{4})\s*-\s*(?:present|current|now)',  # 2020-Present
        r'(\w+)\s+(\d{4})\s*-\s*(\w+)\s+(\d{4})',  # Jan 2020 - Dec 2023
        r'(\w+)\s+(\d{4})\s*-\s*(?:present|current|now)',  # Jan 2020 - Present
    ]
    
    text_lower = date_range.lower()
    current_year = datetime.now().year
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            
            if len(groups) == 2:  # Simple year range
                start_year = int(groups[0])
                if 'present' in text_lower or 'current' in text_lower or 'now' in text_lower:
                    end_year = current_year
                else:
                    end_year = int(groups[1])
                
                return max(0, end_year - start_year)
            
            elif len(groups) == 4:  # Month-year range
                start_year = int(groups[1])
                if 'present' in text_lower or 'current' in text_lower or 'now' in text_lower:
                    end_year = current_year
                else:
                    end_year = int(groups[3])
                
                return max(0, end_year - start_year)
    
    return 0.0


def mask_sensitive_data(data: Dict[str, Any], fields_to_mask: List[str] = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionary"""
    if fields_to_mask is None:
        fields_to_mask = ['email', 'phone', 'password', 'api_key']
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        if key.lower() in [field.lower() for field in fields_to_mask]:
            if isinstance(value, str) and len(value) > 4:
                # Show first 2 and last 2 characters
                masked_data[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                masked_data[key] = "***"
    
    return masked_data


def validate_and_parse_json(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string with default fallback"""
    if not json_string:
        return default
    
    try:
        import json
        return json.loads(json_string)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default


def create_pagination_info(page: int, per_page: int, total_items: int) -> Dict[str, Any]:
    """Create pagination information"""
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    
    return {
        "current_page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None
    }


def rate_limit_key(user_id: int, endpoint: str, time_window: str = "minute") -> str:
    """Generate rate limit key for Redis"""
    current_time = datetime.now()
    
    if time_window == "minute":
        time_key = current_time.strftime("%Y%m%d%H%M")
    elif time_window == "hour":
        time_key = current_time.strftime("%Y%m%d%H")
    elif time_window == "day":
        time_key = current_time.strftime("%Y%m%d")
    else:
        time_key = current_time.strftime("%Y%m%d%H%M")
    
    return f"rate_limit:{user_id}:{endpoint}:{time_window}:{time_key}"