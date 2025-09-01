# CV Analyzer AI - API Documentation

## Overview

The CV Analyzer AI provides comprehensive resume analysis through RESTful API endpoints. This documentation covers all available endpoints, request/response formats, and authentication methods.

## Base URL

```
https://api.cvanalyzer.ai/api/v1
```

For local development:
```
http://localhost:8000/api/v1
```

## Authentication

The API uses API key authentication. All requests must include an API key in the Authorization header:

```http
Authorization: Bearer cvai_your_api_key_here
```

### Getting an API Key

1. Register a user account
2. Login to get access token
3. Create API key using the access token

```bash
# Register
curl -X POST "https://api.cvanalyzer.ai/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "email": "your@email.com", 
    "password": "your_password"
  }'

# Login
curl -X POST "https://api.cvanalyzer.ai/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# Create API Key (using access token from login)
curl -X POST "https://api.cvanalyzer.ai/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "My API Key",
    "permissions": "basic"
  }'
```

## Core Endpoints

### 1. Analyze CV

Upload and analyze a single CV file.

**Endpoint:** `POST /analyze-cv`

**Parameters:**
- `file` (required): CV file (PDF/DOCX, max 10MB)
- `job_requirements` (optional): JSON string with job requirements
- `analysis_options` (optional): JSON string with analysis options

**Example Request:**

```bash
curl -X POST "https://api.cvanalyzer.ai/api/v1/analyze-cv" \
  -H "Authorization: Bearer cvai_your_api_key" \
  -F "file=@resume.pdf" \
  -F 'job_requirements={
    "required_skills": ["Python", "JavaScript", "React"],
    "preferred_skills": ["AWS", "Docker"],
    "minimum_experience": 3,
    "job_description": "Full stack developer position..."
  }' \
  -F 'analysis_options={
    "include_skills_analysis": true,
    "include_experience_analysis": true,
    "include_education_analysis": true,
    "include_job_matching": true,
    "include_scoring": true
  }'
```

**Response:**

```json
{
  "analysis_id": "uuid-string",
  "status": "completed",
  "filename": "resume.pdf",
  "personal_info": {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+1-234-567-8900",
    "location": "New York, NY"
  },
  "skills_analysis": {
    "technical_skills": ["Python", "JavaScript", "React", "Node.js"],
    "soft_skills": ["Leadership", "Communication", "Problem Solving"],
    "skill_categories": {
      "Programming Languages": ["Python", "JavaScript"],
      "Web Technologies": ["React", "Node.js"]
    },
    "total_skills_found": 15
  },
  "experience_analysis": {
    "total_years": 5.5,
    "experience_quality_score": 85.2,
    "keywords_found": ["developed", "managed", "led", "implemented"],
    "experience_level": "Senior"
  },
  "education_analysis": {
    "degrees": ["Bachelor's", "Computer Science"],
    "education_level_score": 80,
    "institutions": ["University of Technology"]
  },
  "overall_score": {
    "overall_score": 82.5,
    "component_scores": {
      "skills": 85.0,
      "experience": 88.0,
      "education": 75.0,
      "quality": 82.0
    },
    "score_grade": "Very Good",
    "percentile_rank": 85
  },
  "job_compatibility": {
    "overall_compatibility": 78.5,
    "skill_compatibility": 85.2,
    "experience_compatibility": 72.0,
    "education_compatibility": 75.0,
    "strengths": ["Strong technical skills", "Relevant experience"],
    "weaknesses": ["Limited AWS experience"],
    "recommendations": ["Gain cloud computing experience"]
  },
  "processing_time_seconds": 3.2,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 2. Batch Analysis

Analyze multiple CV files in a single request.

**Endpoint:** `POST /batch-analyze`

**Parameters:**
- `files` (required): Multiple CV files
- `job_requirements` (optional): Same as single analysis
- `analysis_options` (optional): Same as single analysis

**Example Request:**

```bash
curl -X POST "https://api.cvanalyzer.ai/api/v1/batch-analyze" \
  -H "Authorization: Bearer cvai_your_api_key" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.pdf" \
  -F "files=@resume3.pdf"
```

**Response:**

```json
{
  "batch_id": "batch-uuid-string",
  "total_files": 3,
  "completed": 3,
  "failed": 0,
  "results": [
    {
      "analysis_id": "uuid-1",
      "status": "completed",
      "filename": "resume1.pdf",
      "overall_score": {"overall_score": 85.0},
      "created_at": "2024-01-01T12:00:00Z"
    },
    // ... more results
  ],
  "processing_time_seconds": 8.5
}
```

### 3. Get Analysis Results

Retrieve analysis results by ID.

**Endpoint:** `GET /analysis/{analysis_id}`

**Example Request:**

```bash
curl -X GET "https://api.cvanalyzer.ai/api/v1/analysis/uuid-string" \
  -H "Authorization: Bearer cvai_your_api_key"
```

### 4. Job Matching

Match an existing CV analysis against a specific job.

**Endpoint:** `POST /match-job`

**Parameters:**
- `analysis_id` (required): Existing analysis ID
- `job_description` (required): Job description text
- `required_skills` (required): JSON array or comma-separated skills
- `preferred_skills` (optional): JSON array or comma-separated skills
- `minimum_experience` (optional): Minimum years of experience

**Example Request:**

```bash
curl -X POST "https://api.cvanalyzer.ai/api/v1/match-job" \
  -H "Authorization: Bearer cvai_your_api_key" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "analysis_id=uuid-string" \
  -d "job_description=Senior Python developer position..." \
  -d 'required_skills=["Python", "Django", "PostgreSQL"]' \
  -d 'preferred_skills=["AWS", "Docker"]' \
  -d "minimum_experience=5"
```

## Dashboard Endpoints

### User Statistics

**Endpoint:** `GET /dashboard/stats`

```bash
curl -X GET "https://api.cvanalyzer.ai/api/v1/dashboard/stats" \
  -H "Authorization: Bearer your_access_token"
```

### Analytics

**Endpoint:** `GET /dashboard/analytics`

**Parameters:**
- `period` (optional): 7d, 30d, 90d, or 1y (default: 30d)

### API Usage

**Endpoint:** `GET /dashboard/api-usage`

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing API key)
- `413` - Payload Too Large (file size limit exceeded)
- `422` - Unprocessable Entity (validation errors)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

**Error Response Format:**

```json
{
  "error": "Error description",
  "status_code": 400,
  "details": {
    "field": "Specific validation error"
  }
}
```

## Rate Limits

API requests are rate limited per API key:

- **Basic**: 100 requests/minute, 1,000 requests/hour
- **Premium**: 500 requests/minute, 5,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## File Requirements

### Supported Formats
- PDF (.pdf)
- Microsoft Word (.doc, .docx)

### File Size Limits
- Maximum: 10MB per file
- Batch processing: Up to 50 files

### Content Requirements
- Minimum 50 words
- Must contain readable text (not just images)

## Analysis Options

Customize analysis by setting these options:

```json
{
  "include_skills_analysis": true,      // Extract and categorize skills
  "include_experience_analysis": true,  // Analyze work experience
  "include_education_analysis": true,   // Assess education background
  "include_job_matching": false,        // Match against job requirements
  "include_scoring": true               // Calculate overall scores
}
```

## Webhooks (Coming Soon)

Configure webhooks to receive notifications when analysis is complete:

```json
{
  "webhook_url": "https://your-app.com/cv-analysis-webhook",
  "events": ["analysis.completed", "batch.completed"]
}
```

## SDKs and Libraries

Official SDKs available for:
- Python: `pip install cvanalyzer-python`
- JavaScript/Node.js: `npm install cvanalyzer-js`
- PHP: `composer require cvanalyzer/php-sdk`

## Support

- **Documentation**: https://docs.cvanalyzer.ai
- **Status Page**: https://status.cvanalyzer.ai
- **Support Email**: support@cvanalyzer.ai
- **Response Time**: < 24 hours for technical issues