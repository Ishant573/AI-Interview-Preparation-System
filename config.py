"""
Configuration file for AI Interview Preparation System
"""
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# Detect Vercel or other serverless/lambda environment
IS_SERVERLESS = (
    os.getenv('VERCEL') == '1'
    or 'VERCEL' in os.environ
    or os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if IS_SERVERLESS:
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    DATABASE_PATH = os.getenv('DATABASE_PATH', '/tmp/interviews.db')
    
    # Pre-seed SQLite database to /tmp if local DB exists and /tmp DB doesn't exist yet
    default_db = os.path.join(BASE_DIR, 'data', 'interviews.db')
    if os.path.exists(default_db) and not os.path.exists(DATABASE_PATH):
        try:
            os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
            shutil.copyfile(default_db, DATABASE_PATH)
        except Exception:
            pass
else:
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'interviews.db'))

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'ai-interview-secret-key-2024')
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')  # or 'gpt-3.5-turbo' for lower cost
    
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
    DATABASE_PATH = DATABASE_PATH
    IS_SERVERLESS = IS_SERVERLESS

