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
    
    def _make_llm_call(self, prompt: str, max_tokens: int = None, temperature_override: float = None) -> str:
        """Make a call to the LLM API with error handling and cleaning"""
        if not self.api_key or not self.client:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.MAX_TOKENS,
                temperature=temperature_override if temperature_override is not None else self.TEMPERATURE
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
    
    def generate_subject_line(self, content_summary: str = None) -> str:
        """Generate subject line for the newsletter from a structured content summary"""
        if not self.api_key:
            return self.FALLBACK_SUBJECT_LINE

        prompt = f"""
        Write a subject line for a community tennis newsletter from Vamos Tennis in Belair and Dulwich, South East London.

        Newsletter contents:
        {content_summary}

        Rules:
        - Be specific to the actual content above — mention the real things on offer
        - Tone: clear and direct, lightly warm — not hyped, not cheesy
        - One emoji max, at the start
        - No exclamation marks unless it's genuinely warranted
        - Under 60 characters

        Good examples (notice they reference real content, not vague phrases):
        - 🎾 Adult courses & junior camps open for booking
        - 📅 New courses + July tournament — book your spot
        - 🎾 Beginner to Advanced: courses now open at Dulwich & Belair

        Bad examples (too vague or cheesy — avoid these):
        - Summer Tennis is Here — Courses, Camps & More
        - Tennis in the sun? We've got you covered
        - 🔥 What's New This Month

        Return only the subject line:
        """

        return self._make_llm_call(prompt, max_tokens=60, temperature_override=0.4)
    
    def generate_preview_text(self, content_summary: str = None) -> str:
        """Generate preview text for email from a structured content summary"""
        if not self.api_key:
            return self.FALLBACK_PREVIEW_TEXT

        prompt = f"""
        Write a preview text (shown in email inboxes before opening) for a community tennis newsletter.

        Newsletter contents:
        {content_summary}

        Rules:
        - Under 150 characters
        - Reference the actual content — don't be vague
        - Only mention specific dates if they are present in the newsletter contents above — do not invent them
        - Tone: conversational, like a quick heads-up from a friend
        - No emoji
        - No exclamation marks

        Good examples:
        - Adult and junior courses now open — plus a social doubles tournament on 19 July at Belair Park
        - Beginner to Advanced courses at Dulwich and Belair, with junior camps starting next month

        Bad examples (too vague):
        - New courses and fun events this July
        - Summer tennis is here — join a course, camp or tournament

        Return only the preview text:
        """

        return self._make_llm_call(prompt, max_tokens=80, temperature_override=0.4)
    
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

        Write just the introductory paragraph that should go **above the bullet list**. Only mention specific dates or timing if they are clearly present in the provided content — do not invent them. Avoid sounding too salesy.
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
            You are writing a short, friendly description for a block to be included in a community tennis newsletter.

            User provided this event description: {user_description}

            User provided this event title: {user_title}

            Keep the key details but make it sound more inviting and natural.

            Style: max 3 sentences
            Include: a short summary of the vibe or activity (e.g. social doubles, holiday camps, drop-ins)
            Only mention date, time, and location if they are explicitly provided above — do not invent or assume them.
            Do not mention a venue name unless it is explicitly stated in the event info above.
            Audience: adult recreational tennis players and parents of junior players in South London
            Tone: warm, clear, and lightly enthusiastic (not too salesy or overhyped). Limited emojis in the description

            Example (only if date/location were provided in the input):
            - Join us for a fun adult doubles tournament. Whether you're coming solo or with a partner, it's a great way to meet other players and enjoy some friendly matchplay in the sun.

            Return only the rewritten event description:
            """
            
        return self._make_llm_call(prompt, max_tokens=150)
        
    
    def generate_newsletter_summary(self, content_summary: str = None) -> str:
        """Generate newsletter intro paragraph from a structured content summary"""
        if not self.api_key:
            return self.FALLBACK_NEWSLETTER_SUMMARY

        prompt = f"""
        Write a short intro paragraph (1–2 sentences) for a community tennis newsletter from Vamos Tennis in South London.

        Newsletter contents:
        {content_summary}

        Rules:
        - Name the specific things on offer — don't be vague
        - Tone: like a friendly coach giving a quick roundup, not a marketing email
        - If there's a named event (e.g. a tournament or camp), mention it by name
        - Only mention specific dates if they are present in the newsletter contents above — do not invent them
        - One emoji is fine, but not at the very start
        - No exclamation marks

        Good examples:
        - Courses are back across Dulwich and Belair this month, with sessions from Beginner to Advanced — plus a social doubles tournament on 19 July.
        - We've got adult courses starting this week and junior holiday camps running every Saturday from late July. There's also a social tournament coming up if you fancy some match play.

        Bad examples:
        - Summer tennis is here — join a course, camp or tournament
        - Check out what's coming up this month — from new tennis courses to help you improve your game

        Return only the intro paragraph:
        """

        return self._make_llm_call(prompt, max_tokens=120, temperature_override=0.4)
