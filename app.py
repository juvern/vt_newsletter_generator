import streamlit as st
import pandas as pd
import os
import sys
from csv_processor import CSVProcessor
from html_generator import HTMLGenerator
from llm_helper import LLMHelper
from url_generator import ClubSparkURLGenerator
# from auth import check_password

import json
import requests
from typing import List, Dict, Any

# Page config
st.set_page_config(
    page_title="Vamos Tennis Newsletter Generator",
    page_icon="🎾",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_components(test_mode: bool = False):
    """Initialize all components once"""
    csv_processor = CSVProcessor()
    url_generator = ClubSparkURLGenerator()
    
    if test_mode:
        # In test mode, pass None as API key to disable LLM calls
        llm_helper = LLMHelper(api_key=None)
    else:
        # Get API key from Streamlit secrets
        api_key = st.secrets.get("openai_api_key", None)
        llm_helper = LLMHelper(api_key=api_key)
    
    html_generator = HTMLGenerator(llm_helper=llm_helper)
    return csv_processor, url_generator, llm_helper, html_generator

def main():
    st.title("🎾 Vamos Tennis Newsletter Generator")
    st.markdown("Generate HTML newsletters to copy and paste into Postman")
    
    # Check password first (commented out for now)
    # if not check_password():
    #     st.stop()
    
    # Check if test mode is enabled via environment variable or command line
    test_mode = (
        os.getenv('TEST_MODE', 'false').lower() == 'true' or
        '--test' in sys.argv
    )
    
    # Initialize components with test mode parameter
    csv_processor, url_generator, llm_helper, html_generator = init_components(test_mode=test_mode)
    
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
    st.markdown("Add up to 5 events (optional):")

    events = []
    for i in range(5):
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
    
    # Step 2: Content Order (show if courses or events are available)
    if courses_df is not None or events:
        st.header("📝 Step 2: Content Order")

        # Initialize content order in session state if not exists
        if 'content_order' not in st.session_state:
            # Create default order — only include course types if CSV was uploaded
            default_order = []
            if courses_df is not None:
                default_order.append('adults')
                for content_type in available_content_types:
                    if content_type != 'adults':
                        default_order.append(content_type)
            
            # Add events to order
            for event in events:
                default_order.append(event['id'])  # Use the ID directly since it's already formatted
            
            st.session_state.content_order = default_order
        else:
            # Only update if there are new events that aren't already in the order
            # Preserve the existing order and only add new events at the end
            existing_order = st.session_state.content_order.copy()
            existing_event_ids = [item for item in existing_order if item.startswith('event_')]
            current_event_ids = [event['id'] for event in events]
            
            # Remove events that are no longer present
            updated_order = [item for item in existing_order if not item.startswith('event_') or item in current_event_ids]
            
            # Add new events that aren't already in the order
            for event in events:
                event_key = event['id']
                if event_key not in updated_order:
                    updated_order.append(event_key)
            
            # Only update session state if the order actually changed
            if updated_order != existing_order:
                st.session_state.content_order = updated_order
        
        # Display all content with reordering controls
        st.markdown("**Drag and drop or use Move Up/Down to reorder content:**")
        
        # Create a copy of the order for manipulation
        current_order = st.session_state.content_order.copy()

        for i, content_type in enumerate(current_order):
            col1, col2, col3 = st.columns([0.1, 0.75, 0.15])

            with col1:
                st.write(f"{i+1}.")

            with col2:
                if content_type.startswith('event_'):
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

        # Step 3: Generate Blurbs
        st.header("✏️ Step 3: Generate Blurbs")

        if st.button("🎯 Generate Blurbs", type="primary"):
            with st.spinner("Generating blurbs..."):
                captured_blurbs = {}
                for content_type in content_order:
                    if content_type.startswith('event_'):
                        event = next((e for e in events if e['id'] == content_type), None)
                        if event and llm_helper:
                            try:
                                captured_blurbs[content_type] = llm_helper.generate_event_description({'description': event.get('description', '')}) or ""
                            except Exception:
                                captured_blurbs[content_type] = ""
                        elif event:
                            captured_blurbs[content_type] = ""
                    elif content_type == 'adults' and courses_df is not None and llm_helper:
                        courses = courses_df[courses_df['Type'].str.lower() == 'adult']
                        for skill_level in courses['Skill Level'].dropna().unique():
                            if skill_level != 'Unknown':
                                try:
                                    captured_blurbs[f'adults_{skill_level}'] = llm_helper.generate_level_description(skill_level) or ""
                                except Exception:
                                    captured_blurbs[f'adults_{skill_level}'] = ""
                # Clear blurb widget state so text areas show fresh values
                for k in list(st.session_state.keys()):
                    if k.startswith('blurb_'):
                        del st.session_state[k]
                st.session_state.blurbs = captured_blurbs
                st.session_state.blurbs_generated = True
                st.session_state.html_generated = False
                st.rerun()

        if st.session_state.get('blurbs_generated') and st.session_state.get('blurbs'):
            st.success("✅ Blurbs generated — edit them below, then generate the HTML.")
            blurbs = st.session_state.blurbs
            # Display blurbs in the same order they appear in the HTML
            for content_type in content_order:
                if content_type.startswith('event_'):
                    if content_type in blurbs:
                        event = next((e for e in events if e['id'] == content_type), None)
                        label = event['title'] if event else content_type
                        st.text_area(f"📋 {label}", value=blurbs[content_type], key=f"blurb_{content_type}", height=100)
                elif content_type == 'adults':
                    for skill_level in html_generator.SKILL_LEVEL_ORDER:
                        key = f'adults_{skill_level}'
                        if key in blurbs:
                            st.text_area(f"🎾 Adult — {skill_level}", value=blurbs[key], key=f"blurb_{key}", height=80)

        # Step 4: Generate Newsletter HTML (only after blurbs are ready)
        if st.session_state.get('blurbs_generated'):
            st.header("📄 Step 4: Generate Newsletter HTML")

            if st.button("🎯 Generate Newsletter HTML", type="primary"):
                with st.spinner("Generating newsletter HTML..."):
                    html_blocks = []
                    # Read current text area values (edited by user) from session state
                    blurbs = st.session_state.get('blurbs', {})
                    current_blurbs = {k: st.session_state.get(f'blurb_{k}', v) for k, v in blurbs.items()}

                    try:
                        for content_type in content_order:
                            if content_type.startswith('event_'):
                                event = next((e for e in events if e['id'] == content_type), None)
                                if event:
                                    blurb = current_blurbs.get(content_type, "")
                                    event_html = generate_single_event_html(event, custom_blurb=blurb)
                                    if event_html:
                                        html_blocks.append(event_html)
                            else:
                                if courses_df is None:
                                    continue
                                courses = courses_df[courses_df['Type'].str.lower() == content_type.rstrip('s')]
                                if not courses.empty:
                                    block_blurbs = {k.replace('adults_', ''): v for k, v in current_blurbs.items() if k.startswith(f'{content_type}_')}
                                    course_html = html_generator.generate_course_block(courses, content_type, custom_blurbs=block_blurbs or None)
                                    if course_html:
                                        html_blocks.append(course_html)

                        newsletter_html = html_generator.generate_newsletter_html(html_blocks, subject=None, llm_helper=None, custom_summary=None)
                        if not newsletter_html:
                            raise ValueError("Failed to generate newsletter HTML")

                    except Exception as e:
                        st.error(f"❌ Error generating newsletter HTML: {str(e)}")
                        return

                    st.session_state.newsletter_html = newsletter_html
                    st.session_state.html_blocks = html_blocks
                    st.session_state.html_generated = True
                    st.success("✅ Newsletter HTML generated!")
                    st.rerun()

        if st.session_state.get('html_generated', False):
            st.subheader("📄 Newsletter Preview")
            st.components.v1.html(st.session_state.newsletter_html, height=600, scrolling=True)

        # Step 5: Generate Subject, Preview & Summary (only if HTML is generated)
        if st.session_state.get('html_generated', False):
            st.header("✏️ Step 5: Generate Subject, Preview & Summary")

            if 'subject_lines' not in st.session_state:
                st.session_state.subject_lines = ""
            if 'preview_text' not in st.session_state:
                st.session_state.preview_text = ""
            if 'newsletter_summary' not in st.session_state:
                st.session_state.newsletter_summary = ""
            if 'content_generated' not in st.session_state:
                st.session_state.content_generated = False

            if st.button("🎯 Generate Subject, Preview & Summary", type="primary"):
                with st.spinner("Generating subject, preview text, and newsletter summary..."):
                    # Build a structured content summary — specific enough for good copy, no raw timings
                    summary_lines = []
                    for content_type in content_order:
                        if content_type.startswith('event_'):
                            event = next((e for e in events if e['id'] == content_type), None)
                            if event:
                                summary_lines.append(f"Event: {event['title']} — {event.get('description', '').split('.')[0]}")
                        elif content_type == 'adults' and courses_df is not None:
                            courses = courses_df[courses_df['Type'].str.lower() == 'adult']
                            levels = [lvl for lvl in html_generator.SKILL_LEVEL_ORDER if lvl in courses['Skill Level'].values]
                            if levels:
                                summary_lines.append(f"Adult courses: {', '.join(levels)}")
                        elif content_type == 'juniors' and courses_df is not None:
                            summary_lines.append("Junior courses available")
                    content_summary = "\n".join(summary_lines)

                    try:
                        subject = llm_helper.generate_subject_line(content_summary=content_summary)
                        preview = llm_helper.generate_preview_text(content_summary=content_summary)
                        summary = llm_helper.generate_newsletter_summary(content_summary=content_summary)

                        st.session_state.subject_lines = subject if subject else "🎾 New Tennis Courses Available!"
                        st.session_state.preview_text = preview if preview else "New courses and fun events this month"
                        st.session_state.newsletter_summary = summary if summary else "Check out what's coming up this month — from new tennis courses to help you improve your game!"
                        st.session_state.content_generated = True
                        st.success("✅ Subject, preview text, and summary generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error generating content: {str(e)}")
                        st.session_state.subject_lines = "🎾 New Tennis Courses Available!"
                        st.session_state.preview_text = "New courses and fun events this month"
                        st.session_state.newsletter_summary = "Check out what's coming up this month — from new tennis courses to help you improve your game!"
                        st.session_state.content_generated = True
                        st.rerun()

            if st.session_state.content_generated:
                st.info("💡 Click the button above again to regenerate with different results")

            if st.session_state.content_generated:
                st.subheader("📧 Subject Line")
                selected_subject = st.text_input(
                    "Subject line (you can edit this):",
                    value=st.session_state.subject_lines if st.session_state.subject_lines else "",
                    max_chars=100,
                    help="This is the email subject line"
                )

                st.subheader("📝 Preview Text")
                edited_preview = st.text_area(
                    "Preview text (you can edit this):",
                    value=st.session_state.preview_text,
                    max_chars=150,
                    help="This appears in email clients as a preview"
                )

                st.subheader("📋 Newsletter Summary")
                edited_summary = st.text_area(
                    "Newsletter summary (you can edit this):",
                    value=st.session_state.newsletter_summary,
                    max_chars=500,
                    help="This appears at the top of the newsletter as an introduction"
                )

                # Step 6: Final Newsletter
                st.header("📄 Step 6: Final Newsletter")

                if st.button("🎯 Generate Final Newsletter", type="primary"):
                    with st.spinner("Generating final newsletter..."):
                        final_newsletter_html = html_generator.generate_newsletter_html(
                            st.session_state.html_blocks,
                            selected_subject,
                            llm_helper=None,
                            custom_summary=edited_summary if edited_summary.strip() else None
                        )
                        st.session_state.final_newsletter_json = {
                            "subject": selected_subject,
                            "content": final_newsletter_html,
                            "preview_text": edited_preview
                        }
                        st.session_state.final_generated = True
                        st.rerun()

                if st.session_state.get('final_generated'):
                    newsletter_json = st.session_state.final_newsletter_json
                    st.success("✅ Final newsletter generated successfully!")

                    tab1, tab2 = st.tabs(["📄 Newsletter Preview", "📋 JSON Output"])
                    with tab1:
                        st.components.v1.html(newsletter_json["content"], height=600, scrolling=True)
                    with tab2:
                        st.code(json.dumps(newsletter_json, indent=2), language="json")

                    st.subheader("📤 Send to Kit")
                    st.info("This will create a **draft broadcast** in Kit. You can review and send it from the Kit dashboard.")
                    if st.button("🚀 Send to Kit", type="primary"):
                        kit_api_key = st.secrets.get("kit_api_key", "")
                        if not kit_api_key:
                            st.error("❌ Kit API key not found in secrets.toml")
                        else:
                            with st.spinner("Sending to Kit..."):
                                try:
                                    response = requests.post(
                                        "https://api.convertkit.com/v4/broadcasts",
                                        headers={
                                            "Content-Type": "application/json",
                                            "X-Kit-Api-Key": kit_api_key,
                                        },
                                        json=newsletter_json,
                                        timeout=15,
                                    )
                                    if response.status_code in (200, 201):
                                        st.success("✅ Broadcast created in Kit!")
                                    else:
                                        st.error(f"❌ Kit API error {response.status_code}: {response.text}")
                                except Exception as e:
                                    st.error(f"❌ Request failed: {str(e)}")

                    st.subheader("📋 Next Steps")
                    st.info("""
                    📞 **Don't forget to import ClubSpark's contact list!**

                    After sending to Kit, download the contact list from ClubSpark to import into Kit before sending. This ensures we're sending to all our members.
                    """)
                        
    
    
    else:
        st.info("📊 Add at least one event or upload a courses CSV to continue...")

def generate_single_event_html(event: Dict, llm_helper: LLMHelper = None, custom_blurb: str = None) -> str:
    """Generate HTML for a single event. Uses custom_blurb if provided, otherwise calls LLM."""
    event_title = event.get('title', 'Special Event')
    html_parts = [f'<div style="margin: 40px 0;">']
    html_parts.append(f'<h2>{event_title}</h2>')

    if event.get('image'):
        html_parts.append(f'<img src="{event["image"]}" alt="{event_title}" style="width: 100%; max-width: 600px; margin: 10px auto; display: block;" />')

    description = ""
    if custom_blurb is not None:
        description = custom_blurb
    elif llm_helper:
        try:
            description = llm_helper.generate_event_description({'description': event.get('description', '')}) or ""
        except Exception as e:
            print(f"LLM event description failed: {e}")

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