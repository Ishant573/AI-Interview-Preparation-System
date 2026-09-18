"""
Question Generator - Uses OpenAI API to generate contextual interview questions
Generates technical, behavioral, and role-specific questions based on resume analysis
"""
import json
import openai
from typing import Dict, List, Optional
from config import Config

class QuestionGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL
        self.client = None
        
        # Only initialize client if valid API key is set
        if self.api_key and self.api_key not in ('YOUR_OPENAI_API_KEY_HERE', ''):
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    def generate_questions(self, resume_profile: Dict, job_role: str = "", 
                          num_questions: int = 10) -> List[Dict]:
        """
        Generate interview questions based on resume profile
        
        Args:
            resume_profile: Analyzed resume data
            job_role: Target job role (optional)
            num_questions: Number of questions to generate
            
        Returns:
            List of question objects with type, question, and expected skills
        """
        skills = resume_profile.get('skills', [])
        experience = resume_profile.get('experience_years', 0)
        education = resume_profile.get('education', [])
        achievements = resume_profile.get('key_achievements', [])
        suggested_titles = resume_profile.get('suggested_titles', [])
        
        target_role = job_role or (suggested_titles[0] if suggested_titles else 'Software Professional')
        
        if not self.client:
            return self._generate_fallback_questions(skills, target_role, num_questions)
        
        prompt = f"""
        You are an experienced technical interviewer. Generate {num_questions} interview questions for a candidate applying for "{target_role}" position.
        
        Candidate Profile:
        - Skills: {', '.join(skills[:10]) if skills else 'Not specified'}
        - Years of Experience: {experience}
        - Education: {education}
        - Key Achievements: {', '.join(achievements[:3]) if achievements else 'Not specified'}
        
        Generate a mix of:
        1. Technical questions (40%) - based on their skills
        2. Behavioral questions (30%) - STAR method questions
        3. Role-specific questions (20%) - related to the target role
        4. Problem-solving questions (10%) - analytical thinking
        
        For each question, provide:
        - "id": question number
        - "type": "technical", "behavioral", "role_specific", or "problem_solving"
        - "question": the actual question text
        - "category": skill category being tested
        - "difficulty": "easy", "medium", or "hard"
        - "expected_keywords": key points expected in answer
        - "hint": a brief hint for the candidate
        
        Respond in JSON format as an array of question objects.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Generate questions in JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            questions_text = response.choices[0].message.content.strip()
            # Clean markdown code blocks if present
            if questions_text.startswith("```"):
                questions_text = questions_text.split("\n", 1)[1].rsplit("\n", 1)[0]
                if questions_text.endswith("```"):
                    questions_text = questions_text[:-3]
            
            questions = json.loads(questions_text)
            return questions
            
        except json.JSONDecodeError:
            # Fallback: return structured questions
            return self._generate_fallback_questions(skills, target_role, num_questions)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_questions(skills, target_role, num_questions)
    
    def _generate_fallback_questions(self, skills: List[str], role: str, 
                                     num_questions: int) -> List[Dict]:
        """Generate questions locally if API is unavailable"""
        questions = []
        
        technical_questions = [
            f"Explain the concept of {skill} and how you've applied it in real-world projects." 
            for skill in skills[:5]
        ]
        
        behavioral_questions = [
            "Tell me about a time you faced a significant challenge at work and how you overcame it.",
            "Describe a situation where you had to work with a difficult team member. How did you handle it?",
            "Give an example of a project you led from start to finish. What was your approach?",
            "Tell me about a time you had to learn a new technology quickly. How did you approach it?",
            "Describe a situation where you disagreed with your manager. How did you resolve it?"
        ]
        
        role_specific_questions = [
            f"What interests you most about the {role} role?",
            f"Where do you see yourself in 5 years as a {role}?",
            f"What unique skills can you bring to the {role} position?"
        ]
        
        all_questions = technical_questions + behavioral_questions + role_specific_questions
        
        for i, q in enumerate(all_questions[:num_questions]):
            q_type = "technical" if i < len(technical_questions) else \
                     "behavioral" if i < len(technical_questions) + len(behavioral_questions) else \
                     "role_specific"
            
            questions.append({
                "id": i + 1,
                "type": q_type,
                "question": q,
                "category": "General" if q_type == "behavioral" else role,
                "difficulty": "medium",
                "expected_keywords": [],
                "hint": "Think about specific examples from your experience."
            })
        
        return questions
    
    def generate_follow_up_question(self, question: str, answer: str) -> str:
        """Generate a follow-up question based on the candidate's answer"""
        if not self.client:
            return "Could you elaborate more on that point with a specific example?"
        
        prompt = f"""
        Based on the interview question: "{question}"
        And the candidate's response: "{answer}"
        
        Generate a relevant follow-up question that probes deeper into their answer.
        Keep it concise and focused.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate a brief, relevant follow-up interview question."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Could you elaborate more on that point with a specific example?"


def generate_interview_questions(resume_profile: Dict, job_role: str = "",
                                  num_questions: int = 10) -> List[Dict]:
    """Convenience function to generate questions"""
    generator = QuestionGenerator()
    return generator.generate_questions(resume_profile, job_role, num_questions)


