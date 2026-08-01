"""
Scoring Engine - Evaluates interview performance
Computes communication score, technical accuracy, confidence, and overall performance metrics
"""
import re
from typing import Dict, List, Tuple, Optional
from config import Config

class InterviewScorer:
    def __init__(self):
        self.weights = Config.WEIGHTS
        
    def score_communication(self, answer_text: str, speech_analysis: Dict) -> Dict:
        """
        Score communication skills based on answer and speech patterns
        
        Args:
            answer_text: Transcribed answer text
            speech_analysis: Speech pattern analysis from SpeechProcessor
            
        Returns:
            Dict with communication score and breakdown
        """
        if not answer_text or len(answer_text.split()) < Config.MIN_ANSWER_LENGTH:
            return {
                'score': 0,
                'breakdown': {
                    'clarity': 0,
                    'structure': 0,
                    'engagement': 0,
                    'conciseness': 0
                },
                'feedback': 'Answer too brief to evaluate communication skills.'
            }
        
        # Clarity score from speech analysis
        clarity = speech_analysis.get('clarity_score', 5) / 10
        
        # Structure score (look for signposting words)
        structure_indicators = ['first', 'second', 'finally', 'in conclusion', 
                               'for example', 'specifically', 'additionally',
                               'however', 'therefore', 'because']
        structure_count = sum(1 for word in structure_indicators if word in answer_text.lower())
        structure = min(structure_count / 3, 1.0)
        
        # Engagement score
        engagement_indicators = ['i believe', 'in my experience', 'i learned', 
                                'i developed', 'i created', 'we achieved',
                                'our team', 'my role', 'passionate about']
        engagement_count = sum(1 for phrase in engagement_indicators if phrase in answer_text.lower())
        engagement = min(engagement_count / 2, 1.0)
        
        # Conciseness score
        word_count = len(answer_text.split())
        if 30 <= word_count <= 100:
            conciseness = 1.0
        elif word_count < 30:
            conciseness = word_count / 30
        else:
            conciseness = max(0, 1 - (word_count - 100) / 200)
        
        # Weighted communication score
        communication_score = (
            clarity * 0.35 + 
            structure * 0.25 + 
            engagement * 0.25 + 
            conciseness * 0.15
        )
        
        return {
            'score': round(communication_score * 10, 1),  # Scale to 10
            'breakdown': {
                'clarity': round(clarity * 10, 1),
                'structure': round(structure * 10, 1),
                'engagement': round(engagement * 10, 1),
                'conciseness': round(conciseness * 10, 1)
            },
            'feedback': self._generate_communication_feedback(
                clarity, structure, engagement, conciseness
            )
        }
    
    def score_technical_accuracy(self, answer_text: str, question: Dict) -> Dict:
        """
        Score technical accuracy of the answer
        
        Args:
            answer_text: Candidate's answer
            question: The question object with expected keywords
            
        Returns:
            Dict with technical score and analysis
        """
        expected_keywords = question.get('expected_keywords', [])
        if not expected_keywords:
            return {'score': 5.0, 'keyword_match': 0, 'feedback': 'Technical evaluation not available.'}
        
        answer_lower = answer_text.lower()
        matched_keywords = []
        missing_keywords = []
        
        for keyword in expected_keywords:
            if isinstance(keyword, str) and keyword.lower() in answer_lower:
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        if len(expected_keywords) > 0:
            keyword_score = len(matched_keywords) / len(expected_keywords)
        else:
            keyword_score = 0
        
        # Depth score (longer, detailed answers tend to have more technical depth)
        word_count = len(answer_text.split())
        depth_score = min(word_count / 100, 1.0)
        
        # Technical term usage
        technical_terms = question.get('category', '').lower().split()
        tech_term_count = sum(1 for term in technical_terms if term in answer_lower)
        tech_score = min(tech_term_count / max(len(technical_terms), 1), 1.0)
        
        overall_score = (keyword_score * 0.5 + depth_score * 0.25 + tech_score * 0.25)
        
        return {
            'score': round(overall_score * 10, 1),
            'keyword_match': round(keyword_score * 100, 1),
            'matched_keywords': matched_keywords,
            'missing_keywords': missing_keywords,
            'feedback': self._generate_technical_feedback(matched_keywords, missing_keywords)
        }
    
    def score_confidence(self, answer_text: str, speech_analysis: Dict) -> Dict:
        """
        Score confidence based on speech patterns and language use
        
        Args:
            answer_text: Transcribed answer
            speech_analysis: Speech analysis data
            
        Returns:
            Dict with confidence score
        """
        hedging_words = ['maybe', 'perhaps', 'i think', 'not sure', 'probably',
                        'might', 'could be', 'sort of', 'kind of', 'i guess']
        confident_words = ['i know', 'i am confident', 'certainly', 'definitely',
                          'absolutely', 'i believe', 'i am sure', 'clearly']
        
        answer_lower = answer_text.lower()
        hedging_count = sum(1 for word in hedging_words if word in answer_lower)
        confident_count = sum(1 for word in confident_words if word in answer_lower)
        
        # Normalize scores
        total_words = len(answer_text.split())
        if total_words == 0:
            return {'score': 0, 'feedback': 'No answer provided to assess confidence.'}
        
        hedging_ratio = hedging_count / max(total_words, 1)
        confident_ratio = confident_count / max(total_words, 1)
        
        # From speech analysis
        clarity = speech_analysis.get('clarity_score', 5) / 10
        filler_ratio = speech_analysis.get('filler_word_percentage', 0) / 100
        
        # Confidence formula
        confidence = (
            (1 - hedging_ratio * 10) * 0.3 +
            confident_ratio * 10 * 0.2 +
            clarity * 0.3 +
            (1 - filler_ratio) * 0.2
        )
        
        confidence = max(0, min(confidence, 1))
        
        feedback = []
        if hedging_ratio > 0.1:
            feedback.append("Reduce hedging language (words like 'maybe', 'perhaps', 'I think')")
        if filler_ratio > 0.1:
            feedback.append(f"Reduce filler words (currently {filler_ratio:.1%} of speech)")
        if confident_count < 2:
            feedback.append("Use more definitive language to project confidence")
        
        return {
            'score': round(confidence * 10, 1),
            'hedging_count': hedging_count,
            'confident_phrases': confident_count,
            'feedback': '; '.join(feedback) if feedback else 'Good confidence level demonstrated.'
        }
    
    def score_relevance(self, answer_text: str, question: Dict) -> Dict:
        """
        Score how relevant the answer is to the question
        
        Args:
            answer_text: Candidate's answer
            question: The question object
            
        Returns:
            Dict with relevance score
        """
        if not answer_text:
            return {'score': 0, 'feedback': 'No answer provided.'}
        
        question_words = set(re.findall(r'\w+', question.get('question', '').lower()))
        answer_words = set(re.findall(r'\w+', answer_text.lower()))
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                     'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were',
                     'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
                     'did', 'will', 'would', 'could', 'should', 'may', 'might',
                     'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
                     'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these',
                     'those', 'what', 'which', 'who', 'whom', 'how', 'when', 'where'}
        
        question_words -= stop_words
        answer_words -= stop_words
        
        if len(question_words) == 0:
            return {'score': 5.0, 'feedback': 'Relevance assessment limited.'}
        
        overlap = len(question_words & answer_words)
        relevance_ratio = overlap / len(question_words)
        
        # Penalize very short answers
        word_count = len(answer_text.split())
        length_penalty = min(word_count / Config.MIN_ANSWER_LENGTH, 1.0)
        
        score = relevance_ratio * length_penalty
        
        return {
            'score': round(score * 10, 1),
            'overlap_words': list(question_words & answer_words)[:10],
            'feedback': 'Answer is relevant to the question.' if score > 0.5 \
                       else 'Try to focus your answer more closely on the specific question asked.'
        }
    
    def calculate_overall_score(self, scores: Dict) -> Dict:
        """
        Calculate weighted overall score from individual scores
        
        Args:
            scores: Dict with individual scores
            
        Returns:
            Dict with overall score and grade
        """
        weighted_sum = 0
        breakdown = {}
        
        for category, weight in self.weights.items():
            if category in scores:
                score_value = scores[category].get('score', 0) if isinstance(scores[category], dict) else scores[category]
                weighted_sum += score_value * weight
                breakdown[category] = score_value
        
        overall = weighted_sum * 10  # Scale to 100
        
        # Grade assignment
        if overall >= 90:
            grade = 'A+'
            grade_description = 'Excellent performance'
        elif overall >= 80:
            grade = 'A'
            grade_description = 'Very good performance'
        elif overall >= 70:
            grade = 'B'
            grade_description = 'Good performance'
        elif overall >= 60:
            grade = 'C'
            grade_description = 'Satisfactory performance'
        elif overall >= 50:
            grade = 'D'
            grade_description = 'Needs improvement'
        else:
            grade = 'F'
            grade_description = 'Significant improvement needed'
        
        return {
            'overall_score': round(overall, 1),
            'grade': grade,
            'grade_description': grade_description,
            'breakdown': breakdown,
            'weights_used': self.weights
        }
    
    def _generate_communication_feedback(self, clarity: float, structure: float,
                                         engagement: float, conciseness: float) -> str:
        """Generate personalized communication feedback"""
        feedback = []
        
        if clarity < 0.5:
            feedback.append("Work on speaking more clearly and reducing filler words")
        elif clarity > 0.8:
            feedback.append("Excellent clarity in your responses")
        
        if structure < 0.5:
            feedback.append("Use structured responses with clear beginning, middle, and end")
        elif structure > 0.8:
            feedback.append("Good use of structured responses")
        
        if engagement < 0.5:
            feedback.append("Share more personal experiences to make answers engaging")
        elif engagement > 0.8:
            feedback.append("Great engagement with personal examples")
        
        if conciseness < 0.5:
            feedback.append("Try to be more concise - focus on key points")
        
        return '; '.join(feedback) if feedback else 'Good overall communication skills.'


def calculate_performance_scores(answers: List[Dict], questions: List[Dict]) -> Dict:
    """Calculate comprehensive performance scores for an interview session"""
    scorer = InterviewScorer()
    all_scores = []
    
    for answer, question in zip(answers, questions):
        answer_text = answer.get('text', '')
        speech_analysis = answer.get('speech_analysis', {})
        
        scores = {
            'communication': scorer.score_communication(answer_text, speech_analysis),
            'technical_accuracy': scorer.score_technical_accuracy(answer_text, question),
            'confidence': scorer.score_confidence(answer_text, speech_analysis),
            'relevance': scorer.score_relevance(answer_text, question)
        }
        
        scores['overall'] = scorer.calculate_overall_score(scores)
        all_scores.append(scores)
    
    # Aggregate scores
    if all_scores:
        avg_scores = {}
        for key in ['communication', 'technical_accuracy', 'confidence', 'relevance']:
            avg_scores[key] = sum(s[key]['score'] for s in all_scores) / len(all_scores)
        
        overall = scorer.calculate_overall_score(avg_scores)
    else:
        avg_scores = {}
        overall = {'overall_score': 0, 'grade': 'N/A', 'grade_description': 'No data'}
    
    return {
        'per_question_scores': all_scores,
        'average_scores': avg_scores,
        'overall': overall
    }

