"""
Skill Classification ML Model
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from typing import List, Dict, Tuple, Any
import pickle
import logging
import os

logger = logging.getLogger(__name__)


class SkillClassifier:
    """ML model for classifying and categorizing skills from CV text"""
    
    def __init__(self, model_path: str = None):
        """Initialize skill classifier"""
        self.model = None
        self.categories = [
            "Programming Languages",
            "Web Technologies", 
            "Databases",
            "Cloud & DevOps",
            "Data Science & ML",
            "Mobile Development",
            "Tools & Others"
        ]
        self.model_path = model_path or "models/skill_classifier.pkl"
        
        # Pre-defined skill-to-category mapping for training
        self.skill_category_mapping = self._initialize_skill_mapping()
        
    def _initialize_skill_mapping(self) -> Dict[str, str]:
        """Initialize skill-to-category mapping for training"""
        return {
            # Programming Languages
            "python": "Programming Languages",
            "java": "Programming Languages", 
            "javascript": "Programming Languages",
            "typescript": "Programming Languages",
            "c++": "Programming Languages",
            "c#": "Programming Languages",
            "php": "Programming Languages",
            "ruby": "Programming Languages",
            "go": "Programming Languages",
            "rust": "Programming Languages",
            "swift": "Programming Languages",
            "kotlin": "Programming Languages",
            "scala": "Programming Languages",
            "r": "Programming Languages",
            
            # Web Technologies
            "html": "Web Technologies",
            "css": "Web Technologies",
            "react": "Web Technologies",
            "angular": "Web Technologies",
            "vue": "Web Technologies",
            "node.js": "Web Technologies",
            "express": "Web Technologies",
            "django": "Web Technologies",
            "flask": "Web Technologies",
            "spring": "Web Technologies",
            "laravel": "Web Technologies",
            "bootstrap": "Web Technologies",
            "jquery": "Web Technologies",
            
            # Databases
            "mysql": "Databases",
            "postgresql": "Databases",
            "mongodb": "Databases",
            "redis": "Databases",
            "elasticsearch": "Databases",
            "oracle": "Databases",
            "sql server": "Databases",
            "sqlite": "Databases",
            "cassandra": "Databases",
            "dynamodb": "Databases",
            
            # Cloud & DevOps
            "aws": "Cloud & DevOps",
            "azure": "Cloud & DevOps",
            "google cloud": "Cloud & DevOps",
            "docker": "Cloud & DevOps",
            "kubernetes": "Cloud & DevOps",
            "jenkins": "Cloud & DevOps",
            "terraform": "Cloud & DevOps",
            "ansible": "Cloud & DevOps",
            "gitlab": "Cloud & DevOps",
            "github": "Cloud & DevOps",
            
            # Data Science & ML
            "machine learning": "Data Science & ML",
            "deep learning": "Data Science & ML",
            "artificial intelligence": "Data Science & ML",
            "data science": "Data Science & ML",
            "pandas": "Data Science & ML",
            "numpy": "Data Science & ML",
            "scikit-learn": "Data Science & ML",
            "tensorflow": "Data Science & ML",
            "pytorch": "Data Science & ML",
            "keras": "Data Science & ML",
            
            # Mobile Development
            "ios": "Mobile Development",
            "android": "Mobile Development",
            "react native": "Mobile Development",
            "flutter": "Mobile Development",
            "xamarin": "Mobile Development",
            "ionic": "Mobile Development",
            
            # Tools & Others
            "git": "Tools & Others",
            "jira": "Tools & Others",
            "confluence": "Tools & Others",
            "slack": "Tools & Others",
            "agile": "Tools & Others",
            "scrum": "Tools & Others",
            "rest api": "Tools & Others",
            "graphql": "Tools & Others"
        }
    
    def train_model(self) -> None:
        """Train the skill classification model"""
        try:
            logger.info("Training skill classification model...")
            
            # Prepare training data
            X, y = self._prepare_training_data()
            
            if len(X) < 10:
                logger.warning("Insufficient training data, using rule-based classification")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Create pipeline
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=1000,
                    ngram_range=(1, 2),
                    lowercase=True,
                    stop_words='english'
                )),
                ('classifier', MultinomialNB(alpha=0.1))
            ])
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            logger.info(f"Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
            
            # Save model
            self.save_model()
            
        except Exception as e:
            logger.error(f"Error training skill classification model: {str(e)}")
    
    def _prepare_training_data(self) -> Tuple[List[str], List[str]]:
        """Prepare training data from skill mappings"""
        X = []
        y = []
        
        # Use skill names as features and categories as labels
        for skill, category in self.skill_category_mapping.items():
            # Add the skill itself
            X.append(skill)
            y.append(category)
            
            # Add some variations and context
            variations = [
                f"{skill} programming",
                f"{skill} development",
                f"experience with {skill}",
                f"{skill} framework",
                f"{skill} technology"
            ]
            
            for variation in variations:
                X.append(variation)
                y.append(category)
        
        return X, y
    
    def classify_skill(self, skill_text: str) -> str:
        """
        Classify a skill into a category
        
        Args:
            skill_text: Skill name or description
            
        Returns:
            Category name
        """
        try:
            skill_lower = skill_text.lower().strip()
            
            # First try exact match
            if skill_lower in self.skill_category_mapping:
                return self.skill_category_mapping[skill_lower]
            
            # Try partial matches
            for skill, category in self.skill_category_mapping.items():
                if skill in skill_lower or skill_lower in skill:
                    return category
            
            # Use ML model if available
            if self.model:
                try:
                    prediction = self.model.predict([skill_text])[0]
                    return prediction
                except Exception:
                    pass
            
            # Default category
            return "Tools & Others"
            
        except Exception as e:
            logger.error(f"Error classifying skill '{skill_text}': {str(e)}")
            return "Tools & Others"
    
    def classify_skills_batch(self, skills: List[str]) -> Dict[str, str]:
        """
        Classify multiple skills at once
        
        Args:
            skills: List of skill names
            
        Returns:
            Dictionary mapping skills to categories
        """
        results = {}
        
        for skill in skills:
            results[skill] = self.classify_skill(skill)
        
        return results
    
    def get_category_distribution(self, skills: List[str]) -> Dict[str, int]:
        """
        Get distribution of skills across categories
        
        Args:
            skills: List of skill names
            
        Returns:
            Dictionary with category counts
        """
        classification_results = self.classify_skills_batch(skills)
        
        distribution = {category: 0 for category in self.categories}
        
        for skill, category in classification_results.items():
            if category in distribution:
                distribution[category] += 1
            else:
                distribution["Tools & Others"] += 1
        
        return distribution
    
    def extract_and_classify_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract and classify skills from text
        
        Args:
            text: Input text (CV content)
            
        Returns:
            Dictionary with skills organized by category
        """
        try:
            # Extract potential skills from text
            potential_skills = self._extract_skills_from_text(text)
            
            # Classify skills
            categorized_skills = {category: [] for category in self.categories}
            
            for skill in potential_skills:
                category = self.classify_skill(skill)
                if category in categorized_skills:
                    categorized_skills[category].append(skill)
                else:
                    categorized_skills["Tools & Others"].append(skill)
            
            # Remove empty categories
            return {cat: skills for cat, skills in categorized_skills.items() if skills}
            
        except Exception as e:
            logger.error(f"Error extracting and classifying skills: {str(e)}")
            return {}
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract potential skills from text using keyword matching"""
        text_lower = text.lower()
        found_skills = []
        
        # Check for each known skill in the text
        for skill in self.skill_category_mapping.keys():
            if len(skill) > 2:  # Avoid very short matches
                # Look for word boundaries to avoid partial matches
                import re
                pattern = r'\\b' + re.escape(skill.lower()) + r'\\b'
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def save_model(self) -> None:
        """Save trained model to disk"""
        try:
            if self.model is None:
                logger.warning("No model to save")
                return
            
            # Create models directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save model
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self) -> bool:
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info(f"Model loaded from {self.model_path}")
                return True
            else:
                logger.info("No saved model found, will use rule-based classification")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "model_type": "Skill Classifier",
            "categories": self.categories,
            "known_skills": len(self.skill_category_mapping),
            "has_trained_model": self.model is not None,
            "model_path": self.model_path
        }