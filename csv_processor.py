import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Any

class CSVProcessor:
    """Handles CSV processing and data validation deterministically"""
    
    def __init__(self):
        self.required_columns = ['Name', 'Status', 'Start Date', 'Time', 'Type', 'Day', 'Classes', 'Active Participants']
        self.venue_patterns = {
            'belair': 'Belair Park',
            'dulwich': 'Dulwich Park'
        }
        self.skill_levels = {
            'beginner': 'Beginner',
            'improver': 'Improver', 
            'intermediate': 'Intermediate',
            'advanced': 'Advanced'
        }
    
    def process_csv(self, file) -> pd.DataFrame:
        """Process uploaded CSV file with validation"""
        try:
            # Read CSV
            df = pd.read_csv(file, encoding='utf-8')
            
            # Validate required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Filter for upcoming programs only
            df = df[df['Status'].str.lower() == 'upcoming'].copy()
            
            if df.empty:
                raise ValueError("No upcoming programs found in CSV")
            
            # Clean and standardize data
            df = self._clean_data(df)
            
            # Add derived columns
            df = self._add_derived_columns(df)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error processing CSV: {str(e)}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize CSV data"""
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Clean string columns
        string_columns = ['Name', 'Status', 'Type', 'Day']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Convert numeric columns
        numeric_columns = ['Classes', 'Active Participants']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns for easier processing"""
        # Extract venue from name
        df['Venue'] = df['Name'].apply(self._extract_venue)
        
        # Extract skill level from name
        df['Skill Level'] = df['Name'].apply(self._extract_skill_level)
        
        # Determine if limited spots
        df['Limited Spots'] = df['Active Participants'] > 8
        
        # Format start date
        df['Formatted Start Date'] = df['Start Date'].apply(self._format_date)
        
        # Calculate duration text
        df['Duration Text'] = df['Classes'].apply(lambda x: f"{x} weeks" if x > 1 else f"{x} week")
        
        return df
    
    def _extract_venue(self, name: str) -> str:
        """Extract venue from course name deterministically"""
        name_lower = name.lower()
        
        if 'belair' in name_lower:
            return 'Belair Park'
        elif 'dulwich' in name_lower:
            return 'Dulwich Park'
        else:
            return 'Unknown Venue'
    
    def _extract_skill_level(self, name: str) -> str:
        """Extract skill level from course name deterministically"""
        name_lower = name.lower()
        
        if 'beginner' in name_lower:
            return 'Beginner'
        elif 'improver' in name_lower:
            return 'Improver'
        elif 'intermediate' in name_lower:
            return 'Intermediate'
        elif 'advanced' in name_lower:
            return 'Advanced'
        else:
            return 'Unknown'
    
    def _format_date(self, date_str: str) -> str:
        """Format date string consistently"""
        try:
            # Handle different date formats
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            else:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            return date_obj.strftime('%d %B %Y')
        except:
            return date_str
    
    def get_content_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get available content types from processed data"""
        content_types = {
            'adults': {
                'available': False,
                'count': 0,
                'levels': []
            },
            'juniors': {
                'available': False,
                'count': 0,
                'levels': []
            },
            'events': {
                'available': False,
                'count': 0
            },
            'drop_ins': {
                'available': False,
                'count': 0
            }
        }
        
        # Check for adult courses
        adult_courses = df[df['Type'].str.lower() == 'adult']
        if not adult_courses.empty:
            content_types['adults']['available'] = True
            content_types['adults']['count'] = len(adult_courses)
            content_types['adults']['levels'] = adult_courses['Skill Level'].unique().tolist()
        
        # Check for junior courses
        junior_courses = df[df['Type'].str.lower() == 'junior']
        if not junior_courses.empty:
            content_types['juniors']['available'] = True
            content_types['juniors']['count'] = len(junior_courses)
        
        # Check for events (sessions with specific themes or one-off events)
        event_courses = df[
            (df['Type'].str.lower().str.contains('event|session|drop', na=False)) |
            (df['Classes'] == 1)
        ]
        if not event_courses.empty:
            content_types['events']['available'] = True
            content_types['events']['count'] = len(event_courses)
        
        return content_types
    
    def get_courses_by_type(self, df: pd.DataFrame, content_type: str) -> pd.DataFrame:
        """Get courses filtered by content type"""
        if content_type == 'adults':
            return df[df['Type'].str.lower() == 'adult']
        elif content_type == 'juniors':
            return df[df['Type'].str.lower() == 'junior']
        elif content_type == 'events':
            return df[
                (df['Type'].str.lower().str.contains('event|session|drop', na=False)) |
                (df['Classes'] == 1)
            ]
        else:
            return pd.DataFrame() 