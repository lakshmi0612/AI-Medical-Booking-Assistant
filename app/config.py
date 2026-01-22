import os
import streamlit as st

class Config:
    # API Keys - Read from Streamlit secrets
    try:
        GROQ_API_KEY = st.secrets["groq"]["api_key"]
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
        EMAIL_SENDER = st.secrets["email"]["sender"]
        EMAIL_PASSWORD = st.secrets["email"]["password"]
    except:
        # Fallback to environment variable if secrets not available
        from dotenv import load_dotenv
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        EMAIL_SENDER = os.getenv("EMAIL_SENDER")
        EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    # Model
    GROQ_MODEL = "llama-3.3-70b-versatile"
    
    # RAG Settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Booking Types
    BOOKING_TYPES = [
        "General Consultation",
        "Pediatrics",
        "Cardiology",
        "Dermatology",
        "Orthopedics",
        "Dental"
    ]
    
    # Working Hours
    WORKING_HOURS = {
        "start": "09:00",
        "end": "18:00"
    }
    
    # Memory Settings
    MAX_MEMORY_MESSAGES = 20
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        missing = []
        
        if not Config.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if not Config.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not Config.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not Config.EMAIL_SENDER:
            missing.append("EMAIL_SENDER")
        if not Config.EMAIL_PASSWORD:
            missing.append("EMAIL_PASSWORD")
        
        if missing:
            st.error(f"❌ Missing configuration: {', '.join(missing)}")
            st.info("Please set these in your secrets.toml file")
            return False
        
        # Debug output
        st.sidebar.success(f"✅ API Key loaded: {Config.GROQ_API_KEY[:10]}...")
        return True