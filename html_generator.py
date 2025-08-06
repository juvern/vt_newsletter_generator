import pandas as pd
from typing import Dict, List, Any
from llm_helper import LLMHelper
from datetime import datetime

class HTMLGenerator:
    """Generates HTML blocks for newsletter content"""
    
    # Class constants
    SKILL_LEVELS = {
        'Beginner': 1,
        'Improver': 4,
        'Intermediate': 2,
        'Advanced': 3
    }
    
    JUNIOR_COLORS = {
        'Blue': '🔵 Blue (4–6) – New to tennis',
        'Red': '🔴 Red (6–8) – Rallying, volleying, serving',
        'Orange': '🟠 Orange (8–11) - Hitting from mid-court and learning tactics. Great for beginners and improvers.',
        'Green': '🟢 Green (11–14) - Playing on full-size courts with standard balls. All levels welcome, with drills matched to ability.'
    }
    
    SKILL_LEVEL_ORDER = ['Beginner', 'Improver', 'Intermediate', 'Advanced']
    
    ADULT_BOOKING_URL = "https://clubspark.lta.org.uk/VamosTennis/Coaching/Adult"
    JUNIOR_BOOKING_URL = "https://clubspark.lta.org.uk/VamosTennis/Coaching/Junior"
    
    BLOCK_CONFIGS = {
        'adults': {
            'title': 'Adult Courses',
            'group_by': 'Skill Level',
            'include_venue': True,
            'extra_content': None
        },
        'juniors': {
            'title': 'Term Time Junior Courses',
            'group_by': 'Venue',
            'include_venue': False,
            'extra_content': None  # Will be set dynamically
        }
    }
    
    def __init__(self, llm_helper: LLMHelper = None):
        # Optional LLM helper for creative content
        self.llm_helper = llm_helper
    
    def _format_course_item(self, course: pd.Series, include_venue: bool = True) -> str:
        """Format a single course as HTML list item"""
        venue = course.get('Venue', 'Unknown Venue')
        start_date = course.get('Formatted Start Date', course.get('Start Date', ''))
        time = self._format_time(course.get('Time', ''))
        duration = course.get('Duration Text', '')
        spots = course.get('Active Participants', 0)
        
        limited_spots = " <strong>(Limited spots!)</strong>" if spots >= 7 and spots < 10 else ""
        full_spots = " <strong>(Full!)</strong>" if spots >= 10 else ""
        
        if include_venue:
            return f'<li><strong>{venue}</strong> - starting {start_date} at {time} ({duration}){limited_spots}{full_spots}</li>'
        else:
            return f'<li>{start_date} at {time} ({duration}){limited_spots}{full_spots}</li>'
    
    def _generate_course_list(self, courses: pd.DataFrame, group_by: str = None, include_venue: bool = True) -> List[str]:
        """Generate HTML list items for courses with optional grouping"""
        html_parts = []
        
        if group_by:
            if group_by == 'Skill Level':
                # Sort by predefined skill level order
                grouped = courses.groupby(group_by)
                sorted_groups = []
                for group_name, group_courses in grouped:
                    if group_name != 'Unknown':
                        sorted_groups.append((group_name, group_courses))
                
                # Sort groups according to skill level order
                sorted_groups.sort(key=lambda x: self.SKILL_LEVEL_ORDER.index(x[0]) if x[0] in self.SKILL_LEVEL_ORDER else 999)
                
                for group_name, group_courses in sorted_groups:
                    html_parts.append(f'<h3>{group_name}</h3>')
                    
                    # Add level description (LLM helper handles its own fallback)
                    if self.llm_helper:
                        try:
                            level_description = self.llm_helper.generate_level_description(group_name)
                            if level_description:
                                html_parts.append(f'<p>{level_description}</p>')
                        except Exception as e:
                            print(f"LLM level description failed: {e}")
                    
                    html_parts.append('<ul>')
                    for _, course in group_courses.iterrows():
                        html_parts.append(self._format_course_item(course, include_venue))
                    html_parts.append('</ul>')
                    
                    # Add booking button for this skill level
                    booking_button = self.generate_booking_button(group_name, courses)
                    html_parts.append(booking_button)
            else:
                # For other grouping types, use default behavior
                grouped = courses.groupby(group_by)
                for group_name, group_courses in grouped:
                    if group_name == 'Unknown':
                        continue
                    html_parts.append(f'<h3>{group_name}</h3>')
                    html_parts.append('<ul>')
                    for _, course in group_courses.iterrows():
                        html_parts.append(self._format_course_item(course, include_venue))
                    html_parts.append('</ul>')
        else:
            html_parts.append('<ul>')
            for _, course in courses.iterrows():
                html_parts.append(self._format_course_item(course, include_venue))
            html_parts.append('</ul>')
        
        return html_parts
    
    def generate_course_block(self, courses: pd.DataFrame, block_type: str = 'adults') -> str:
        """Generate HTML block for courses with flexible configuration"""
        if courses.empty:
            return ""
        
        # Get configuration from class constants
        config = self.BLOCK_CONFIGS.get(block_type, self.BLOCK_CONFIGS['adults']).copy()
        
        # Set extra content for juniors dynamically
        if block_type == 'juniors':
            config['extra_content'] = self._generate_junior_explanation(courses)
        
        html_parts = [f'<h2>{config["title"]}</h2>']
        
        # # Add LLM-generated description if available
        # if self.llm_helper:
        #     try:
        #         description = self.llm_helper.generate_block_description(block_type)
        #         html_parts.append(f'<p>{description}</p>')
        #     except Exception as e:
        #         print(f"LLM description failed: {e}")
        
        # Add extra content (like junior age groups explanation)
        if config['extra_content']:
            html_parts.extend(config['extra_content'])
        
        # Generate course list (skip for juniors to avoid duplication)
        if block_type != 'juniors':
            html_parts.extend(self._generate_course_list(
                courses, 
                group_by=config['group_by'], 
                include_venue=config['include_venue']
            ))
        
        # Add booking button for junior courses
        if block_type == 'juniors':
            html_parts.append(self.generate_junior_booking_button())
        
        return '\n'.join(html_parts)
    
    def _generate_junior_explanation(self, courses: pd.DataFrame = None) -> List[str]:
        """Generate junior age groups explanation using course names from CSV"""
        if courses is None or courses.empty:
            # Fallback to static descriptions
            return [
                '<p><strong>Age Groups:</strong></p>',
                '<ul>',
                *[f'<li>{description}</li>' for description in self.JUNIOR_COLORS.values()],
                '</ul>'
            ]
        
        # Use course names directly from CSV
        course_names = []
        for _, course in courses.iterrows():
            course_name = course.get('Name', '')  # Use 'Name' column from CSV
            if course_name:
                course_names.append(course_name)
        
        if not course_names:
            # Fallback to static descriptions
            return [
                '<p><strong>Age Groups:</strong></p>',
                '<ul>',
                *[f'<li>{description}</li>' for description in self.JUNIOR_COLORS.values()],
                '</ul>'
            ]
        
        # Return both course names and age group descriptions
        return [
            '<p><strong>Age Groups:</strong></p>',
            '<ul>',
            *[f'<li>{description}</li>' for description in self.JUNIOR_COLORS.values()],
            '</ul>',
            '<p><strong>Available Courses:</strong></p>',
            '<ul>',
            *[f'<li>{name}</li>' for name in course_names],
            '</ul>'
        ]
    
    def generate_events_block(self, courses: pd.DataFrame) -> str:
        """Generate HTML block for events and special sessions"""
        if courses.empty:
            return ""
        
        html_parts = []
        
        # Add LLM-generated description if available
        if self.llm_helper:
            try:
                description = self.llm_helper.generate_block_description('events')
                html_parts.append(f'<p>{description}</p>')
            except Exception as e:
                print(f"LLM description failed: {e}")
        
        html_parts.extend(self._generate_course_list(courses, group_by=None, include_venue=True))
        
        return '\n'.join(html_parts)
    
    def _extract_earliest_date(self, courses_df: pd.DataFrame) -> str:
        """Extract the earliest start date from courses and format for booking URL"""
        if courses_df.empty:
            return "2025-08-03T00:00:00.000Z"  # Fallback date
        
        try:
            # Get the earliest start date
            earliest_date = courses_df['Start Date'].min()
            
            # Parse the date and format for URL
            if '/' in str(earliest_date):
                date_obj = datetime.strptime(str(earliest_date), '%d/%m/%Y')
            else:
                date_obj = datetime.strptime(str(earliest_date), '%Y-%m-%d')
            
            # Format as ISO string for URL
            return date_obj.strftime('%Y-%m-%dT00:00:00.000Z')
        except:
            return "2025-08-03T00:00:00.000Z"  # Fallback date
    
    def generate_booking_button(self, skill_level: str = None, courses_df: pd.DataFrame = None) -> str:
        """Generate booking button HTML with ClubSpark URL"""
        if skill_level and skill_level in self.SKILL_LEVELS:
            level_id = self.SKILL_LEVELS[skill_level]
            url = f"{self.ADULT_BOOKING_URL}?skill-level%5B%5D={level_id}&date-range[]=%22{self._extract_earliest_date(courses_df)}%22"
            button_text = f"Book {skill_level}"
        else:
            url = self.ADULT_BOOKING_URL
            button_text = "Book Your Place"
        
        return f'''
        <p style="text-align: center;">
            <a href="{url}" class="cta-button">{button_text}</a>
        </p>
        '''
    
    def generate_junior_booking_button(self) -> str:
        """Generate booking button HTML for junior courses"""
        return f'''
        <p style="text-align: center;">
            <a href="{self.JUNIOR_BOOKING_URL}" class="cta-button">Book Junior Courses</a>
        </p>
        '''
    
    def _format_time(self, time_str: str) -> str:
        """Convert 24-hour time to 12-hour format"""
        try:
            if ':' in time_str:
                hour, minute = time_str.split(':')
                hour = int(hour)
                if hour > 12:
                    return f"{hour-12}pm"
                elif hour == 12:
                    return "12pm"
                elif hour == 0:
                    return "12am"
                else:
                    return f"{hour}am"
            return time_str
        except:
            return time_str
    
    def generate_newsletter_html(self, blocks: List[str], subject: str = None, llm_helper: LLMHelper = None, custom_summary: str = None) -> str:
        """Combine all blocks into a complete newsletter HTML"""
        html_parts = ['<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; width: 100%; box-sizing: border-box; text-align: left;">']
        
        for block in blocks:
            if block.strip():
                html_parts.append(block)
        
        html_parts.append('</div>')
        
        # Generate the complete HTML first
        complete_html = '\n'.join(html_parts)
        
        # Add summary at the top if custom summary is provided
        if custom_summary:
            summary_html = f'''
        <div style="margin: 40px 0;">
          <p>{custom_summary}</p>
        </div>
        '''
            # Insert summary after the title but before the content
            html_parts = ['<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; width: 100%; box-sizing: border-box; text-align: left;">']
            if subject:
                html_parts.append(f'<h1>{subject}</h1>')
            html_parts.append(summary_html)
            
            for block in blocks:
                if block.strip():
                    html_parts.append(block)
            
            html_parts.append('</div>')
            complete_html = '\n'.join(html_parts)
        # Add summary at the top if LLM helper is available (fallback)
        elif llm_helper:
            try:
                summary_text = llm_helper.generate_newsletter_summary_from_html(complete_html)
                if summary_text:
                    summary_html = f'''
        <div style="margin: 40px 0;">
          <p>{summary_text}</p>
        </div>
        '''
                    # Insert summary after the title but before the content
                    html_parts = ['<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; width: 100%; box-sizing: border-box; text-align: left;">']
                    if subject:
                        html_parts.append(f'<h1>{subject}</h1>')
                    html_parts.append(summary_html)
                    
                    for block in blocks:
                        if block.strip():
                            html_parts.append(block)
                    
                    html_parts.append('</div>')
                    complete_html = '\n'.join(html_parts)
            except Exception as e:
                print(f"Error adding newsletter summary: {e}")
        
        return complete_html
    
