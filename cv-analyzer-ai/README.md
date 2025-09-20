# CV Analyzer AI

AI-powered CV analysis system that provides comprehensive resume screening and job matching capabilities through REST API endpoints.

## Features

- **CV Parsing**: Extract content from PDF and DOCX files
- **AI Analysis**: NLP-powered skills extraction, experience analysis, and education assessment
- **Job Matching**: Match CVs against specific job requirements with compatibility scoring
- **Batch Processing**: Analyze multiple CVs simultaneously
- **API Authentication**: Secure API key-based authentication with rate limiting
- **Dashboard Analytics**: Usage statistics and performance metrics
- **Comprehensive Scoring**: Overall CV scoring with detailed breakdowns

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd cv-analyzer-ai
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services:
```bash
docker-compose up -d
```

4. The API will be available at `http://localhost:8000`

### Manual Installation

1. Install Python 3.12+ and dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. Set up PostgreSQL database and update `DATABASE_URL` in settings

3. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## Key Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/api-keys` - Create API key

### CV Analysis
- `POST /api/v1/analyze-cv` - Analyze single CV
- `POST /api/v1/batch-analyze` - Batch analyze multiple CVs
- `GET /api/v1/analysis/{id}` - Get analysis results
- `POST /api/v1/match-job` - Match CV against job description

### Dashboard
- `GET /api/v1/dashboard/stats` - User statistics
- `GET /api/v1/dashboard/analytics` - Detailed analytics
- `GET /api/v1/dashboard/api-usage` - API usage metrics

## Usage Example

```python
import requests

# Register user and create API key
response = requests.post('http://localhost:8000/api/v1/auth/register', json={
    "username": "testuser",
    "email": "test@example.com", 
    "password": "password123"
})

# Login to get access token
login_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    "username": "testuser",
    "password": "password123"
})
token = login_response.json()['access_token']

# Create API key
api_key_response = requests.post(
    'http://localhost:8000/api/v1/auth/api-keys',
    headers={'Authorization': f'Bearer {token}'},
    json={"key_name": "My API Key"}
)
api_key = api_key_response.json()['key_value']

# Analyze CV
with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    headers = {'Authorization': f'Bearer {api_key}'}
    
    response = requests.post(
        'http://localhost:8000/api/v1/analyze-cv',
        files=files,
        headers=headers
    )
    
    analysis = response.json()
    print(f"Overall Score: {analysis['overall_score']['overall_score']}")
```

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `REDIS_URL`: Redis connection string (for rate limiting)
- `MAX_FILE_SIZE`: Maximum upload file size (default: 10MB)
- `ALLOWED_FILE_TYPES`: Supported file extensions
- `REQUESTS_PER_MINUTE`: Rate limit per API key

## Architecture

The system consists of several key components:

1. **FastAPI Application** (`main.py`): Main API server
2. **CV Parser** (`app/services/cv_parser.py`): PDF/DOCX content extraction
3. **ML Analyzer** (`app/services/ml_analyzer.py`): NLP processing using spaCy
4. **Skill Matcher** (`app/services/skill_matcher.py`): Job requirement matching
5. **Scoring Engine** (`app/services/scoring_engine.py`): Comprehensive scoring algorithms
6. **ML Models** (`ml_models/`): Specialized ML components for classification and scoring

## Business Model

The system is designed for B2B monetization:

- **API-based Access**: Companies integrate via REST API
- **Tiered Pricing**: Based on API usage and features
- **Usage Tracking**: Comprehensive analytics for billing
- **Rate Limiting**: Enforced limits per subscription tier
- **White-label Options**: Customizable for enterprise clients

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Linting
flake8 app/

# Type checking
mypy app/
```

### Database Migrations

```bash
alembic upgrade head
```

## Deployment

### Production Checklist

- [ ] Update `SECRET_KEY` to secure random value
- [ ] Configure production database
- [ ] Set up SSL certificates
- [ ] Configure logging and monitoring
- [ ] Set up backup procedures
- [ ] Configure rate limiting and security headers

### Scaling Considerations

- Use load balancer for multiple API instances
- Implement Redis clustering for high availability
- Consider PostgreSQL read replicas for heavy read workloads
- Use cloud storage for uploaded files
- Implement proper logging and monitoring

## License

This project is proprietary software. All rights reserved.

## Support

For technical support and questions:
- Email: support@cvanalyzer.ai
- Documentation: https://docs.cvanalyzer.ai
- Status Page: https://status.cvanalyzer.ai