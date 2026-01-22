# 🏥 AI Booking Assistant

An intelligent chatbot for medical appointment booking with RAG capabilities, built with Streamlit, Groq API, and Supabase.

## ✨ Features

- **Conversational Booking**: Natural language appointment scheduling
- **RAG System**: Upload PDFs and ask questions about your documents
- **Smart Intent Detection**: Automatically routes queries to appropriate handlers
- **Email Confirmations**: Automatic booking confirmations via email
- **Admin Dashboard**: View, search, and export all bookings
- **Short-term Memory**: Maintains context for up to 25 messages
- **Data Validation**: Robust input validation with friendly error messages
- **Multi-specialty Support**: Handles various appointment types

## 🚀 Quick Start

### Prerequisites

1. **Groq API Key** (Free)
   - Sign up at [console.groq.com](https://console.groq.com)
   - Get your API key

2. **Supabase Account** (Free)
   - Sign up at [supabase.com](https://supabase.com)
   - Create a new project
   - Get your URL and anon key

3. **Gmail App Password** (for email notifications)
   - Enable 2FA on your Gmail account
   - Generate app password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ai-booking-assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Supabase Database**
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor
   - Copy and run the SQL from `db/schema.sql`

4. **Configure secrets**

Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
SUPABASE_URL = "your_supabase_url_here"
SUPABASE_KEY = "your_supabase_anon_key_here"
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password_here"
```

5. **Run the application**
```bash
streamlit run app/main.py
```

## 📁 Project Structure

```
ai-booking-assistant/
├── app/
│   ├── main.py                 # Main Streamlit app
│   ├── chat_logic.py           # Intent detection & routing
│   ├── booking_flow.py         # Booking conversation logic
│   ├── rag_pipeline.py         # PDF processing & RAG
│   ├── tools.py                # Tool implementations
│   ├── admin_dashboard.py      # Admin interface
│   └── config.py               # Configuration
├── db/
│   ├── database.py             # Supabase client
│   └── schema.sql              # Database schema
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .streamlit/
    └── secrets.toml            # API keys (create this)
```

## 🎯 How to Use

### For Users (Chat Mode)

1. **Start with a greeting**: Say "Hi" or "Hello"
   - Bot will welcome you and show available appointment types
   
2. **Book an appointment**: Choose your appointment type
   - Bot will ask for: name, email, phone, date, time
   - You can provide multiple details at once or one by one
   
3. **Confirm your booking**: Review details and say "yes"
   - Receive booking ID and email confirmation

Example conversation:
```
User: Hello
Bot: 👋 Hello! Welcome to our Medical Center!
     [Shows appointment types and working hours]

User: I need a cardiology appointment
Bot: Great! May I have your full name?

User: Lakshmi KN
Bot: Great to meet you, Lakshmi Kn! What's your email address?

User: lakshmi@example.com
Bot: Got your email! Please provide your phone number.

[... continues until all info collected ...]

Bot: Please confirm your booking details: [shows summary]
User: yes
Bot: ✅ Booking confirmed! Your booking ID is #1
     📧 Confirmation email sent!
```

### For Admins (Dashboard)

1. Switch to "Admin Dashboard" in sidebar
2. View all bookings in a table
3. Search by name or email
4. Export data to CSV

## 🛠️ Configuration

Edit `app/config.py` to customize:
- Booking types (appointment categories)
- Working hours
- Memory limit
- RAG chunk sizes

## 📧 Email Setup (Gmail)

1. Enable 2-Factor Authentication on Gmail
2. Generate App Password:
   - Go to Google Account → Security
   - Under "2-Step Verification", find "App passwords"
   - Generate new app password for "Mail"
   - Use this password in secrets.toml

## 🚀 Deployment (Streamlit Cloud)

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select `app/main.py` as the main file
   - Add secrets in "Advanced settings"
   - Deploy!

3. **Add Secrets in Streamlit Cloud**
   - Click "Advanced settings" during deployment
   - Paste your secrets.toml content
   - Deploy

## 📊 Features Checklist

- ✅ RAG with PDF upload
- ✅ Conversational booking flow
- ✅ Intent detection
- ✅ Multi-turn dialogue
- ✅ Short-term memory (25 messages)
- ✅ Data validation
- ✅ Confirmation before saving
- ✅ Supabase integration
- ✅ Email confirmations
- ✅ Admin dashboard
- ✅ Search & filter
- ✅ CSV export
- ✅ Error handling
- ✅ Tool calling (RAG, DB, Email)

## 🎨 Customization Tips

### Change Booking Domain
Edit `Config.BOOKING_TYPES` in `config.py`:
```python
BOOKING_TYPES = [
    "Haircut",
    "Hair Coloring",
    "Manicure",
    "Pedicure"
]
```

### Modify Working Hours
```python
WORKING_HOURS = {
    "start": "08:00",
    "end": "20:00"
}
```

### Switch LLM Model
```python
GROQ_MODEL = "llama-3.1-70b-versatile"  # or other Groq models
```

## 🐛 Troubleshooting

### "Database connection failed"
- Check Supabase URL and key in secrets.toml
- Verify database tables are created (run schema.sql)

### "Email authentication failed"
- Use App Password, not regular Gmail password
- Enable 2FA first

### "No text extracted from PDFs"
- Ensure PDFs contain actual text (not just images)
- Try different PDFs

### RAG not working
- Upload PDFs first via sidebar
- Click "Process PDFs" button
- Wait for success message

## 📝 Assignment Submission Checklist

- [ ] Code pushed to GitHub
- [ ] README with clear instructions
- [ ] Deployed on Streamlit Cloud
- [ ] Public URL working
- [ ] PPT presentation ready
- [ ] All features tested:
  - [ ] PDF upload & RAG
  - [ ] Booking flow
  - [ ] Email confirmation
  - [ ] Admin dashboard
  - [ ] Error handling

## 🤝 Support

For issues or questions:
1. Check this README
2. Review error messages carefully
3. Verify all API keys are correct
4. Test each component individually

## 📄 License

This project is for educational purposes (assignment submission).

## 🙏 Acknowledgments

- Groq for fast LLM inference
- Supabase for database hosting
- Streamlit for the amazing framework
- LangChain for RAG capabilities