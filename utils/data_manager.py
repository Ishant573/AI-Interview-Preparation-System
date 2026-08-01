"""
Data Manager - Handles SQLite database operations for interview data persistence
Stores user profiles, interview sessions, answers, and performance analytics
"""
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import Config

class DataManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Resume profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_name TEXT,
                skills TEXT,
                experience_years REAL,
                education TEXT,
                suggested_titles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Interview sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_role TEXT,
                total_questions INTEGER,
                questions_answered INTEGER,
                overall_score REAL,
                grade TEXT,
                status TEXT DEFAULT 'in_progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Interview answers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                question_id INTEGER,
                question_text TEXT,
                question_type TEXT,
                category TEXT,
                difficulty TEXT,
                answer_text TEXT,
                answer_duration REAL,
                communication_score REAL,
                technical_score REAL,
                confidence_score REAL,
                relevance_score REAL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
            )
        ''')
        
        # Performance analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id INTEGER,
                avg_communication_score REAL,
                avg_technical_score REAL,
                avg_confidence_score REAL,
                avg_relevance_score REAL,
                strengths TEXT,
                areas_for_improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # User operations
    def create_user(self, name: str, email: str = None) -> int:
        """Create a new user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            (name, email)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    # Resume profile operations
    def save_resume_profile(self, user_id: int, file_name: str, profile: Dict) -> int:
        """Save resume analysis results"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO resume_profiles 
               (user_id, file_name, skills, experience_years, education, suggested_titles) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                user_id,
                file_name,
                json.dumps(profile.get('skills', [])),
                profile.get('experience_years', 0),
                json.dumps(profile.get('education', [])),
                json.dumps(profile.get('suggested_titles', []))
            )
        )
        conn.commit()
        profile_id = cursor.lastrowid
        conn.close()
        return profile_id
    
    def get_latest_profile(self, user_id: int) -> Optional[Dict]:
        """Get the latest resume profile for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM resume_profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
            (user_id,)
        )
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            profile = dict(profile)
            profile['skills'] = json.loads(profile['skills'])
            profile['education'] = json.loads(profile['education'])
            profile['suggested_titles'] = json.loads(profile['suggested_titles'])
            return profile
        return None
    
    # Interview session operations
    def create_session(self, user_id: int, job_role: str = "", 
                      total_questions: int = 10) -> int:
        """Create a new interview session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO interview_sessions 
               (user_id, job_role, total_questions, status) 
               VALUES (?, ?, ?, 'in_progress')''',
            (user_id, job_role, total_questions)
        )
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        return session_id
    
    def update_session_score(self, session_id: int, score: float, grade: str):
        """Update session with final score"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''UPDATE interview_sessions SET 
               overall_score = ?, grade = ?, status = 'completed', 
               completed_at = CURRENT_TIMESTAMP 
               WHERE id = ?''',
            (score, grade, session_id)
        )
        conn.commit()
        conn.close()
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get interview session details"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM interview_sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        conn.close()
        return dict(session) if session else None
    
    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get all sessions for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM interview_sessions WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sessions
    
    # Answer operations
    def save_answer(self, session_id: int, question: Dict, answer_data: Dict,
                    scores: Dict) -> int:
        """Save an interview answer with scores"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO interview_answers 
               (session_id, question_id, question_text, question_type, category, difficulty,
                answer_text, answer_duration, communication_score, technical_score,
                confidence_score, relevance_score, feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                session_id,
                question.get('id', 0),
                question.get('question', ''),
                question.get('type', 'general'),
                question.get('category', ''),
                question.get('difficulty', 'medium'),
                answer_data.get('text', ''),
                answer_data.get('duration', 0),
                scores.get('communication', {}).get('score', 0),
                scores.get('technical_accuracy', {}).get('score', 0),
                scores.get('confidence', {}).get('score', 0),
                scores.get('relevance', {}).get('score', 0),
                json.dumps(scores.get('feedback', ''))
            )
        )
        conn.commit()
        answer_id = cursor.lastrowid
        
        # Update questions answered count
        cursor.execute(
            'UPDATE interview_sessions SET questions_answered = COALESCE(questions_answered, 0) + 1 WHERE id = ?',
            (session_id,)
        )
        conn.commit()
        conn.close()
        return answer_id
    
    def get_session_answers(self, session_id: int) -> List[Dict]:
        """Get all answers for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM interview_answers WHERE session_id = ? ORDER BY question_id',
            (session_id,)
        )
        answers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return answers
    
    # Analytics operations
    def save_analytics(self, user_id: int, session_id: int, 
                      avg_scores: Dict, overall: Dict) -> int:
        """Save performance analytics"""
        # Determine strengths and areas for improvement
        strengths = []
        improvements = []
        
        for category, score in avg_scores.items():
            if score >= 7:
                strengths.append(category)
            elif score < 5:
                improvements.append(category)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO performance_analytics 
               (user_id, session_id, avg_communication_score, avg_technical_score,
                avg_confidence_score, avg_relevance_score, strengths, areas_for_improvement)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                user_id, session_id,
                avg_scores.get('communication', 0),
                avg_scores.get('technical_accuracy', 0),
                avg_scores.get('confidence', 0),
                avg_scores.get('relevance', 0),
                json.dumps(strengths),
                json.dumps(improvements)
            )
        )
        conn.commit()
        analytics_id = cursor.lastrowid
        conn.close()
        return analytics_id
    
    def get_user_analytics(self, user_id: int) -> List[Dict]:
        """Get all analytics for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT * FROM performance_analytics 
               WHERE user_id = ? ORDER BY created_at DESC''',
            (user_id,)
        )
        analytics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        for entry in analytics:
            entry['strengths'] = json.loads(entry['strengths'])
            entry['areas_for_improvement'] = json.loads(entry['areas_for_improvement'])
        
        return analytics
    
    def get_user_performance_trend(self, user_id: int) -> Dict:
        """Get performance trend data across all sessions"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT overall_score, grade, created_at FROM interview_sessions 
               WHERE user_id = ? AND status = 'completed' 
               ORDER BY created_at ASC''',
            (user_id,)
        )
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not sessions:
            return {'sessions_count': 0, 'scores': [], 'trend': 'no_data'}
        
        scores = [s['overall_score'] for s in sessions if s['overall_score']]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate trend
        if len(scores) >= 2:
            if scores[-1] > scores[0]:
                trend = 'improving'
            elif scores[-1] < scores[0]:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'sessions_count': len(sessions),
            'scores': scores,
            'average_score': round(average_score, 1),
            'trend': trend,
            'sessions': sessions
        }


def get_data_manager() -> DataManager:
    """Get singleton data manager instance"""
    return DataManager()
