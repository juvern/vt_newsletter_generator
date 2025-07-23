import streamlit as st
import pandas as pd
from csv_processor import CSVProcessor
from html_generator import HTMLGenerator
from llm_helper import LLMHelper
from url_generator import ClubSparkURLGenerator
from auth import check_password
import json
from typing import List, Dict, Any

# Page config
st.set_page_config(
    page_title="Vamos Tennis Newsletter Generator",
    page_icon="🎾",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize all components once"""
    csv_processor = CSVProcessor()
    url_generator = ClubSparkURLGenerator()
    
    # Get API key from Streamlit secrets
    api_key = st.secrets.get("openai_api_key", None)
    llm_helper = LLMHelper(api_key=api_key)
    
    html_generator = HTMLGenerator(llm_helper=llm_helper)
    return csv_processor, url_generator, llm_helper, html_generator

def main():
    st.title("🎾 Vamos Tennis Newsletter Generator")
    st.markdown("Generate HTML newsletters to copy and paste into Postman")
    
    # Check password first
    if not check_password():
        st.stop()
    
    # Initialize components
    csv_processor, url_generator, llm_helper, html_generator = init_components()
    
    # Main app flow
    app_flow(csv_processor, url_generator, html_generator, llm_helper)

def app_flow(csv_processor, url_generator, html_generator, llm_helper):
    """Single page app flow"""
    
    # Step 1: Data Input
    st.header("📊 Step 1: Data Input")
    
    # Courses Section
    st.subheader("🎾 Courses")
    
    # Generate ClubSpark URL
    courses_url = url_generator.get_courses_url()
    st.markdown(f"**Download your courses data:**")
    st.markdown(f"[📥 Click here to download CSV from ClubSpark]({courses_url})")
    st.info("Download the CSV file, then upload it below.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your ClubSpark courses CSV:",
        type=['csv'],
        help="Upload the CSV file you downloaded from ClubSpark"
    )
    
    courses_df = None
    available_content_types = []
    
    if uploaded_file is not None:
        try:
            # Process CSV
            courses_df = csv_processor.process_csv(uploaded_file)
            
            # Show summary
            st.success(f"✅ Processed {len(courses_df)} courses successfully!")
            
            # Show content types available
            content_types = csv_processor.get_content_types(courses_df)
            available_content_types = [k for k, v in content_types.items() if v['available']]
            
            st.markdown("**Available content types:**")
            for content_type in available_content_types:
                count = content_types[content_type]['count']
                st.markdown(f"- {content_type.title()}: {count} courses")
            
        except Exception as e:
            st.error(f"❌ Error processing CSV: {str(e)}")
    
    # Events Section
    st.subheader("🏆 Events")
    st.markdown("Add up to 3 events (optional):")
    
    events = []
    for i in range(3):
        with st.expander(f"Event {i+1}", expanded=(i==0)):
            st.markdown("**Event Details:**")
            st.markdown("*Examples you can copy and paste:*")
            st.markdown("""
            - **Summer Tournament** - Saturday 15th August, 2pm at Belair Park. Join us for a fun afternoon of tennis! Perfect for Improver players and above. Come solo or with a partner! Great opportunity to meet other players.
            
            - **Barclays Big Tennis Weekend** - Sunday 20th July, 10am-4pm at Dulwich Park. Fun is the name of the game! Join us for Adult Coaching taster session and Family Time where we will provide modified balls and rackets for the younger ones and coaches will be on hand to give you some pointers if you want them, games and more!
            
            - **Junior Holiday Camp** - Monday 22nd July to Friday 26th July, 9am-3pm at Belair Park. Fun and engaging tennis camps for ages 4-11. All equipment provided, no experience necessary!
            """)
            
            event_title = st.text_input(
                f"Event {i+1} Title", 
                key=f"event_title_{i}",
                placeholder="e.g., Summer Tournament"
            )

            event_description = st.text_area(
                f"Event {i+1} Description", 
                key=f"event_description_{i}",
                placeholder="e.g., Saturday 15th August, 2pm at Belair Park. Join us for a fun afternoon of tennis!",
                height=100,
                help="Include the date, time, location, and description"
            )
            
            event_url = st.text_input(
                f"Event {i+1} URL", 
                key=f"event_url_{i}",
                placeholder="https://..."
            )
            event_image = st.text_input(
                f"Event {i+1} Image URL (optional)", 
                key=f"event_image_{i}",
                placeholder="https://..."
            )
            
            if event_description:  # Only add if description is provided
                # Use actual title or fallback, but ensure we have a meaningful title
                final_title = event_title.strip() if event_title and event_title.strip() else f"Event {i+1}"
                events.append({
                    'id': f"event_{i+1}",  # Unique identifier
                    'title': final_title,
                    'url': event_url,
                    'image': event_image,
                    'description': event_description  # Store the full description
                })
    
    if events:
        st.success(f"✅ Added {len(events)} events")
    
    # Step 2: Content Order (only show if courses are loaded)
    if courses_df is not None:
        st.header("📝 Step 2: Content Order")
        
        # Initialize content order in session state if not exists
        if 'content_order' not in st.session_state:
            # Create default order
            default_order = ['adults']
            for content_type in available_content_types:
                if content_type != 'adults':
                    default_order.append(content_type)
            
            # Add events to order
            for event in events:
                default_order.append(event['id'])  # Use the ID directly since it's already formatted
            
            st.session_state.content_order = default_order
        else:
            # Update content order to include all current events
            # Keep existing course order
            course_order = [item for item in st.session_state.content_order if not item.startswith('event_')]
            
            # Add all current events to the end
            for event in events:
                event_key = event['id']  # Use the ID directly since it's already formatted
                if event_key not in course_order:
                    course_order.append(event_key)
            
            st.session_state.content_order = course_order
        
        # Display all content with reordering controls
        st.markdown("**Drag and drop or use Move Up/Down to reorder content:**")
        
        # Create a copy of the order for manipulation
        current_order = st.session_state.content_order.copy()
        
        for i, content_type in enumerate(current_order):
            col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
            
            with col1:
                st.write(f"{i+1}.")
            
            with col2:
                if content_type.startswith('event_'):
                    event_id = content_type.replace('event_', '')
                    # Find the actual event title from the events list
                    event_title = "Event"
                    for event in events:
                        if event['id'] == content_type:
                            event_title = event['title']
                            break
                    st.write(f"🏆 {event_title}")
                else:
                    st.write(f"🎾 {content_type.title()} Courses")
            
            with col3:
                if st.button("Move Up", key=f"up_{i}", disabled=(i==0)):
                    if i > 0:
                        current_order[i], current_order[i-1] = current_order[i-1], current_order[i]
                        st.session_state.content_order = current_order
                        st.rerun()
                
                if st.button("Move Down", key=f"down_{i}", disabled=(i==len(current_order)-1)):
                    if i < len(current_order) - 1:
                        current_order[i], current_order[i+1] = current_order[i+1], current_order[i]
                        st.session_state.content_order = current_order
                        st.rerun()
        
        # Update content_order for use in generation
        content_order = st.session_state.content_order
        
        # Step 3: Generate Newsletter HTML
        st.header("📄 Step 3: Generate Newsletter HTML")
        
        # Generate newsletter button
        if st.button("🎯 Generate Newsletter HTML", type="primary"):
            with st.spinner("Generating newsletter HTML..."):
                
                # Generate HTML blocks
                html_blocks = []
                
                # Debug: Show what we're working with
                st.info(f"📋 Content order: {content_order}")
                st.info(f"📋 Available events: {[e['id'] for e in events]}")
                
                try:
                    for content_type in content_order:
                        if content_type.startswith('event_'):
                            # Handle individual event
                            event = next((e for e in events if e['id'] == content_type), None)
                            if event:
                                event_html = generate_single_event_html(event, llm_helper)
                                if event_html:
                                    html_blocks.append(event_html)
                                else:
                                    st.warning(f"⚠️ Failed to generate HTML for event {content_type}")
                            else:
                                st.warning(f"⚠️ Event {content_type} not found in events list")
                        else:
                            # Generate course blocks
                            courses = courses_df[courses_df['Type'].str.lower() == content_type.rstrip('s')]
                            if not courses.empty:
                                course_html = html_generator.generate_course_block(courses, content_type)
                                if course_html:
                                    html_blocks.append(course_html)
                                else:
                                    st.warning(f"⚠️ Failed to generate HTML for course type {content_type}")
                            else:
                                st.warning(f"⚠️ No courses found for type {content_type}")
                    
                    # Combine into final newsletter HTML (without summary for now)
                    newsletter_html = html_generator.generate_newsletter_html(
                        html_blocks, 
                        subject=None,  # No subject yet
                        llm_helper=None,  # Don't auto-generate summary
                        custom_summary=None  # No summary yet
                    )
                    
                    if not newsletter_html:
                        raise ValueError("Failed to generate newsletter HTML")
                        
                except Exception as e:
                    st.error(f"❌ Error generating newsletter HTML: {str(e)}")
                    return
                
                # Store the HTML in session state
                st.session_state.newsletter_html = newsletter_html
                st.session_state.html_blocks = html_blocks  # Store the blocks too
                st.session_state.html_generated = True
                st.success("✅ Newsletter HTML generated successfully!")
                st.rerun()
        
        # Show HTML preview if generated
        if st.session_state.get('html_generated', False):
            st.subheader("📄 Newsletter HTML Preview")
            st.markdown("**Preview of the generated newsletter HTML:**")
            st.components.v1.html(st.session_state.newsletter_html, height=600, scrolling=True)
        
        # Step 4: Generate Subject, Preview & Summary (only if HTML is generated)
        if st.session_state.get('html_generated', False):
            st.header("✏️ Step 4: Generate Subject, Preview & Summary")
            
            # Initialize session state for generated content
            if 'subject_lines' not in st.session_state:
                st.session_state.subject_lines = ""
            if 'preview_text' not in st.session_state:
                st.session_state.preview_text = ""
            if 'newsletter_summary' not in st.session_state:
                st.session_state.newsletter_summary = ""
            if 'content_generated' not in st.session_state:
                st.session_state.content_generated = False
            
            # Button to generate subject, preview text, and newsletter summary
            if st.button("🎯 Generate Subject, Preview & Summary", type="primary"):
                with st.spinner("Generating subject, preview text, and newsletter summary..."):
                    # Get the stored HTML content
                    newsletter_html = st.session_state.newsletter_html
                    
                    # Generate from the full HTML content
                    try:
                        # Debug: Show what content we're working with
                        debug_text = llm_helper.debug_extract_text(newsletter_html)
                        st.info(f"📋 Debug: Extracted text length: {len(debug_text)} characters")
                        st.info(f"📋 Debug: First 300 chars: {debug_text[:300]}...")
                        
                        # Ensure all methods return strings, not None
                        subject = llm_helper.generate_subject_line(html_content=newsletter_html)
                        preview = llm_helper.generate_preview_text(html_content=newsletter_html)
                        summary = llm_helper.generate_newsletter_summary(html_content=newsletter_html)
                        
                        st.session_state.subject_lines = subject if subject else "🎾 New Tennis Courses Available!"
                        st.session_state.preview_text = preview if preview else "New courses and fun events this month"
                        st.session_state.newsletter_summary = summary if summary else "Check out what's coming up this month — from new tennis courses to help you improve your game!"
                        st.session_state.content_generated = True
                        st.success("✅ Subject, preview text, and summary generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error generating content: {str(e)}")
                        # Set fallback values
                        st.session_state.subject_lines = "🎾 New Tennis Courses Available!"
                        st.session_state.preview_text = "New courses and fun events this month"
                        st.session_state.newsletter_summary = "Check out what's coming up this month — from new tennis courses to help you improve your game!"
                        st.session_state.content_generated = True
                        st.rerun()
            
            # Show info about regeneration
            if st.session_state.content_generated:
                st.info("💡 Click the button above again to regenerate with different results")
            
            # Only show subject and preview if they've been generated
            if st.session_state.content_generated:
                # Subject Line Selection
                st.subheader("📧 Subject Line")
                selected_subject = st.text_input(
                    "Subject line (you can edit this):",
                    value=st.session_state.subject_lines if st.session_state.subject_lines else "",
                    max_chars=100,
                    help="This is the email subject line"
                )
                
                # Preview Text
                st.subheader("📝 Preview Text")
                edited_preview = st.text_area(
                    "Preview text (you can edit this):",
                    value=st.session_state.preview_text,
                    max_chars=150,
                    help="This appears in email clients as a preview"
                )
                
                # Newsletter Summary
                st.subheader("📋 Newsletter Summary")
                edited_summary = st.text_area(
                    "Newsletter summary (you can edit this):",
                    value=st.session_state.newsletter_summary,
                    max_chars=300,
                    help="This appears at the top of the newsletter as an introduction"
                )
                
                # Step 5: Final Newsletter
                st.header("📄 Step 5: Final Newsletter")
                
                # Generate final newsletter button
                if st.button("🎯 Generate Final Newsletter", type="primary"):
                    with st.spinner("Generating final newsletter..."):
                        
                        # Use the stored HTML blocks
                        html_blocks = st.session_state.html_blocks
                        
                        # Add subject and summary to the existing HTML
                        final_newsletter_html = html_generator.generate_newsletter_html(
                            html_blocks, 
                            selected_subject, 
                            llm_helper=None,  # Don't auto-generate summary
                            custom_summary=edited_summary if edited_summary.strip() else None
                        )
                        
                        # Create JSON output
                        newsletter_json = {
                            "subject": selected_subject,
                            "content": final_newsletter_html,
                            "preview_text": edited_preview
                        }
                        
                        st.success("✅ Final newsletter generated successfully!")
                        
                        # Display results
                        st.subheader("📋 Results")
                        
                        # Tabs for different outputs
                        tab1, tab2, tab3 = st.tabs(["📄 Newsletter Preview", "📋 JSON Output", "📱 WhatsApp Message"])
                        
                        with tab1:
                            st.markdown("**Newsletter Preview:**")
                            st.components.v1.html(final_newsletter_html, height=600, scrolling=True)
                        
                        with tab2:
                            st.markdown("**Copy this JSON for Postman:**")
                            json_str = json.dumps(newsletter_json, indent=2)
                            st.code(json_str, language="json")
                            
                        
                        with tab3:
                            st.markdown("**WhatsApp Message:**")
                            st.info("WhatsApp message generation has been removed from this version.")
    
    
    else:
        st.info("📊 Upload your courses CSV to continue...")

def generate_single_event_html(event: Dict, llm_helper: LLMHelper = None) -> str:
    """Generate HTML for a single event with user description or LLM-generated description"""
    event_title = event.get('title', 'Special Event')
    html_parts = [f'<div style="margin: 40px 0;">']
    html_parts.append(f'<h2>{event_title}</h2>')
    
    if event.get('image'):
        html_parts.append(f'<img src="{event["image"]}" alt="{event_title}" style="width: 100%; max-width: 600px; margin: 10px auto; display: block;" />')
    
    # Always try LLM generation first, with user description as input
    event_info = {
        'description': event.get('description', '')  # Only pass the user description
    }
    
    description = ""
    if llm_helper:
        try:
            description = llm_helper.generate_event_description(event_info)
        except Exception as e:
            print(f"LLM event description failed: {e}")
    
    # Add description if we have one
    if description:
        html_parts.append(f'<p>{description}</p>')
    
    if event.get('url'):
        html_parts.append(f'''
        <p style="text-align: center;">
            <a href="{event["url"]}" class="cta-button">Book Your Spot</a>
        </p>
        ''')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)

def generate_events_html(events: List[Dict]) -> str:
    """Generate HTML for multiple events (legacy function)"""
    html_parts = ['<h2>🏆 Special Events</h2>']
    
    for event in events:
        html_parts.append('<div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">')
        
        if event.get('image'):
            html_parts.append(f'<img src="{event["image"]}" style="max-width: 100%; height: auto; margin-bottom: 10px;">')
        
        html_parts.append(f'<h3>{event["title"]}</h3>')
        html_parts.append(f'<p><strong>When:</strong> {event["date"]}</p>')
        
        if event.get('url'):
            html_parts.append(f'<a href="{event["url"]}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">Learn More</a>')
        
        html_parts.append('</div>')
    
    return '\n'.join(html_parts)

if __name__ == "__main__":
    main() 