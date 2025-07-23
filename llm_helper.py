import os
from typing import List, Dict, Any
from openai import OpenAI

class LLMHelper:
    """Handles LLM interactions for newsletter content generation"""
    
    # LLM Configuration Constants
    MODEL = "gpt-4o"
    MAX_TOKENS = 150
    TEMPERATURE = 0.7
    
    # Fallback subject line
    FALLBACK_SUBJECT_LINE = "🎾 New Courses Available!"
    
    # Fallback descriptions
    FALLBACK_DESCRIPTIONS = {
        'adults': "Perfect for players of all levels, our adult courses focus on technique, strategy, and match play.",
        'juniors': "Fun and engaging courses for young players, using the LTA's colored ball progression system.",
        'events': "Special sessions and events to enhance your tennis experience and meet other players."
    }
    
    FALLBACK_LEVEL_DESCRIPTIONS = {
        'Beginner': "Perfect for those new to tennis or returning after a break.",
        'Improver': "For players who are confident rallying and ready to level up.",
        'Intermediate': "For regular players wanting to refine technique and strategy.",
        'Advanced': "For experienced players focusing on advanced techniques and match play."
    }
    
    FALLBACK_PREVIEW_TEXT = "New courses and fun events this July"
    FALLBACK_NEWSLETTER_SUMMARY = "Check out what's coming up this month — from new tennis courses to help you improve your game!"
    FALLBACK_EVENT_DESCRIPTION = "Join us for a fun adult doubles tournament at Belair Park. Whether you're coming solo or with a partner, it's a great way to meet other players and enjoy some friendly matchplay in the sun."
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response by removing quotes, numbering, and extra formatting"""
        if not response or response is None:
            return ""
        
        # Remove quotes at the beginning and end
        cleaned = response.strip()
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove numbering (1., 2., etc.)
        lines = cleaned.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Remove numbering patterns
            if line and not line[0].isdigit() or (line[0].isdigit() and len(line) > 1 and line[1] in ['.', ')', '-']):
                # Remove numbered prefixes
                if line[0].isdigit() and len(line) > 1 and line[1] in ['.', ')', '-']:
                    line = line[2:].strip()
                # Remove dash prefixes
                if line.startswith('- '):
                    line = line[2:].strip()
                if line:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text content from HTML, removing tags but preserving structure"""
        import re
        
        if not html_content:
            return ""
        
        # Simple approach: just remove all HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def debug_extract_text(self, html_content: str) -> str:
        """Debug method to see what text is being extracted from HTML"""
        print(f"DEBUG: Original HTML length: {len(html_content)}")
        print(f"DEBUG: First 200 chars of HTML: {html_content[:200]}...")
        
        extracted = self._extract_text_from_html(html_content)
        print(f"DEBUG: Extracted text length: {len(extracted)}")
        print(f"DEBUG: First 500 chars of extracted text: {extracted[:500]}")
        
        # Show some key content that should be present
        key_phrases = ['Course', 'Event', 'Book', 'Beginner', 'Improver', 'Adult', 'Junior']
        found_phrases = []
        for phrase in key_phrases:
            if phrase.lower() in extracted.lower():
                found_phrases.append(phrase)
        
        print(f"DEBUG: Key phrases found: {found_phrases}")
        return extracted
    
    def test_html_extraction(self, html_content: str) -> str:
        """Test method to verify HTML extraction is working correctly"""
        print("=== HTML EXTRACTION TEST ===")
        print(f"Input HTML length: {len(html_content)}")
        
        # Show a sample of the HTML
        sample_html = html_content[:300] if len(html_content) > 300 else html_content
        print(f"Sample HTML: {sample_html}")
        
        # Extract text
        extracted = self._extract_text_from_html(html_content)
        print(f"Extracted text length: {len(extracted)}")
        
        # Show a sample of the extracted text
        sample_text = extracted[:300] if len(extracted) > 300 else extracted
        print(f"Sample extracted text: {sample_text}")
        
        # Check for common tennis-related content
        tennis_keywords = ['tennis', 'course', 'event', 'book', 'beginner', 'improver', 'adult', 'junior']
        found_keywords = [kw for kw in tennis_keywords if kw in extracted.lower()]
        print(f"Found tennis keywords: {found_keywords}")
        
        print("=== END TEST ===")
        return extracted
    
    def _make_llm_call(self, prompt: str, max_tokens: int = None) -> str:
        """Make a call to the LLM API with error handling and cleaning"""
        if not self.api_key or not self.client:
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.MAX_TOKENS,
                temperature=self.TEMPERATURE
            )
            
            # Clean the response to remove quotes, numbering, etc.
            content = response.choices[0].message.content
            if content is None:
                return ""
            
            cleaned_content = self._clean_llm_response(content)
            return cleaned_content if cleaned_content else ""
            
        except Exception as e:
            print(f"Error making LLM call: {e}")
            return ""
    
    def generate_subject_line(self, content_types: List[str] = None, course_count: int = None, html_content: str = None) -> str:
        """Generate subject line for the newsletter from content types or HTML content"""
        # Check for API key first
        if not self.api_key:
            print("No API key available, using fallback subject line")
            return self.FALLBACK_SUBJECT_LINE
    
        text_content = self._extract_text_from_html(html_content)
        
        prompt = f"""        
        Generate a subject line for a friendly community tennis newsletter in Belair and Dulwich in South East London.

        User provided this content: {text_content}
        Tone: upbeat, clear, slightly playful but not cheesy  
        Audience: casual tennis players, families with kids  

        Examples:
        - 🎾 Book Your Spot: Junior Courses Start Next Week
        - ☀️ Still time to join! Adult courses, junior camps & tournament
        - 🔥 What's New This June: Sunday Drop-Ins and Doubles Tournament
        - 🎾 Adults & Juniors: New Courses Now Open for Booking
        - ☀️ Summer Tennis is Here — Courses, Camps & More
        - 📅 August Courses Now Open — Find Your Level
        - 🎒 Tennis Camps for Ages 4–11 — Saturdays at Dulwich Park
            
        Return only the subject line, without quotes or numbering:
        """
        
        return self._make_llm_call(prompt, max_tokens=100)
    
    def generate_preview_text(self, content_types: List[str] = None, course_count: int = None, html_content: str = None) -> str:
        """Generate preview text for email from content types or HTML content"""
        if not self.api_key:
            return self.FALLBACK_PREVIEW_TEXT
        
        text_content = self._extract_text_from_html(html_content)
        
        prompt = f"""
        Write a single preview text for a community tennis newsletter.

        Requirements:
        - Keep under 150 characters
        - Audience: families and adults interested in local tennis.  
        - Tone: warm, informative, lightly enthusiastic.  
        - Highlight the following: {text_content}
        - Make it sound inviting, like a friendly tip from someone in the know.
        - Return only ONE preview text, not multiple options
        
        Examples:
        - Wimbledon's heating up — and so are our courses, junior holiday camps, and a social doubles tournament
        - New courses and fun events this July
        - Summer tennis is here — join a course, camp or tournament 
        - Tennis in the sun? We've got courses, camps & tournaments waiting

        Return only the preview text:
        """
        
        return self._make_llm_call(prompt, max_tokens=100)
    
    def generate_block_description(self, content_type: str) -> str:
        """Generate description for content blocks using LLM with fallback"""
        if not self.api_key:
            return self.FALLBACK_DESCRIPTIONS.get(content_type, "Join our tennis courses and improve your game!")
        
        prompt = f"""
        You are helping write short introductory summary text for sections in a community tennis newsletter.
        
        Each section includes a list of courses or camps (e.g. Adults or Juniors).  
        
        Your job is to write **1–2 warm, friendly lines** introducing what’s on offer, just before the bullet list.

        Audience: casual adult players or parents of juniors  
        Tone: inviting, clear, and upbeat — like a trusted local coach  
        Do **not** start with an emoji.

        Here is the block: {content_type}

        Write just the introductory paragraph that should go **above the bullet list**. Mention timing or what’s new if relevant (e.g. “courses starting this Sunday” or “holiday camps now open”). Avoid sounding too salesy.
        """
        
        result = self._make_llm_call(prompt)
        return result
    
    def generate_level_description(self, level: str) -> str:
        """Generate description for skill levels using LLM"""
        if not self.api_key:
            return self.FALLBACK_LEVEL_DESCRIPTIONS.get(level, "Suitable for all levels.")
        
        prompt = f"""
        Generate a short, engaging description for a tennis skill level called "{level}".
        
        Requirements:
        - Keep under 100 characters
        - Be encouraging and motivating
        - Explain what this level is for
        - Use natural, friendly tone
        - No emojis
        
        Examples:
        - Perfect for those new to tennis or returning after a break.
        - For players who are confident rallying and ready to level up.
        
        Return only the description (no level name, no quotes):
        """
        
        result = self._make_llm_call(prompt, max_tokens=50)
        return result

    def generate_event_description(self, event_info: Dict[str, Any]) -> str:
        """Generate event description using LLM or fallback"""
        user_description = event_info.get('description', '')
        user_title = event_info.get('title', 'Event')

        if not self.api_key:
            return self.FALLBACK_EVENT_DESCRIPTION.get(event_info.get('title', 'Event'))
        
        prompt = f"""
            You are writing a short, friendly description of a for a block to be included in a community tennis newsletter.
            
            User provided this event description: {user_description}
            
            User provided this event title: {user_title}

            Keep the key details but make it sound more inviting and natural.
            
            Style: max 3 sentences, with clear mention of date, time, and location  
            Include: a short summary of the vibe or activity (e.g. social doubles, holiday camps, drop-ins)
            Audience: adult recreational tennis players and parents of junior players in South London  
            Tone: warm, clear, and lightly enthusiastic (not too salesy or overhyped). Limited emojis in the description

            Example
            - Celebrate the finals weekend with a casual mixed doubles session on Sunday, 14 July @ Belair Park, 3–5pm.
            - Join us for a fun adult doubles tournament at Belair Park on Sunday, 14 July @ Belair Park, 3–5pm. Whether you're coming solo or with a partner, it's a great way to meet other players and enjoy some friendly matchplay in the sun.
            
            Return only the rewritten event description:
            """
            
        return self._make_llm_call(prompt, max_tokens=150)
        
    
    def generate_newsletter_summary(self, content_types: List[str] = None, html_content: str = None) -> str:
        """Generate newsletter summary from content types or HTML content"""
        if not self.api_key:
            return self.FALLBACK_NEWSLETTER_SUMMARY
        
        if html_content:
            text_content = self._extract_text_from_html(html_content)
            prompt = f"""
            Write a short introductory paragraph (max 2 lines) for a friendly tennis newsletter.

            Audience: local players and parents in South London  
            Tone: welcoming, friendly, lightly seasonal  
            Newsletter includes: {text_content}

            Mention Wimbledon, other grand slam tournaments or the weather if it's relevant. Avoid emojis at the start, but 1 is fine elsewhere. Make it sound like a friendly coach giving you a quick update.

            Example:
            - Wimbledon's heating up — and so are our courses, junior holiday camps, and a social doubles tournament
            - New courses and fun events this July
            - Summer tennis is here — join a course, camp or tournament 
            - Tennis in the sun? We've got courses, camps & tournaments waiting
            
            Return only the summary:
            """
        
        return self._make_llm_call(prompt, max_tokens=150)
