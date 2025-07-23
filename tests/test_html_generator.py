#!/usr/bin/env python3
"""
Test script to generate HTML preview using HTMLGenerator
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from html_generator import HTMLGenerator
from llm_helper import LLMHelper
from csv_processor import CSVProcessor

def load_real_data():
    """Load and process real coaching data from CSV"""
    csv_file = "../coaching-export.csv"  # This is the correct filename
    
    try:
        # Load the CSV file using CSVProcessor
        processor = CSVProcessor()
        with open(csv_file, 'r') as f:
            processed_df = processor.process_csv(f)
        
        print(f"📊 Loaded and processed {len(processed_df)} courses from {csv_file}")
        return processed_df
        
    except FileNotFoundError:
        print(f"❌ File {csv_file} not found. Using sample data instead.")
        return create_sample_data()
    except Exception as e:
        print(f"❌ Error loading CSV: {e}. Using sample data instead.")
        return create_sample_data()

def create_sample_data():
    """Create sample course data for testing (fallback)"""
    data = {
        'Venue': ['Belair Park', 'Dulwich Park', 'Belair Park', 'Dulwich Park', 'Belair Park'],
        'Start Date': ['2025-07-27', '2025-08-04', '2025-08-05', '2025-08-04', '2025-08-05'],
        'Formatted Start Date': ['27 July 2025', '04 August 2025', '05 August 2025', '04 August 2025', '05 August 2025'],
        'Time': ['10:00', '18:00', '19:00', '17:00', '18:00'],
        'Duration Text': ['6 weeks', '4 weeks', '4 weeks', '4 weeks', '4 weeks'],
        'Skill Level': ['Beginner', 'Beginner', 'Improver', 'Improver', 'Intermediate'],
        'Type': ['adult', 'adult', 'adult', 'adult', 'adult'],
        'Active Participants': [5, 8, 12, 6, 9]
    }
    return pd.DataFrame(data)

def main():
    """Generate HTML preview"""
    print("🎾 Generating HTML preview...")
    
    # Load real data from CSV
    courses_df = load_real_data()
    print(f"📊 Data loaded with {len(courses_df)} courses")
    
    # Initialize components
    # Option 1: Use environment variable (recommended)
    # export OPENAI_API_KEY='your-api-key-here'
    llm_helper = LLMHelper()  # Will use fallback content if no API key
    
    # Option 2: Pass API key directly
    # llm_helper = LLMHelper(api_key='your-api-key-here')
    
    html_generator = HTMLGenerator(llm_helper)
    
    # Show data summary
    print(f"\n📋 Data Summary:")
    print(f"   Total courses: {len(courses_df)}")
    print(f"   Adult courses: {len(courses_df[courses_df['Type'].str.lower() == 'adult'])}")
    print(f"   Junior courses: {len(courses_df[courses_df['Type'].str.lower() == 'junior'])}")
    print(f"   Skill levels: {courses_df['Skill Level'].unique()}")
    print(f"   Venues: {courses_df['Venue'].unique()}")
    print(f"   Course types: {courses_df['Type'].unique()}")
    print(f"   Sample course data:")
    if len(courses_df) > 0:
        print(f"     First course: {courses_df.iloc[0].to_dict()}")
    
    # Generate adult courses block
    adult_courses = courses_df[courses_df['Type'].str.lower() == 'adult']
    print(f"   Adult courses found: {len(adult_courses)}")
    adult_html = html_generator.generate_course_block(adult_courses, 'adults')
    print(f"   Adult HTML length: {len(adult_html) if adult_html else 0}")
    
    # Generate junior courses block (empty for this sample)
    junior_courses = courses_df[courses_df['Type'].str.lower() == 'junior']
    print(f"   Junior courses found: {len(junior_courses)}")
    junior_html = html_generator.generate_course_block(junior_courses, 'juniors')
    print(f"   Junior HTML length: {len(junior_html) if junior_html else 0}")
    
    # Generate events block
    event_courses = courses_df[courses_df['Type'].str.contains('event', na=False)]
    print(f"   Event courses found: {len(event_courses)}")
    events_html = html_generator.generate_events_block(event_courses)
    print(f"   Events HTML length: {len(events_html) if events_html else 0}")
    
    # Test event description generation
    sample_event = {
        'title': 'August Social Tournament',
        'date': 'Saturday, 16 August, 4–6pm',
        'url': 'https://clubspark.lta.org.uk/VamosTennis/Coaching/Book/467cf618-e6c3-489f-ba93-28edc5a8994d',
        'description': 'Come solo or with a partner!'
    }
    
    print("\n🎪 Testing event description generation:")
    event_description = llm_helper.generate_event_description(sample_event)
    print(f"Generated description: {event_description}")
    
    # Combine all blocks
    blocks = []
    if adult_html:
        blocks.append(adult_html)
    if junior_html:
        blocks.append(junior_html)
    if events_html:
        blocks.append(events_html)
    
    # Generate complete newsletter
    newsletter_html = html_generator.generate_newsletter_html(blocks, "🎾 New Tennis Courses Available!", llm_helper)
    
    # Save to file
    output_file = "newsletter_preview.html"
    with open(output_file, 'w') as f:
        f.write(newsletter_html)
    
    print(f"✅ HTML generated and saved to: {output_file}")
    print("📄 Open the file in your browser to preview")
    
    # Also print a snippet
    print("\n📋 HTML Preview (first 500 chars):")
    print("-" * 50)
    print(newsletter_html[:500] + "...")
    print("-" * 50)

if __name__ == "__main__":
    main() 