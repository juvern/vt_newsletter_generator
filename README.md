# 🎾 Vamos Tennis Newsletter Generator

A Streamlit app for generating HTML newsletters from ClubSpark course data. Automatically formats courses by skill level, adds participant count warnings, and creates newsletter content with AI-generated descriptions.

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Setup
1. Add your OpenAI API key to `.streamlit/secrets.toml`:
```toml
openai_api_key = "your-api-key-here"
```

## 📋 Usage

### Normal Mode (With AI Features)
```bash
streamlit run app.py
```
- Uses OpenAI API for generating descriptions, subject lines, and summaries
- Requires API key in secrets.toml

### Test Mode (No AI Calls)
Perfect for testing the flow without using API tokens:

#### Option 1: Command Line Flag
```bash
streamlit run app.py -- --test
```

#### Option 2: Environment Variable
```bash
TEST_MODE=true streamlit run app.py
```

#### Option 3: Test Script
```bash
python test_app.py
```

## 🔧 Features

### Course Processing
- **Automatic skill level grouping** (Beginner → Improver → Intermediate → Advanced)
- **Participant count warnings**:
  - 7+ participants: "Limited spots!"
  - 10+ participants: "Full!"
- **Venue and time formatting** (24h → 12h conversion)

### AI-Generated Content
- Course descriptions by skill level
- Newsletter subject lines
- Preview text for emails
- Event descriptions
- Newsletter summaries

### Export Options
- HTML preview
- JSON output for Postman/email platforms
- Contact list reminder for ClubSpark exports

## 📁 Workflow

1. **Upload CSV**: Download courses from ClubSpark and upload
2. **Add Events**: Optional events with custom descriptions
3. **Content Order**: Drag & drop to reorder newsletter sections
4. **Generate HTML**: Creates newsletter with course listings
5. **Generate Metadata**: AI creates subject lines and summaries
6. **Final Newsletter**: Complete HTML + JSON for distribution

## 🧪 Test Mode Fallbacks

When running in test mode, the app uses these fallback values:

- **Subject Line**: "🎾 New Courses Available!"
- **Preview Text**: "New courses and fun events this July"
- **Summary**: "Check out what's coming up this month — from new tennis courses to help you improve your game!"
- **Level Descriptions**: Predefined text for each skill level
- **Event Descriptions**: Standard tournament text

## 📊 CSV Format

The app expects ClubSpark CSV exports with these columns:
- `Name`: Course name
- `Type`: Course type (adult/junior/event)
- `Skill Level`: Beginner/Improver/Intermediate/Advanced
- `Venue`: Location name
- `Start Date`: Course start date
- `Time`: Start time
- `Duration Text`: Course duration
- `Active Participants`: Number of enrolled participants

## 📞 Contact Integration

The app includes reminders to:
1. Download contact lists from ClubSpark
2. Export as CSV from Participants/Members section
3. Import to Kit for email distribution

## 🛠 Development

### File Structure
```
newsletter_generator/
├── app.py                 # Main Streamlit app
├── html_generator.py      # HTML formatting logic
├── csv_processor.py       # CSV parsing and validation
├── llm_helper.py         # OpenAI API integration
├── url_generator.py      # ClubSpark URL generation
├── auth.py               # Password protection
├── test_app.py           # Test mode launcher
└── requirements.txt      # Dependencies
```

## ⚙️ Configuration

### Customization
- Modify fallback text in `llm_helper.py`
- Adjust participant thresholds in `html_generator.py`
- Update booking URLs in class constants

## 🔒 Security

The app includes password protection via `auth.py`. Set your password in the Streamlit secrets:

```toml
password = "your-secure-password"
```