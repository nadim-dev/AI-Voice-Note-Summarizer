"""Intelligent Universal Summarizer - Works for all content types"""

import os
import re
from dotenv import load_dotenv
from typing import Dict, List
import openai

# Load environment variables automatically
load_dotenv()

class SummaryEngine:
    def __init__(self, api_key=None):
        # If api_key provided, use it. Otherwise try from environment
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
        
        # Configure OpenAI if key exists
        if self.api_key:
            openai.api_key = self.api_key
            self.use_ai = True
            print("✅ Using OpenAI API for intelligent summaries")
        else:
            self.use_ai = False
            print("ℹ️ Using local summarizer (add OPENAI_API_KEY to .env for AI)")
    
    def generate_summary(self, text: str, style: str = "detailed") -> Dict:
        """Generate summary - automatically detects content type"""
        
        if self.use_ai:
            return self._ai_smart_summary(text, style)
        else:
            return self._local_smart_summary(text, style)
    
    def _detect_content_type(self, text: str) -> str:
        """Automatically detect what kind of content this is"""
        text_lower = text.lower()
        
        # Check for meeting indicators
        meeting_words = ['meeting', 'discuss', 'agenda', 'team', 'project', 'deadline', 'client']
        if any(word in text_lower for word in meeting_words):
            return "meeting"
        
        # Check for story indicators
        story_words = ['woke up', 'felt', 'realized', 'happened', 'morning', 'night', 'later']
        if any(word in text_lower for word in story_words):
            return "story"
        
        # Check for action items
        action_words = ['need to', 'should', 'must', 'todo', 'task', 'action']
        if any(word in text_lower for word in action_words):
            return "action"
        
        # Default
        return "general"
    
    def _ai_smart_summary(self, text: str, style: str) -> Dict:
        """AI summary that adapts to content type"""
        
        content_type = self._detect_content_type(text)
        
        # Different prompts for different content types
        prompts = {
            "story": f"""This is a personal story/narrative. Create a natural, engaging summary:

Story: {text}

Please provide:
1. SUMMARY: A flowing 2-3 sentence overview of what happened
2. KEY MOMENTS: The main events in chronological order
3. EMOTIONS/REFLECTIONS: Any feelings or realizations

Example of good story summary:
"A stressful morning began when the author overslept, couldn't find keys (discovered in fridge), got stuck in traffic, arrived late to work, and faced the embarrassment of mismatched shoes—all before even sitting at their desk.""" ,

            "meeting": f"""This is a meeting or professional discussion. Extract key information:

Meeting Notes: {text}

Please provide:
1. SUMMARY: What was accomplished/discussed (2-3 sentences)
2. DECISIONS: What was decided
3. ACTION ITEMS: Who needs to do what by when
4. NEXT STEPS: What happens next

Example of good meeting summary:
"The team discussed the Q4 project timeline. Decided to push the launch date to Friday. John will update the client, Sarah needs to complete testing by Wednesday.""" ,

            "action": f"""This contains tasks and action items. Extract clearly:

Content: {text}

Please provide:
1. SUMMARY: Overview of what needs to be done
2. ACTION ITEMS: List each task with who and when
3. PRIORITIES: What's most important/urgent

Example:
"Three main tasks identified: Project completion by Friday, design work by John, testing by Sarah.""" ,

            "general": f"""Summarize this content clearly and concisely:

Content: {text}

Please provide:
1. SUMMARY: Main points in 2-3 sentences
2. KEY DETAILS: Important supporting information
3. KEY TAKEAWAYS: What to remember

Keep it clear and useful."""
        }
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are an expert summarizer. The content type is: {content_type}. Create natural, useful summaries."},
                    {"role": "user", "content": prompts[content_type]}
                ],
                temperature=0.4,
                max_tokens=400
            )
            
            ai_text = response.choices[0].message.content
            
            # Parse and enhance the response
            result = self._parse_ai_response(ai_text)
            result['content_type'] = content_type  # Add content type for display
            
            return result
            
        except Exception as e:
            print(f"AI Error: {e}, falling back to local")
            return self._local_smart_summary(text, style)
    
    def _local_smart_summary(self, text: str, style: str) -> Dict:
        """Local summarizer that adapts to content type"""
        
        content_type = self._detect_content_type(text)
        sentences = self._split_sentences(text)
        
        if not sentences:
            return self._empty_result()
        
        # Different strategies for different content types
        if content_type == "story":
            return self._summarize_story(sentences, text)
        elif content_type == "meeting":
            return self._summarize_meeting(sentences, text)
        elif content_type == "action":
            return self._summarize_actions(sentences, text)
        else:
            return self._summarize_general(sentences, text)
    
    def _summarize_story(self, sentences: List[str], full_text: str) -> Dict:
        """Create a flowing story summary"""
        
        if len(sentences) <= 2:
            summary = ' '.join(sentences)
        else:
            # Create a narrative flow
            intro = sentences[0]
            middle = ' '.join(sentences[1:-1])
            conclusion = sentences[-1]
            
            summary = f"{intro} Then, {middle.lower()} Finally, {conclusion.lower()}"
        
        # Key moments are the main events
        key_points = []
        for sent in sentences:
            if any(word in sent.lower() for word in ['found', 'realized', 'discovered', 'happened']):
                key_points.append(sent)
            elif len(key_points) < 3 and sent not in key_points:
                key_points.append(sent)
        
        return {
            'summary': summary[:400],
            'key_points': key_points[:4],
            'action_items': self._extract_action_items(full_text),
            'deadlines': [],
            'decisions': self._extract_decisions(full_text),
            'content_type': 'story'
        }
    
    def _summarize_meeting(self, sentences: List[str], full_text: str) -> Dict:
        """Create a professional meeting summary"""
        
        if len(sentences) <= 2:
            summary = ' '.join(sentences)
        else:
            # Meeting summary focuses on outcomes
            summary = f"The discussion covered: {sentences[0]}. " + \
                     f"Key outcomes: {sentences[1] if len(sentences) > 1 else ''}"
        
        return {
            'summary': summary[:400],
            'key_points': sentences[:4],
            'action_items': self._extract_action_items(full_text),
            'deadlines': self._extract_deadlines(full_text),
            'decisions': self._extract_decisions(full_text),
            'content_type': 'meeting'
        }
    
    def _summarize_actions(self, sentences: List[str], full_text: str) -> Dict:
        """Focus on action items"""
        
        action_items = self._extract_action_items(full_text)
        
        if action_items:
            summary = f"Action items identified: {len(action_items)} tasks. " + \
                     f"Main tasks: {'. '.join(action_items[:2])}"
        else:
            summary = "No clear action items identified."
        
        return {
            'summary': summary,
            'key_points': sentences[:3],
            'action_items': action_items,
            'deadlines': self._extract_deadlines(full_text),
            'decisions': self._extract_decisions(full_text),
            'content_type': 'action'
        }
    
    def _summarize_general(self, sentences: List[str], full_text: str) -> Dict:
        """General purpose summary"""
        
        if len(sentences) <= 3:
            summary = ' '.join(sentences)
        else:
            summary = f"{sentences[0]} {sentences[1]} {sentences[-1]}"
        
        return {
            'summary': summary[:400],
            'key_points': sentences[:4],
            'action_items': self._extract_action_items(full_text),
            'deadlines': self._extract_deadlines(full_text),
            'decisions': self._extract_decisions(full_text),
            'content_type': 'general'
        }
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'summary': 'No content to summarize',
            'key_points': [],
            'action_items': [],
            'deadlines': [],
            'decisions': [],
            'content_type': 'unknown'
        }
    
    def _parse_ai_response(self, ai_text: str) -> Dict:
        """Parse AI response into structured format"""
        
        sections = {
            'summary': '',
            'key_points': [],
            'action_items': [],
            'deadlines': [],
            'decisions': []
        }
        
        lines = ai_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            # Detect sections
            if 'summary' in lower_line and ':' in line:
                parts = line.split(':', 1)
                sections['summary'] = parts[1].strip() if len(parts) > 1 else ''
                current_section = 'summary'
            elif any(word in lower_line for word in ['key moments', 'key points', 'main events']):
                current_section = 'key_points'
            elif any(word in lower_line for word in ['action items', 'tasks', 'to-do']):
                current_section = 'action_items'
            elif any(word in lower_line for word in ['deadlines', 'due', 'by when']):
                current_section = 'deadlines'
            elif any(word in lower_line for word in ['decisions', 'conclusions', 'agreed']):
                current_section = 'decisions'
            elif line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                clean_line = line.lstrip('- •*123456789.').strip()
                if clean_line and current_section and current_section in sections:
                    if isinstance(sections[current_section], list):
                        sections[current_section].append(clean_line)
            elif current_section == 'summary' and sections['summary']:
                sections['summary'] += ' ' + line
            elif current_section == 'summary' and not sections['summary']:
                sections['summary'] = line
        
        return sections
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences intelligently"""
        # Handle common abbreviations
        text = text.replace('Mr.', 'Mr').replace('Mrs.', 'Mrs').replace('Dr.', 'Dr')
        text = text.replace('i.e.', 'ie').replace('e.g.', 'eg')
        
        # Split on sentence endings
        sentences = []
        for sent in re.split(r'[.!?]+', text):
            sent = sent.strip()
            if len(sent) > 10:  # Ignore very short fragments
                # Capitalize first letter
                if sent and sent[0].islower():
                    sent = sent[0].upper() + sent[1:]
                sentences.append(sent)
        
        return sentences
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items using keywords"""
        action_phrases = [
            'need to', 'should', 'must', 'have to', 'will',
            'going to', 'please', 'action item', 'todo',
            'task', 'remind', 'don\'t forget', 'remember to'
        ]
        
        sentences = self._split_sentences(text)
        actions = []
        
        for sent in sentences:
            lower_sent = sent.lower()
            if any(phrase in lower_sent for phrase in action_phrases):
                if len(sent) > 15:
                    actions.append(sent)
        
        # Remove duplicates
        seen = set()
        return [a for a in actions if not (a in seen or seen.add(a))][:5]
    
    def _extract_deadlines(self, text: str) -> List[str]:
        """Extract deadlines and dates"""
        deadline_keywords = ['by', 'due', 'deadline', 'before', 'until', 'tomorrow', 'next']
        deadlines = []
        
        sentences = self._split_sentences(text)
        for sent in sentences:
            if any(word in sent.lower() for word in deadline_keywords):
                deadlines.append(sent)
        
        return deadlines[:3]
    
    def _extract_decisions(self, text: str) -> List[str]:
        """Extract decisions made"""
        decision_keywords = ['decided', 'agreed', 'realized', 'noticed', 'concluded', 'understood']
        decisions = []
        
        sentences = self._split_sentences(text)
        for sent in sentences:
            if any(word in sent.lower() for word in decision_keywords):
                decisions.append(sent)
        
        return decisions[:3]