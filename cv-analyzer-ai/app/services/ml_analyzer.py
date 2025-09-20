"""
ML Analyzer Service for NLP processing and analysis
"""

import spacy
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import re

logger = logging.getLogger(__name__)


class MLAnalyzer:
    """Machine Learning analyzer for CV content processing"""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize ML analyzer with spaCy model"""
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"Could not load {model_name}, using blank English model")
            self.nlp = spacy.blank("en")
        
        # Initialize skill categories
        self.skill_categories = self._initialize_skill_categories()
        self.experience_keywords = self._initialize_experience_keywords()
        
    async def analyze_cv_content(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive ML analysis on CV content
        
        Args:
            cv_data: Parsed CV data from CV parser
            
        Returns:
            Analysis results dictionary
        """
        try:
            text = cv_data.get("raw_text", "")
            if not text:
                raise ValueError("No text content found in CV data")
            
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Perform various analyses
            analysis_results = {
                "named_entities": self._extract_named_entities(doc),
                "skills_analysis": await self._analyze_skills(text, doc),
                "experience_analysis": await self._analyze_experience(cv_data.get("structured_sections", {}), doc),
                "education_analysis": await self._analyze_education(cv_data.get("structured_sections", {}), doc),
                "language_analysis": self._analyze_language_proficiency(text),
                "text_quality": self._assess_text_quality(doc),
                "sentiment_analysis": self._analyze_sentiment(doc)
            }
            
            logger.info("CV content analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in CV content analysis: {str(e)}")
            raise
    
    def _extract_named_entities(self, doc: spacy.tokens.Doc) -> Dict[str, List[str]]:
        """Extract named entities from CV text"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "technologies": [],
            "dates": [],
            "other": []
        }
        
        for ent in doc.ents:
            entity_text = ent.text.strip()
            if len(entity_text) < 2:  # Skip very short entities
                continue
                
            if ent.label_ in ["PERSON"]:
                entities["persons"].append(entity_text)
            elif ent.label_ in ["ORG"]:
                entities["organizations"].append(entity_text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(entity_text)
            elif ent.label_ in ["DATE", "TIME"]:
                entities["dates"].append(entity_text)
            else:
                entities["other"].append(f"{entity_text} ({ent.label_})")
        
        # Remove duplicates and sort
        for category in entities:
            entities[category] = sorted(list(set(entities[category])))
        
        return entities
    
    async def _analyze_skills(self, text: str, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Analyze and categorize skills from CV"""
        skills_analysis = {
            "technical_skills": [],
            "soft_skills": [],
            "skill_categories": {},
            "skill_frequency": {},
            "total_skills_found": 0
        }
        
        text_lower = text.lower()
        
        # Find technical skills
        for category, skills_list in self.skill_categories.items():
            found_skills = []
            for skill in skills_list:
                skill_lower = skill.lower()
                # Count occurrences of each skill
                count = len(re.findall(rf"\\b{re.escape(skill_lower)}\\b", text_lower))
                if count > 0:
                    found_skills.append(skill)
                    skills_analysis["skill_frequency"][skill] = count
            
            if found_skills:
                skills_analysis["skill_categories"][category] = found_skills
                skills_analysis["technical_skills"].extend(found_skills)
        
        # Find soft skills
        soft_skills_keywords = [
            "leadership", "communication", "teamwork", "problem solving", "creativity",
            "analytical", "detail-oriented", "organized", "motivated", "adaptable",
            "collaborative", "innovative", "strategic", "customer service", "presentation",
            "negotiation", "time management", "project management", "critical thinking"
        ]
        
        for skill in soft_skills_keywords:
            if skill.lower() in text_lower:
                skills_analysis["soft_skills"].append(skill)
                skills_analysis["skill_frequency"][skill] = len(re.findall(rf"\\b{re.escape(skill.lower())}\\b", text_lower))
        
        skills_analysis["total_skills_found"] = len(set(skills_analysis["technical_skills"] + skills_analysis["soft_skills"]))
        
        return skills_analysis
    
    async def _analyze_experience(self, sections: Dict[str, str], doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Analyze work experience from CV"""
        experience_text = sections.get("experience", "")
        
        experience_analysis = {
            "total_years": 0.0,
            "experience_entries": [],
            "job_titles": [],
            "companies": [],
            "experience_quality_score": 0.0,
            "keywords_found": []
        }
        
        if not experience_text:
            return experience_analysis
        
        # Extract years of experience
        years_patterns = [
            r"(\\d+)\\+?\\s*years?\\s*(?:of\\s*)?experience",
            r"(\\d+)\\s*-\\s*(\\d+)\\s*years?",
            r"over\\s+(\\d+)\\s*years?",
            r"(\\d+)\\s*years?\\s*in",
        ]
        
        total_years = 0
        for pattern in years_patterns:
            matches = re.findall(pattern, experience_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Range pattern (e.g., "5-7 years")
                    years = sum(int(x) for x in match if x.isdigit()) / len(match)
                else:
                    years = int(match)
                total_years = max(total_years, years)
        
        experience_analysis["total_years"] = float(total_years)
        
        # Find experience-related keywords
        for keyword in self.experience_keywords:
            if keyword.lower() in experience_text.lower():
                experience_analysis["keywords_found"].append(keyword)
        
        # Calculate experience quality score based on keywords and structure
        quality_score = min(100, len(experience_analysis["keywords_found"]) * 5 + 
                          (50 if total_years > 0 else 0))
        experience_analysis["experience_quality_score"] = quality_score
        
        return experience_analysis
    
    async def _analyze_education(self, sections: Dict[str, str], doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Analyze education background from CV"""
        education_text = sections.get("education", "")
        
        education_analysis = {
            "degrees": [],
            "institutions": [],
            "education_level_score": 0,
            "relevant_coursework": [],
            "certifications": []
        }
        
        if not education_text:
            return education_analysis
        
        # Common degree patterns
        degree_patterns = [
            r"\\b(?:bachelor|master|phd|doctorate|mba|bs|ms|ba|ma|bsc|msc)\\b",
            r"\\b(?:degree|diploma|certificate)\\b"
        ]
        
        degrees_found = []
        for pattern in degree_patterns:
            matches = re.findall(pattern, education_text, re.IGNORECASE)
            degrees_found.extend(matches)
        
        education_analysis["degrees"] = list(set(degrees_found))
        
        # Score education level
        education_score = 0
        if any("phd" in degree.lower() or "doctorate" in degree.lower() for degree in degrees_found):
            education_score = 100
        elif any("master" in degree.lower() or "mba" in degree.lower() or "ms" in degree.lower() 
                or "ma" in degree.lower() for degree in degrees_found):
            education_score = 80
        elif any("bachelor" in degree.lower() or "bs" in degree.lower() or "ba" in degree.lower() 
                for degree in degrees_found):
            education_score = 60
        elif degrees_found:
            education_score = 40
        
        education_analysis["education_level_score"] = education_score
        
        return education_analysis
    
    def _analyze_language_proficiency(self, text: str) -> Dict[str, Any]:
        """Analyze language skills and proficiency"""
        language_analysis = {
            "languages": [],
            "proficiency_levels": {},
            "total_languages": 0
        }
        
        # Common languages
        languages = [
            "english", "spanish", "french", "german", "italian", "portuguese", "russian",
            "chinese", "japanese", "korean", "arabic", "hindi", "dutch", "swedish",
            "norwegian", "danish", "finnish", "polish", "turkish", "greek"
        ]
        
        proficiency_levels = ["native", "fluent", "advanced", "intermediate", "basic", "conversational"]
        
        text_lower = text.lower()
        
        for language in languages:
            if language in text_lower:
                language_analysis["languages"].append(language.title())
                
                # Look for proficiency level near the language mention
                context_start = max(0, text_lower.find(language) - 50)
                context_end = min(len(text_lower), text_lower.find(language) + 50)
                context = text_lower[context_start:context_end]
                
                proficiency = "intermediate"  # default
                for level in proficiency_levels:
                    if level in context:
                        proficiency = level
                        break
                
                language_analysis["proficiency_levels"][language.title()] = proficiency
        
        language_analysis["total_languages"] = len(language_analysis["languages"])
        
        return language_analysis
    
    def _assess_text_quality(self, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Assess the quality of CV text"""
        quality_analysis = {
            "word_count": len([token for token in doc if not token.is_space]),
            "sentence_count": len(list(doc.sents)),
            "average_sentence_length": 0.0,
            "readability_score": 0.0,
            "grammar_issues": 0,
            "quality_score": 0.0
        }
        
        sentences = list(doc.sents)
        if sentences:
            quality_analysis["average_sentence_length"] = quality_analysis["word_count"] / len(sentences)
        
        # Simple readability assessment
        avg_sentence_length = quality_analysis["average_sentence_length"]
        readability = 100 - (avg_sentence_length - 15) * 2 if avg_sentence_length > 15 else 100
        quality_analysis["readability_score"] = max(0, min(100, readability))
        
        # Overall quality score
        word_count_score = min(100, quality_analysis["word_count"] / 10)  # 1000 words = 100 points
        sentence_variety_score = min(100, len(sentences))  # More sentences = better structure
        
        quality_analysis["quality_score"] = (word_count_score + sentence_variety_score + 
                                           quality_analysis["readability_score"]) / 3
        
        return quality_analysis
    
    def _analyze_sentiment(self, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Basic sentiment analysis of CV content"""
        # Simple keyword-based sentiment analysis
        positive_keywords = [
            "achieved", "successful", "improved", "increased", "developed", "created",
            "led", "managed", "delivered", "award", "excellent", "outstanding"
        ]
        
        negative_keywords = [
            "failed", "decreased", "problem", "issue", "difficulty", "challenge"
        ]
        
        text = doc.text.lower()
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        sentiment_score = positive_count - negative_count
        
        if sentiment_score > 2:
            sentiment = "positive"
        elif sentiment_score < -1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "positive_keywords": positive_count,
            "negative_keywords": negative_count,
            "sentiment_score": sentiment_score
        }
    
    def _initialize_skill_categories(self) -> Dict[str, List[str]]:
        """Initialize categorized technical skills"""
        return {
            "Programming Languages": [
                "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby",
                "Go", "Rust", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Shell", "Bash"
            ],
            "Web Technologies": [
                "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
                "Django", "Flask", "Spring", "Laravel", "Ruby on Rails", "ASP.NET",
                "jQuery", "Bootstrap", "Sass", "Less", "Webpack", "Next.js", "Nuxt.js"
            ],
            "Databases": [
                "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Oracle",
                "SQL Server", "SQLite", "Cassandra", "DynamoDB", "Neo4j", "InfluxDB"
            ],
            "Cloud & DevOps": [
                "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
                "GitLab CI", "GitHub Actions", "Terraform", "Ansible", "Chef", "Puppet",
                "Vagrant", "Nginx", "Apache", "Linux", "Ubuntu", "CentOS"
            ],
            "Data Science & ML": [
                "Machine Learning", "Deep Learning", "Artificial Intelligence", "Data Science",
                "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
                "Jupyter", "Matplotlib", "Seaborn", "Plotly", "Apache Spark", "Hadoop"
            ],
            "Mobile Development": [
                "iOS", "Android", "React Native", "Flutter", "Xamarin", "Ionic",
                "Objective-C", "Swift", "Java", "Kotlin"
            ],
            "Tools & Others": [
                "Git", "SVN", "JIRA", "Confluence", "Slack", "Teams", "Agile", "Scrum",
                "Kanban", "REST API", "GraphQL", "Microservices", "Unit Testing",
                "Integration Testing", "CI/CD", "Monitoring", "Logging"
            ]
        }
    
    def _initialize_experience_keywords(self) -> List[str]:
        """Initialize experience-related keywords"""
        return [
            "developed", "implemented", "designed", "created", "built", "managed",
            "led", "supervised", "coordinated", "collaborated", "achieved", "delivered",
            "improved", "optimized", "increased", "reduced", "streamlined", "automated",
            "maintained", "supported", "troubleshooted", "debugged", "tested", "deployed",
            "integrated", "migrated", "refactored", "architected", "planned", "executed",
            "analyzed", "researched", "evaluated", "recommended", "presented", "trained",
            "mentored", "recruited", "onboarded", "documented", "standardized"
        ]