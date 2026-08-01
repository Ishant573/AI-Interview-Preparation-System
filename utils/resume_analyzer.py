"""
Resume Analyzer - Parses and analyzes uploaded resumes
Extracts skills, experience, education, and generates a structured profile
"""
import re
import PyPDF2
import pdfplumber
from typing import Dict, List, Optional

# Common skill categories for keyword matching
SKILL_DATABASE = {
    'programming_languages': ['python', 'java', 'javascript', 'c++', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'typescript', 'scala', 'perl', 'php', 'c#', 'sql'],
    'web_technologies': ['react', 'angular', 'vue', 'django', 'flask', 'node.js', 'express', 'spring', 'html', 'css', 'bootstrap', 'tailwind', 'redux', 'next.js', 'gatsby'],
    'cloud_devops': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'ci/cd', 'gitlab', 'github actions'],
    'data_science': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'data analysis', 'statistics', 'nlp', 'computer vision'],
    'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'oracle', 'cassandra', 'dynamodb'],
    'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking', 'time management', 'project management', 'agile', 'scrum']
}

class ResumeAnalyzer:
    def __init__(self):
        self.resume_text = ""
        self.profile = {}
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file using multiple methods for better accuracy"""
        text = ""
        
        # Method 1: Using pdfplumber (better for structured text)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
        
        # Method 2: Fallback to PyPDF2
        if not text.strip():
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                print(f"PyPDF2 extraction failed: {e}")
        
        self.resume_text = text
        return text
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from plain text file"""
        with open(txt_path, 'r', encoding='utf-8') as file:
            self.resume_text = file.read()
        return self.resume_text
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze resume text and extract structured information"""
        self.resume_text = text
        
        profile = {
            'skills': self._extract_skills(),
            'experience_years': self._extract_experience_years(),
            'education': self._extract_education(),
            'key_achievements': self._extract_achievements(),
            'summary': self._generate_summary(),
            'skill_categories': self._categorize_skills()
        }
        
        self.profile = profile
        return profile
    
    def _extract_skills(self) -> List[str]:
        """Extract technical skills from resume text"""
        found_skills = set()
        text_lower = self.resume_text.lower()
        
        for category, skills in SKILL_DATABASE.items():
            for skill in skills:
                if skill in text_lower:
                    found_skills.add(skill)
        
        return list(found_skills)
    
    def _extract_experience_years(self) -> float:
        """Extract total years of experience"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
            r'experience\s*(?:of)?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:in|as)'
        ]
        
        text_lower = self.resume_text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                return float(max(matches))
        
        # Estimate from date ranges
        date_pattern = r'(20\d\d)\s*(?:-|–|to)\s*(?:present|current|20\d\d)'
        matches = re.findall(date_pattern, text_lower)
        if matches:
            return len(matches) * 2  # rough estimate
        
        return 0
    
    def _extract_education(self) -> List[Dict]:
        """Extract education details"""
        education = []
        degree_patterns = [
            r'(bachelor[s]?|master[s]?|phd|ph\.d|doctorate|b\.tech|m\.tech|b\.e|m\.e|b\.sc|m\.sc|b\.a|m\.a|mba)',
            r'(bachelor[s]?|master[s]?|phd|ph\.d|doctorate)\s+(?:of|in|degree)\s+(?:science|engineering|arts|technology|computer|business|administration)'
        ]
        
        text_lower = self.resume_text.lower()
        universities = re.findall(r'(?:university|college|institute|school)\s*(?:of)?\s*[a-z\s]+', text_lower)
        
        for pat in degree_patterns:
            matches = re.findall(pat, text_lower)
            for match in matches[:3]:  # max 3 degrees
                edu_entry = {
                    'degree': match.strip(),
                    'institution': universities[len(education)] if len(education) < len(universities) else 'Unknown',
                    'year': None
                }
                education.append(edu_entry)
        
        return education
    
    def _extract_achievements(self) -> List[str]:
        """Extract key achievements from resume"""
        achievements = []
        achievement_indicators = [
            r'(?:achieved|accomplished|delivered|improved|increased|reduced|led|managed|created|developed|implemented|designed|optimized)[^.]*\.',
            r'(?:awarded|recognized|received|won|certified)[^.]*\.',
        ]
        
        text_lower = self.resume_text.lower()
        for indicator in achievement_indicators:
            matches = re.findall(indicator, text_lower)
            achievements.extend([m.strip() for m in matches[:5]])
        
        return achievements
    
    def _generate_summary(self) -> str:
        """Generate a professional summary based on extracted information"""
        skills = self._extract_skills()
        experience = self._extract_experience_years()
        
        if not skills:
            return "Resume analysis incomplete. Please ensure your resume contains detailed information."
        
        top_skills = skills[:5]
        summary_parts = [f"Professional with {experience:.0f}+ years of experience"]
        
        if top_skills:
            summary_parts.append(f"skilled in {', '.join(top_skills[:-1])} and {top_skills[-1]}")
        
        summary_parts.append("seeking to leverage expertise in a challenging role.")
        
        return " ".join(summary_parts)
    
    def _categorize_skills(self) -> Dict[str, List[str]]:
        """Categorize found skills into their respective groups"""
        categorized = {}
        text_lower = self.resume_text.lower()
        
        for category, skills in SKILL_DATABASE.items():
            found = [s for s in skills if s in text_lower]
            if found:
                categorized[category.replace('_', ' ').title()] = found
        
        return categorized
    
    def get_job_title_suggestions(self) -> List[str]:
        """Suggest job titles based on resume content"""
        titles = []
        text_lower = self.resume_text.lower()
        
        title_patterns = [
            (['python', 'java', 'javascript', 'c++'], 'Software Engineer'),
            (['machine learning', 'tensorflow', 'pytorch', 'data analysis'], 'Data Scientist'),
            (['react', 'angular', 'vue', 'html', 'css'], 'Frontend Developer'),
            (['django', 'flask', 'node.js', 'express'], 'Backend Developer'),
            (['aws', 'azure', 'docker', 'kubernetes'], 'DevOps Engineer'),
            (['sql', 'mysql', 'postgresql', 'mongodb'], 'Database Administrator'),
        ]
        
        for keywords, title in title_patterns:
            if any(kw in text_lower for kw in keywords):
                titles.append(title)
        
        return titles[:3] if titles else ['General Applicant']


def analyze_resume(file_path: str) -> Dict:
    """Main function to analyze a resume file"""
    analyzer = ResumeAnalyzer()
    
    if file_path.endswith('.pdf'):
        analyzer.extract_text_from_pdf(file_path)
    elif file_path.endswith('.txt'):
        analyzer.extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")
    
    profile = analyzer.analyze_text(analyzer.resume_text)
    profile['suggested_titles'] = analyzer.get_job_title_suggestions()
    
    return profile

