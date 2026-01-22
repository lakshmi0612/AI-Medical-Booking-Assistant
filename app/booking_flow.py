import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import streamlit as st
from app.config import Config

class BookingFlow:
    """Manages the booking conversation flow"""
    
    REQUIRED_FIELDS = ["name", "email", "phone", "booking_type", "date", "time"]
    
    def __init__(self):
        self.reset_booking()
    
    def reset_booking(self):
        """Reset booking state"""
        st.session_state.booking_data = {
            "name": None,
            "email": None,
            "phone": None,
            "booking_type": None,
            "date": None,
            "time": None
        }
        st.session_state.booking_confirmed = False
        st.session_state.awaiting_confirmation = False
    
    def extract_info(self, user_message: str) -> Dict:
        """Extract booking information from user message"""
        extracted = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, user_message)
        if email_match:
            extracted["email"] = email_match.group()
        
        # Extract phone (various formats)
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, user_message)
        if phone_match:
            extracted["phone"] = re.sub(r'[^\d+]', '', phone_match.group())
        
        # Extract date (YYYY-MM-DD or DD/MM/YYYY or variations)
        date_patterns = [
            r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b',  # DD-MM-YYYY
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, user_message)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    if '/' in date_str or '-' in date_str:
                        # Try different formats
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                extracted["date"] = parsed_date.strftime('%Y-%m-%d')
                                break
                            except:
                                continue
                except:
                    pass
        
        # Extract time (HH:MM format)
        time_pattern = r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9])\b'
        time_match = re.search(time_pattern, user_message)
        if time_match:
            extracted["time"] = time_match.group()
        
        # Extract booking type
        message_lower = user_message.lower()
        for booking_type in Config.BOOKING_TYPES:
            if booking_type.lower() in message_lower:
                extracted["booking_type"] = booking_type
                break
        
        # Extract name - more flexible pattern
        if "name is" in message_lower:
            name_match = re.search(r'name is (.+?)(?:\.|$)', user_message, re.IGNORECASE)
            if name_match:
                extracted["name"] = name_match.group(1).strip().title()
        elif "i'm" in message_lower or "i am" in message_lower:
            name_match = re.search(r"(?:i'm|i am) (.+?)(?:\.|$)", user_message, re.IGNORECASE)
            if name_match:
                extracted["name"] = name_match.group(1).strip().title()
        else:
            # If just a name is provided (common scenario when bot asks "What's your name?")
            # Check if message is likely just a name (2-3 words, starts with capital)
            words = user_message.strip().split()
            if 1 <= len(words) <= 4 and words[0][0].isupper():
                # Likely a name if no special keywords present
                if not any(keyword in message_lower for keyword in ['book', 'appointment', 'email', '@', 'phone', 'time', 'date', ':', 'http']):
                    extracted["name"] = user_message.strip().title()
        
        return extracted
    
    def update_booking_data(self, extracted: Dict):
        """Update booking data with extracted information"""
        for key, value in extracted.items():
            if key in st.session_state.booking_data and value:
                st.session_state.booking_data[key] = value
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        for field in self.REQUIRED_FIELDS:
            if not st.session_state.booking_data.get(field):
                missing.append(field)
        return missing
    
    def validate_booking_data(self) -> tuple[bool, str]:
        """Validate booking data"""
        data = st.session_state.booking_data
        
        # Validate email
        if data["email"]:
            email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
            if not re.match(email_pattern, data["email"]):
                return False, "Please provide a valid email address."
        
        # Validate phone
        if data["phone"]:
            if len(re.sub(r'[^\d]', '', data["phone"])) < 10:
                return False, "Please provide a valid phone number (at least 10 digits)."
        
        # Validate date - STRICT VALIDATION
        if data["date"]:
            try:
                booking_date = datetime.strptime(data["date"], '%Y-%m-%d')
                today = datetime.now().date()
                max_date = today + timedelta(days=90)
                
                if booking_date.date() < today:
                    return False, f"❌ Booking date cannot be in the past.\n\nThe date {data['date']} has already passed."
                    
                if booking_date.date() > max_date:
                    return False, f"❌ Booking date is too far in the future.\n\nBookings can only be made up to 90 days in advance.\nThe date {data['date']} is beyond our booking window."
                    
            except ValueError:
                return False, "Please provide date in YYYY-MM-DD format."
        
        # Validate time
        if data["time"]:
            try:
                booking_time = datetime.strptime(data["time"], '%H:%M').time()
                start_time = datetime.strptime(Config.WORKING_HOURS["start"], '%H:%M').time()
                end_time = datetime.strptime(Config.WORKING_HOURS["end"], '%H:%M').time()
                
                if not (start_time <= booking_time <= end_time):
                    return False, f"Please select a time between {Config.WORKING_HOURS['start']} and {Config.WORKING_HOURS['end']}."
            except:
                return False, "Please provide time in HH:MM format (e.g., 14:30)."
        
        return True, ""
    
    def get_confirmation_message(self) -> str:
        """Generate confirmation message"""
        data = st.session_state.booking_data
        return f"""
Please confirm your booking details:

👤 Name: {data['name']}
📧 Email: {data['email']}
📱 Phone: {data['phone']}
🏥 Appointment Type: {data['booking_type']}
📅 Date: {data['date']}
🕐 Time: {data['time']}

Is this information correct? Please reply with 'yes' to confirm or 'no' to cancel.
"""
    
    def generate_next_prompt(self) -> str:
        """Generate next prompt based on missing fields"""
        missing = self.get_missing_fields()
        
        if not missing:
            return None
        
        today = datetime.now().date()
        max_date = today + timedelta(days=90)
        
        prompts = {
            "name": "May I have your full name?",
            "email": "What's your email address?",
            "phone": "Please provide your phone number.",
            "booking_type": f"What type of appointment do you need? We offer: {', '.join(Config.BOOKING_TYPES)}",
            "date": f"What date would you prefer? (Format: YYYY-MM-DD)\n\n📅 Valid range: {today.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}",
            "time": f"What time works for you? (Format: HH:MM, between {Config.WORKING_HOURS['start']} and {Config.WORKING_HOURS['end']})"
        }
        
        return prompts.get(missing[0], "Please provide more information.")