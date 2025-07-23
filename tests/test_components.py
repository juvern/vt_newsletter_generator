#!/usr/bin/env python3
"""
Test script for HTML Generator and LLM Helper components
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_processor import CSVProcessor
from html_generator import HTMLGenerator
from llm_helper import LLMHelper

def load_real_csv():
    """Load the real coaching export CSV file"""
    try:
        df = pd.read_csv('../coaching-export-22-July-2025-10_55.csv')
        print(f"✅ Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print("❌ CSV file not found. Using sample data instead.")
        return create_sample_data()
    except Exception as e:
        print(f"❌ Error loading CSV: {e}. Using sample data instead.")
        return create_sample_data()

def create_sample_data():
    """Create sample CSV data for testing (fallback)"""
    sample_data = {
        'Name': [
            'Belair Park Adult Beginner Course',
            'Dulwich Park Adult Intermediate Course', 
            'Belair Park Junior Red Ball Course',
            'Dulwich Park Junior Orange Ball Course',
            'Belair Park Drop-in Session',
            'Dulwich Park Tournament'
        ],
        'Status': ['Upcoming'] * 6,
        'Start Date': ['04/08/2025', '11/08/2025', '18/08/2025', '25/08/2025', '01/09/2025', '08/09/2025'],
        'Time': ['18:00', '19:00', '16:00', '17:00', '20:00', '14:00'],
        'Type': ['Adult', 'Adult', 'Junior', 'Junior', 'Drop-in', 'Event'],
        'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'Classes': [6, 6, 8, 8, 1, 1],
        'Active Participants': [8, 9, 6, 7, 4, 12]
    }
    
    return pd.DataFrame(sample_data)

def test_csv_processor():
    """Test CSV processor functionality"""
    print("🧪 Testing CSV Processor...")
    
    processor = CSVProcessor()
    raw_df = load_real_csv()
    
    # Test processing
    processed_df = processor._clean_data(raw_df)
    processed_df = processor._add_derived_columns(processed_df)
    
    print(f"✅ Processed {len(processed_df)} courses")
    print(f"   Venues: {processed_df['Venue'].unique()}")
    print(f"   Skill Levels: {processed_df['Skill Level'].unique()}")
    
    # Test content types
    content_types = processor.get_content_types(processed_df)
    print(f"   Content types available: {[k for k, v in content_types.items() if v['available']]}")
    
    # Show some sample data
    print(f"   Sample courses:")
    for i, row in processed_df.head(3).iterrows():
        print(f"     - {row['Name']} ({row['Skill Level']}) at {row['Venue']}")
    
    return processed_df

def test_html_generator(df):
    """Test HTML generator functionality"""
    print("\n🧪 Testing HTML Generator...")
    
    # Test without LLM (deterministic)
    generator = HTMLGenerator()
    processor = CSVProcessor()
    
    # Test adult block
    adult_courses = processor.get_courses_by_type(df, 'adults')
    adult_html = generator.generate_course_block(adult_courses, 'adults')
    print(f"✅ Adult block generated: {len(adult_html)} characters")
    
    # Test junior block
    junior_courses = processor.get_courses_by_type(df, 'juniors')
    junior_html = generator.generate_course_block(junior_courses, 'juniors')
    print(f"✅ Junior block generated: {len(junior_html)} characters")
    
    # Test events block
    event_courses = processor.get_courses_by_type(df, 'events')
    events_html = generator.generate_events_block(event_courses)
    print(f"✅ Events block generated: {len(events_html)} characters")
    
    # Test complete newsletter
    blocks = [adult_html, junior_html, events_html]
    newsletter_html = generator.generate_newsletter_html(blocks, "New Tennis Courses Available!")
    print(f"✅ Complete newsletter generated: {len(newsletter_html)} characters")
    
    # Test with LLM integration
    print("\n🧪 Testing HTML Generator with LLM...")
    llm_helper = LLMHelper()
    generator_with_llm = HTMLGenerator(llm_helper=llm_helper)
    
    # Test adult block with LLM descriptions
    adult_html_with_llm = generator_with_llm.generate_course_block(adult_courses, 'adults')
    print(f"✅ Adult block with LLM: {len(adult_html_with_llm)} characters")
    
    return newsletter_html

def test_llm_helper():
    """Test LLM helper functionality"""
    print("\n🧪 Testing LLM Helper...")
    
    helper = LLMHelper()  # Will use fallback if no API key
    
    # Test subject lines
    subject_lines = helper.generate_subject_lines(['adults', 'juniors'], 6)
    print(f"✅ Subject lines generated: {len(subject_lines)} options")
    for i, line in enumerate(subject_lines, 1):
        print(f"   {i}. {line}")
    
    # Test preview text
    preview_text = helper.generate_preview_text(['adults', 'juniors'], 6)
    print(f"✅ Preview text generated: {len(preview_text)} characters")
    print(f"   '{preview_text}'")
    
    # Test WhatsApp message
    sample_courses = [
        {'Venue': 'Belair Park', 'Formatted Start Date': '4 Aug 2025', 'Time': '6pm', 'Skill Level': 'Beginner'},
        {'Venue': 'Dulwich Park', 'Formatted Start Date': '11 Aug 2025', 'Time': '7pm', 'Skill Level': 'Intermediate'}
    ]
    whatsapp_msg = helper.generate_whatsapp_message(sample_courses, "https://clubspark.lta.org.uk/VamosTennis/Coaching/Adult")
    print(f"✅ WhatsApp message generated: {len(whatsapp_msg)} characters")
    print(f"   '{whatsapp_msg[:100]}...'")
    
    return subject_lines, preview_text, whatsapp_msg

def main():
    """Run all tests"""
    print("🚀 Testing Newsletter Generator Components\n")
    
    # Test CSV processor
    df = test_csv_processor()
    
    # Test HTML generator
    newsletter_html = test_html_generator(df)
    
    # Test LLM helper
    subject_lines, preview_text, whatsapp_msg = test_llm_helper()
    
    print("\n✅ All tests completed successfully!")
    print("\n📋 Summary:")
    print(f"   - Processed {len(df)} courses")
    print(f"   - Generated newsletter HTML ({len(newsletter_html)} chars)")
    print(f"   - Created {len(subject_lines)} subject line options")
    print(f"   - Generated WhatsApp message ({len(whatsapp_msg)} chars)")
    
    # Show sample output
    print("\n📄 Sample Newsletter HTML Preview:")
    print(newsletter_html[:500] + "..." if len(newsletter_html) > 500 else newsletter_html)

if __name__ == "__main__":
    main() 