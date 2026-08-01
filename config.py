"""
Configuration file for AI Interview Preparation System
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'ai-interview-secret-key-2024')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE')
    OPENAI_MODEL = 'gpt-4'  # or 'gpt-3.5-turbo' for lower cost
    
    # Application Settings
    APP_NAME = 'AI Interview Preparation System'
    APP_VERSION = '1.0.0'
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # Interview Settings
    MAX_QUESTIONS_PER_SESSION = 10
    QUESTION_TIME_LIMIT = 120  # seconds per question
    MIN_ANSWER_LENGTH = 10  # minimum words for valid answer
    
    # Scoring Weights
    WEIGHTS = {
        'technical_accuracy': 0.30,
        'communication': 0.25,
        'confidence': 0.20,
        'relevance': 0.15,
        'clarity': 0.10
    }
    
    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'interviews.db')
