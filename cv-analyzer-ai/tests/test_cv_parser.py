"""
Basic tests for CV parser service
"""

import pytest
import io
from unittest.mock import patch, MagicMock
from app.services.cv_parser import CVParser


@pytest.fixture
def cv_parser():
    """Create CVParser instance for testing"""
    return CVParser()


@pytest.mark.asyncio
async def test_parse_cv_pdf(cv_parser):
    """Test parsing PDF CV"""
    # Mock PDF content
    mock_pdf_content = b"%PDF-1.4 mock pdf content"
    filename = "test_resume.pdf"
    
    with patch('app.services.cv_parser.pdfplumber.open') as mock_pdf_open:
        # Mock PDF structure
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\nPython, JavaScript"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        # Test parsing
        result = await cv_parser.parse_cv(mock_pdf_content, filename)
        
        # Assertions
        assert result["filename"] == filename
        assert result["file_type"] == "pdf"
        assert "raw_text" in result
        assert "structured_sections" in result
        assert "contact_info" in result
        assert result["total_pages"] == 1


@pytest.mark.asyncio
async def test_parse_cv_unsupported_format(cv_parser):
    """Test parsing unsupported file format"""
    mock_content = b"some content"
    filename = "test_file.txt"
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        await cv_parser.parse_cv(mock_content, filename)


def test_extract_contact_info(cv_parser):
    """Test contact information extraction"""
    text = """
    John Doe
    john.doe@email.com
    +1-234-567-8900
    New York, NY
    linkedin.com/in/johndoe
    """
    
    contact_info = cv_parser._extract_contact_info(text)
    
    assert "john.doe@email.com" in contact_info["email"]
    assert contact_info["linkedin"] == "linkedin.com/in/johndoe"
    assert contact_info["name"] is not None


def test_extract_sections(cv_parser):
    """Test CV section extraction"""
    text = """
    EXPERIENCE:
    Software Engineer at Company ABC
    Developed web applications using Python and Django
    
    EDUCATION:
    Bachelor of Science in Computer Science
    University of Technology, 2020
    
    SKILLS:
    Python, JavaScript, React, SQL
    """
    
    sections = cv_parser._extract_sections(text)
    
    assert "experience" in sections
    assert "education" in sections  
    assert "skills" in sections
    assert "Software Engineer" in sections["experience"]
    assert "Bachelor" in sections["education"]


def test_extract_skills_keywords(cv_parser):
    """Test skill keyword extraction"""
    text = "I have experience with Python, JavaScript, React, and AWS cloud services."
    
    skills = cv_parser.extract_skills_keywords(text)
    
    expected_skills = ["python", "javascript", "react", "aws"]
    for skill in expected_skills:
        assert skill in skills


@pytest.mark.asyncio
async def test_parse_cv_with_empty_content(cv_parser):
    """Test parsing with empty content"""
    with patch('app.services.cv_parser.pdfplumber.open') as mock_pdf_open:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        result = await cv_parser.parse_cv(b"mock content", "empty.pdf")
        
        assert result["raw_text"] is not None
        assert result["structured_sections"] == {}


def test_supported_formats(cv_parser):
    """Test supported file formats"""
    assert '.pdf' in cv_parser.supported_formats
    assert '.doc' in cv_parser.supported_formats
    assert '.docx' in cv_parser.supported_formats