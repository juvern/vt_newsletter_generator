# 🎾 Vamos Tennis Newsletter Generator

Generates HTML newsletters from ClubSpark course data — automatically formats courses by skill level, adds participant count warnings, and drafts newsletter copy. There are two independent ways to use it, covered in their own sections below.

## 🤖 Two ways to build a newsletter

| | Streamlit app | Claude Code skill |
|---|---|---|
| **Interface** | Form-based web UI | Conversation, inside Claude Code |
| **Run with** | `streamlit run app.py` | `/newsletter` |
| **Courses CSV** | Required upload step | Optional — supports promo-only newsletters too |
| **Copy generation** | OpenAI API (`llm_helper.py`) | Claude drafts it directly in chat — no OpenAI key needed |
| **Editing copy** | Regenerate and re-click through steps | Iterate conversationally, or edit the HTML text directly |
| **Sending to Kit** | "Send to Kit" button | `send_to_kit.py`, after explicit confirmation in chat |

Both paths are fully independent — the skill has its own duplicated copy of `csv_processor.py` under `.claude/skills/newsletter/scripts/`, so nothing it does touches the running Streamlit app, and vice versa. They read the same `.streamlit/secrets.toml` for the Kit API key.

---

## 🖥 Streamlit App

### 🚀 Quick Start

**Installation**
```bash
pip install -r requirements.txt
```

**Setup** — add your OpenAI API key to `.streamlit/secrets.toml`:
```toml
openai_api_key = "your-api-key-here"
```

### 📋 Usage

**Normal mode** (with AI features — requires API key in secrets.toml):
```bash
streamlit run app.py
```

**Test mode** (no API calls, uses fallback text — good for testing the flow without spending tokens):
```bash
streamlit run app.py -- --test
# or
TEST_MODE=true streamlit run app.py
# or
python test_app.py
```

### 🔧 Features

**Course processing**
- Automatic skill level grouping (Beginner → Improver → Intermediate → Advanced)
- Participant count warnings: 7+ participants = "Limited spots!", 10+ = "Full!"
- Venue and time formatting (24h → 12h conversion)

**AI-generated content** (via OpenAI): course descriptions by skill level, subject lines, preview text, event descriptions, newsletter summaries.

**Export options**: HTML preview, JSON output for Kit/Postman, contact list reminder for ClubSpark exports.

### 📁 Workflow

1. **Upload CSV** — download courses from ClubSpark and upload
2. **Add Events** — optional events with custom descriptions
3. **Content Order** — drag & drop to reorder newsletter sections
4. **Generate HTML** — creates newsletter with course listings
5. **Generate Metadata** — AI creates subject lines and summaries
6. **Final Newsletter** — complete HTML + JSON for distribution

### 🧪 Test Mode Fallbacks

- **Subject Line**: "🎾 New Courses Available!"
- **Preview Text**: "New courses and fun events this July"
- **Summary**: "Check out what's coming up this month — from new tennis courses to help you improve your game!"
- **Level Descriptions**: Predefined text for each skill level
- **Event Descriptions**: Standard tournament text

### 🔒 Security

The app includes password protection via `auth.py`. Set your password in the Streamlit secrets:
```toml
password = "your-secure-password"
```

### ⚙️ Customization

- Modify fallback text in `llm_helper.py`
- Adjust participant thresholds in `html_generator.py`
- Update booking URLs in class constants

---

## 💬 Claude Code Skill

A conversational alternative to the app, for use from inside Claude Code in this repo. Instead of a fixed form, you talk through the courses CSV (optional) and any events, Claude drafts the blurbs, subject line, and the newsletter HTML directly in the conversation — so you can iterate ("make this punchier", reorder sections, edit the HTML text directly) — then sends the finished newsletter to Kit as a draft broadcast once you explicitly confirm.

**Use it**: run `/newsletter` in Claude Code.

**Flow** (full detail in `.claude/skills/newsletter/SKILL.md`):
1. Optional courses CSV, parsed via `scripts/parse_courses.py`, plus any events/promotions
2. Agree content order
3. Draft blurbs in chat
4. Write the newsletter HTML directly, following the rules in SKILL.md
5. Draft subject line / preview text / summary in chat
6. Explicit confirmation, then send via `scripts/send_to_kit.py`

**Requirements**: `kit_api_key` in `.streamlit/secrets.toml` (same key the app uses). No OpenAI key needed — Claude writes the copy itself.

---

## 📊 CSV Format

Both paths use the same parsing logic (`csv_processor.py`, duplicated for the skill). The ClubSpark export must include these columns:
- `Name` — course name (venue and skill level are extracted from this automatically)
- `Status` — rows are filtered to only those marked `Upcoming`
- `Type` — `Adult` or `Junior`
- `Day` — e.g. `Saturday`
- `Start Date`, `Time`
- `Classes` — number of weeks (used to build the duration text)
- `Active Participants` — used for the "Limited spots!" / "Full!" warnings

## 📞 Contact Integration

Both paths end with the same reminder: download the contact list from ClubSpark (Participants/Members section export) and import it into Kit before actually sending, so the broadcast reaches everyone.

## 🛠 File Structure

```
newsletter_generator/
├── app.py                 # Main Streamlit app
├── html_generator.py      # HTML formatting logic
├── csv_processor.py       # CSV parsing and validation
├── llm_helper.py          # OpenAI API integration
├── url_generator.py       # ClubSpark URL generation
├── auth.py                # Password protection
├── test_app.py            # Test mode launcher
├── requirements.txt       # Dependencies
└── .claude/skills/newsletter/   # Claude Code skill
    ├── SKILL.md                 # Flow + HTML construction rules
    └── scripts/
        ├── csv_processor.py     # Duplicated, not imported — keeps the skill independent of app.py
        ├── parse_courses.py     # CSV -> display-ready JSON for the skill's HTML
        └── send_to_kit.py       # Posts the finished newsletter to Kit as a draft broadcast
```
