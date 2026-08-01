"""
Speech Recognition Module - Handles voice recording and transcription
Supports real-time speech-to-text for interview answers
"""
import os
import tempfile
import speech_recognition as sr
from typing import Optional, Dict
from config import Config

class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 2.0
        
    def transcribe_audio_file(self, audio_path: str) -> Dict:
        """
        Transcribe an audio file to text
        
        Args:
            audio_path: Path to audio file (wav, mp3, etc.)
            
        Returns:
            Dict with transcription text, confidence, and metadata
        """
        try:
            with sr.AudioFile(audio_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
                
                # Try Google Web Speech API first (free, no key needed)
                try:
                    text = self.recognizer.recognize_google(audio_data)
                    confidence = 0.85  # estimated confidence
                except sr.UnknownValueError:
                    return {
                        'text': '',
                        'confidence': 0,
                        'error': 'Could not understand audio',
                        'duration': self._get_audio_duration(audio_path)
                    }
                except sr.RequestError:
                    # Fallback to Sphinx (offline)
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data)
                        confidence = 0.6
                    except:
                        return {
                            'text': '',
                            'confidence': 0,
                            'error': 'Speech recognition services unavailable',
                            'duration': self._get_audio_duration(audio_path)
                        }
                
                return {
                    'text': text,
                    'confidence': confidence,
                    'error': None,
                    'duration': self._get_audio_duration(audio_path),
                    'word_count': len(text.split()),
                    'filler_word_count': self._count_filler_words(text)
                }
                
        except Exception as e:
            return {
                'text': '',
                'confidence': 0,
                'error': str(e),
                'duration': 0
            }
    
    def transcribe_from_microphone(self, timeout: int = 60) -> Dict:
        """
        Record from microphone and transcribe in real-time
        
        Args:
            timeout: Maximum recording time in seconds
            
        Returns:
            Dict with transcription and analysis
        """
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"Recording... (max {timeout} seconds)")
                
                audio_data = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=120)
                print("Processing speech...")
                
                text = self.recognizer.recognize_google(audio_data)
                
                return {
                    'text': text,
                    'confidence': 0.85,
                    'error': None,
                    'duration': len(audio_data.frame_data) / audio_data.sample_rate,
                    'word_count': len(text.split()),
                    'filler_word_count': self._count_filler_words(text)
                }
                
        except sr.WaitTimeoutError:
            return {'text': '', 'confidence': 0, 'error': 'No speech detected', 'duration': 0}
        except sr.UnknownValueError:
            return {'text': '', 'confidence': 0, 'error': 'Could not understand speech', 'duration': 0}
        except Exception as e:
            return {'text': '', 'confidence': 0, 'error': str(e), 'duration': 0}
    
    def _count_filler_words(self, text: str) -> int:
        """Count filler words in transcription"""
        filler_words = ['um', 'uh', 'like', 'actually', 'basically', 'literally',
                       'you know', 'i mean', 'sort of', 'kind of', 'well', 'so',
                       'anyway', 'right', 'okay', 'hmm', 'ah', 'er']
        text_lower = text.lower()
        count = 0
        for filler in filler_words:
            count += text_lower.count(filler)
        return count
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except:
            return 0
    
    def analyze_speech_patterns(self, text: str) -> Dict:
        """
        Analyze speech patterns from transcribed text
        
        Returns:
            Dict with speaking pace, clarity, filler words analysis
        """
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return {
                'pace': 0,
                'words_per_minute': 0,
                'filler_word_percentage': 0,
                'clarity_score': 0,
                'suggestions': []
            }
        
        filler_count = self._count_filler_words(text)
        filler_percentage = (filler_count / word_count) * 100
        
        # Estimate pace (assume ~2 seconds per word for speech)
        estimated_duration_minutes = word_count * 2 / 60
        wpm = word_count / max(estimated_duration_minutes, 0.1)
        
        # Clarity score based on filler word percentage
        if filler_percentage < 5:
            clarity_score = 9
        elif filler_percentage < 10:
            clarity_score = 7
        elif filler_percentage < 15:
            clarity_score = 5
        else:
            clarity_score = 3
        
        suggestions = []
        if wpm > 160:
            suggestions.append("Try speaking a bit slower for better clarity")
        elif wpm < 80:
            suggestions.append("Try speaking a bit faster to maintain engagement")
        
        if filler_percentage > 10:
            suggestions.append(f"Reduce filler words (currently {filler_percentage:.1f}% of speech)")
        
        if word_count < 20:
            suggestions.append("Try to provide more detailed answers with specific examples")
        
        return {
            'pace': min(wpm / 200, 1.0),  # normalized pace
            'words_per_minute': round(wpm, 1),
            'filler_word_count': filler_count,
            'filler_word_percentage': round(filler_percentage, 1),
            'clarity_score': clarity_score,
            'suggestions': suggestions
        }


def transcribe_audio(audio_path: str) -> Dict:
    """Convenience function to transcribe audio file"""
    processor = SpeechProcessor()
    return processor.transcribe_audio_file(audio_path)


def analyze_speech(text: str) -> Dict:
    """Convenience function to analyze speech patterns"""
    processor = SpeechProcessor()
    return processor.analyze_speech_patterns(text)

