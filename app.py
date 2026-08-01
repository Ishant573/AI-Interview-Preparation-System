"""
AI Interview Preparation System - Main Flask Application
Handles routing, session management, and API endpoints
"""
import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from config import Config
from utils.resume_analyzer import analyze_resume
from utils.question_generator import generate_interview_questions
from utils.speech_recognition import transcribe_audio, analyze_speech
from utils.scoring import calculate_performance_scores, InterviewScorer
from utils.data_manager import DataManager

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialize data manager
db = DataManager()

# Store active interview sessions in memory
active_sessions = {}

def allowed_file(filename: str) -> bool:
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Landing page with resume upload"""
    return render_template('index.html', 
                         app_name=Config.APP_NAME,
                         version=Config.APP_VERSION)


@app.route('/interview')
def interview():
    """Interview session page"""
    return render_template('interview.html',
                         app_name=Config.APP_NAME)


@app.route('/results')
def results():
    """Interview results page"""
    return render_template('results.html',
                         app_name=Config.APP_NAME)


@app.route('/analytics')
def analytics():
    """Performance analytics page"""
    return render_template('analytics.html',
                         app_name=Config.APP_NAME)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and analyze resume"""
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload PDF, DOCX, or TXT'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
        file.save(filepath)
        
        # Analyze resume
        profile = analyze_resume(filepath)
        
        # Create user session
        if 'user_id' not in session:
            user_id = db.create_user(f"User_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            session['user_id'] = user_id
        else:
            user_id = session['user_id']
        
        # Save profile to database
        db.save_resume_profile(user_id, filename, profile)
        
        return jsonify({
            'success': True,
            'profile': profile,
            'message': 'Resume analyzed successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing resume: {str(e)}'}), 500


@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    data = request.json
    job_role = data.get('job_role', '')
    num_questions = data.get('num_questions', Config.MAX_QUESTIONS_PER_SESSION)
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Please upload your resume first'}), 400
    
    # Get latest resume profile
    profile = db.get_latest_profile(user_id)
    if not profile:
        return jsonify({'error': 'No resume profile found. Please upload your resume.'}), 400
    
    # Build profile dict for question generator
    profile_data = {
        'skills': profile.get('skills', []),
        'experience_years': profile.get('experience_years', 0),
        'education': profile.get('education', []),
        'key_achievements': [],
        'suggested_titles': profile.get('suggested_titles', [])
    }
    
    # Generate questions
    questions = generate_interview_questions(profile_data, job_role, num_questions)
    
    # Create database session
    session_id = db.create_session(user_id, job_role, len(questions))
    
    # Store in active sessions
    active_sessions[session_id] = {
        'questions': questions,
        'current_question': 0,
        'answers': [],
        'job_role': job_role
    }
    
    # Store session_id in flask session
    session['current_session_id'] = session_id
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'questions': questions,
        'total_questions': len(questions),
        'profile': profile_data
    })


@app.route('/api/get-question', methods=['GET'])
def get_question():
    """Get current interview question"""
    session_id = session.get('current_session_id')
    
    if not session_id or session_id not in active_sessions:
        return jsonify({'error': 'No active interview session'}), 400
    
    interview = active_sessions[session_id]
    current_idx = interview['current_question']
    questions = interview['questions']
    
    if current_idx >= len(questions):
        return jsonify({'error': 'Interview completed'}), 400
    
    question = questions[current_idx]
    
    return jsonify({
        'success': True,
        'question': question,
        'question_number': current_idx + 1,
        'total_questions': len(questions),
        'progress': (current_idx / len(questions)) * 100
    })


@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """Submit answer for current question"""
    session_id = session.get('current_session_id')
    
    if not session_id or session_id not in active_sessions:
        return jsonify({'error': 'No active interview session'}), 400
    
    interview = active_sessions[session_id]
    current_idx = interview['current_question']
    questions = interview['questions']
    
    if current_idx >= len(questions):
        return jsonify({'error': 'Interview already completed'}), 400
    
    question = questions[current_idx]
    data = request.json
    answer_text = data.get('answer', '')
    audio_data = data.get('audio', None)  # Base64 encoded audio (optional)
    
    # Analyze speech patterns
    speech_analysis = analyze_speech(answer_text)
    
    # Score the answer
    scorer = InterviewScorer()
    scores = {
        'communication': scorer.score_communication(answer_text, speech_analysis),
        'technical_accuracy': scorer.score_technical_accuracy(answer_text, question),
        'confidence': scorer.score_confidence(answer_text, speech_analysis),
        'relevance': scorer.score_relevance(answer_text, question)
    }
    
    # Calculate overall score for this question
    overall = scorer.calculate_overall_score(
        {k: v['score'] for k, v in scores.items() if isinstance(v, dict)}
    )
    scores['overall'] = overall
    
    # Prepare answer data
    answer_data = {
        'text': answer_text,
        'speech_analysis': speech_analysis,
        'duration': 0
    }
    
    # Save to database
    db.save_answer(session_id, question, answer_data, scores)
    
    # Store in session
    interview['answers'].append({
        'question': question,
        'answer': answer_data,
        'scores': scores
    })
    
    # Move to next question
    interview['current_question'] += 1
    
    # Check if interview is complete
    is_complete = interview['current_question'] >= len(questions)
    
    if is_complete:
        # Calculate final scores
        all_scores = calculate_performance_scores(
            [a['answer'] for a in interview['answers']],
            questions
        )
        
        # Update session with final score
        db.update_session_score(
            session_id,
            all_scores['overall']['overall_score'],
            all_scores['overall']['grade']
        )
        
        # Save analytics
        db.save_analytics(
            session.get('user_id'),
            session_id,
            all_scores['average_scores'],
            all_scores['overall']
        )
        
        # Store final results
        interview['final_results'] = all_scores
    
    return jsonify({
        'success': True,
        'scores': scores,
        'speech_analysis': speech_analysis,
        'is_complete': is_complete,
        'next_question': None if is_complete else interview['questions'][interview['current_question']]
    })


@app.route('/api/get-results', methods=['GET'])
def get_results():
    """Get interview results"""
    session_id = session.get('current_session_id')
    
    if not session_id or session_id not in active_sessions:
        return jsonify({'error': 'No interview results found'}), 400
    
    interview = active_sessions[session_id]
    results = interview.get('final_results')
    
    if not results:
        return jsonify({'error': 'Interview not completed yet'}), 400
    
    # Get session details from database
    session_data = db.get_session(session_id)
    answers = db.get_session_answers(session_id)
    
    return jsonify({
        'success': True,
        'results': results,
        'session': session_data,
        'answers': answers,
        'questions': interview['questions']
    })


@app.route('/api/get-analytics', methods=['GET'])
def get_analytics():
    """Get performance analytics for user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'No user data found'}), 400
    
    # Get all sessions
    sessions = db.get_user_sessions(user_id)
    
    # Get performance trend
    trend = db.get_user_performance_trend(user_id)
    
    # Get analytics data
    analytics_data = db.get_user_analytics(user_id)
    
    # Calculate aggregate stats
    completed_sessions = [s for s in sessions if s['status'] == 'completed']
    
    if completed_sessions:
        avg_scores = {}
        for s in completed_sessions:
            for key in ['overall_score']:
                if key not in avg_scores:
                    avg_scores[key] = []
                if s.get(key):
                    avg_scores[key].append(s[key])
        
        averages = {k: round(sum(v) / len(v), 1) for k, v in avg_scores.items() if v}
    else:
        averages = {}
    
    return jsonify({
        'success': True,
        'sessions': sessions,
        'trend': trend,
        'analytics': analytics_data,
        'averages': averages,
        'total_sessions': len(sessions),
        'completed_sessions': len(completed_sessions)
    })


@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload audio file for transcription"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No audio selected'}), 400
    
    try:
        # Save audio file
        filename = f"audio_{uuid.uuid4()}.wav"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        audio_file.save(filepath)
        
        # Transcribe
        transcription = transcribe_audio(filepath)
        
        return jsonify({
            'success': True,
            'transcription': transcription
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing audio: {str(e)}'}), 500


@app.route('/api/reset-session', methods=['POST'])
def reset_session():
    """Reset current interview session"""
    session_id = session.get('current_session_id')
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    session.pop('current_session_id', None)
    
    return jsonify({'success': True, 'message': 'Session reset'})


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = 5001  # Using 5001 as 5000 is used by AirPlay Receiver on macOS
    print(f"🚀 Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    print(f"📍 Open http://127.0.0.1:{port} in your browser")
    app.run(debug=True, host='0.0.0.0', port=port)
