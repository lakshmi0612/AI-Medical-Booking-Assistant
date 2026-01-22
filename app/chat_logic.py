from groq import Groq
from typing import List, Dict
import streamlit as st
from app.config import Config
from app.booking_flow import BookingFlow
from app.rag_pipline import RAG
import re
import json

class ChatLogic:
    """Main chat logic with intent detection and routing"""

    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.booking_flow = BookingFlow()
        self.tools = Tools()
        
        # Initialize booking mode state
        if 'booking_mode' not in st.session_state:
            st.session_state.booking_mode = None  # 'manual' or 'pdf'
        if 'pdf_uploaded' not in st.session_state:
            st.session_state.pdf_uploaded = False

    def detect_intent(self, message: str, chat_history: List[Dict]) -> str:
        """Detect user intent"""
        message_lower = message.lower()

        # Check for confirmation responses
        if st.session_state.get('awaiting_confirmation', False):
            if any(word in message_lower for word in ['yes', 'confirm', 'correct', 'right', 'yep', 'yeah']):
                return 'confirm_yes'
            elif any(word in message_lower for word in ['no', 'cancel', 'wrong', 'nope']):
                return 'confirm_no'
        
        # Check for greetings (at start of conversation)
        if len(chat_history) <= 2:
            greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
            if any(keyword in message_lower for keyword in greeting_keywords):
                return 'greeting'

        # Booking intent
        booking_keywords = ['book', 'appointment', 'schedule', 'reservation', 'need', 'want to see', 'visit', 'consultation']
        if any(keyword in message_lower for keyword in booking_keywords):
            return 'booking'
        
        # Check if currently in booking flow
        if st.session_state.get('booking_data'):
            missing_fields = self.booking_flow.get_missing_fields()
            if missing_fields:
                return 'booking'

        # Questions
        question_keywords = ['what', 'how', 'when', 'where', 'who', 'why', 'tell me', 'explain']
        if any(keyword in message_lower for keyword in question_keywords):
            return 'question'

        return 'general'

    def handle_message(self, message: str, chat_history: List[Dict]) -> str:
        """Route messages to correct handler"""
        intent = self.detect_intent(message, chat_history)

        if intent == 'greeting':
            return self.handle_greeting(message)
        elif intent == 'confirm_yes':
            return self.handle_booking_confirmation(True)
        elif intent == 'confirm_no':
            return self.handle_booking_confirmation(False)
        elif intent == 'booking':
            return self.handle_booking(message, chat_history)
        elif intent == 'question':
            return self.handle_question(message, chat_history)
        else:
            return self.handle_general(message, chat_history)
    
    def handle_greeting(self, message: str) -> str:
        """Handle greeting messages with appointment options"""
        greeting_response = """👋 Hello! Welcome to our Medical Center!

I'm here to help you book an appointment. We offer the following services:

🏥 **Available Appointment Types:**
1. General Consultation
2. Pediatrics
3. Cardiology
4. Dermatology
5. Orthopedics
6. Dental

📅 **Working Hours:** 9:00 AM - 6:00 PM (Monday to Saturday)

Would you like to book an appointment? Just let me know which type you need, or I can help answer any questions about our services!"""
        
        return greeting_response

    def handle_booking(self, message: str, chat_history: List[Dict]) -> str:
        """Handle booking flow with PDF or manual option"""
        message_lower = message.lower()
        
        # Step 1: Ask for booking mode if not set
        if st.session_state.booking_mode is None:
            # Check if user mentioned PDF or manual
            if 'pdf' in message_lower or 'file' in message_lower or 'upload' in message_lower:
                st.session_state.booking_mode = 'pdf'
                st.session_state.pdf_uploaded = False
                return """Great! Please upload your PDF file using the sidebar. 

📄 **Your PDF should contain:**
- Full Name
- Email Address
- Phone Number
- Appointment Type
- Preferred Date
- Preferred Time

Once you click "Process PDFs", I'll automatically extract and show you the details!"""
            
            elif 'manual' in message_lower or 'type' in message_lower or 'enter' in message_lower:
                st.session_state.booking_mode = 'manual'
                return "Perfect! Let's book your appointment manually. May I have your full name?"
            
            else:
                # First time - ask user to choose
                return """Would you like to book your appointment:

📄 **Type 'PDF'** - Upload a PDF with your details
✍️ **Type 'Manual'** - Enter details step by step

Please choose your preferred method."""
        
        # Step 2: Handle PDF mode (waiting for upload)
        if st.session_state.booking_mode == 'pdf':
            if not st.session_state.pdf_uploaded:
                # Still waiting for PDF
                return """⏳ Please upload your PDF using the sidebar first.

Click on "📄 Upload Documents" in the sidebar, select your file, and click "Process PDFs".

I'll automatically extract the details for you!"""
            else:
                # PDF already processed, extraction happened in sidebar
                # User might be providing missing fields manually
                if st.session_state.get('awaiting_confirmation'):
                    return "Please confirm with 'yes' or 'no'."
                
                # Extract any additional info from message
                extracted = self.booking_flow.extract_info(message)
                if extracted:
                    self.booking_flow.update_booking_data(extracted)
                    
                    missing = self.booking_flow.get_missing_fields()
                    if missing:
                        next_prompt = self.booking_flow.generate_next_prompt()
                        return f"Got it! {next_prompt}"
                    else:
                        st.session_state.awaiting_confirmation = True
                        return self.booking_flow.get_confirmation_message()
                else:
                    missing = self.booking_flow.get_missing_fields()
                    if missing:
                        return self.booking_flow.generate_next_prompt()
                    else:
                        st.session_state.awaiting_confirmation = True
                        return self.booking_flow.get_confirmation_message()
        
        # Step 3: Handle Manual mode
        if st.session_state.booking_mode == 'manual':
            extracted = self.booking_flow.extract_info(message)
            self.booking_flow.update_booking_data(extracted)

            # Validate current data
            is_valid, error_msg = self.booking_flow.validate_booking_data()
            if not is_valid:
                # If it's a date error, provide helpful guidance
                if "date" in error_msg.lower():
                    from datetime import datetime, timedelta
                    today = datetime.now().date()
                    max_date = today + timedelta(days=90)
                    error_msg += f"\n\n📅 **Valid date range:**\n"
                    error_msg += f"- From: **{today.strftime('%Y-%m-%d')}** (today)\n"
                    error_msg += f"- To: **{max_date.strftime('%Y-%m-%d')}** (90 days from now)\n\n"
                    error_msg += "Please provide a date in **YYYY-MM-DD** format within this range."
                return error_msg

            missing = self.booking_flow.get_missing_fields()
            if missing:
                next_prompt = self.booking_flow.generate_next_prompt()
                acknowledgment = ""
                if extracted:
                    ack_parts = []
                    if 'name' in extracted:
                        ack_parts.append(f"Great to meet you, {extracted['name']}!")
                    if 'email' in extracted:
                        ack_parts.append(f"Got your email: {extracted['email']}")
                    if 'phone' in extracted:
                        ack_parts.append(f"Phone number noted: {extracted['phone']}")
                    if 'booking_type' in extracted:
                        ack_parts.append(f"Appointment type: {extracted['booking_type']}")
                    if 'date' in extracted:
                        ack_parts.append(f"Date: {extracted['date']}")
                    if 'time' in extracted:
                        ack_parts.append(f"Time: {extracted['time']}")
                    
                    if ack_parts:
                        acknowledgment = " ".join(ack_parts) + "\n\n"
                
                # If no acknowledgment and asking same question, something went wrong
                if not acknowledgment and next_prompt:
                    return next_prompt
                
                return acknowledgment + next_prompt if next_prompt else acknowledgment
            else:
                st.session_state.awaiting_confirmation = True
                return self.booking_flow.get_confirmation_message()
    
    def extract_from_pdf(self) -> Dict:
        """Extract booking information from uploaded PDF using LLM (SIMPLIFIED - LIKE WORKING CODE)"""
        extracted = {}
        
        try:
            st.write("### 🔍 EXTRACTION DEBUG LOG")
            st.write("---")
            
            # Step 1: Check RAG
            st.write("**Step 1: Checking RAG system...**")
            if not self.tools.rag.is_ready():
                st.error("❌ RAG not ready")
                return {}
            st.success("✅ RAG is ready")
            
            # Step 2: Get PDF context using RAG query (like working code)
            st.write("\n**Step 2: Getting PDF context via RAG query...**")
            # Use a generic query to get PDF content
            rag_query = "booking appointment patient name email phone date time"
            pdf_context = self.tools.rag_query(rag_query, [])
            
            if not pdf_context or len(pdf_context) < 20:
                st.warning("⚠️ RAG query returned little content, trying raw text...")
                pdf_context = self.tools.rag.get_raw_text()
            
            if not pdf_context:
                st.error("❌ No PDF content found")
                return {}
            
            st.success(f"✅ Got {len(pdf_context)} characters of PDF content")
            st.text_area("📄 PDF Content:", pdf_context, height=150, key="debug_pdf_content")
            
            # Step 3: Clean text (remove formatting artifacts)
            st.write("\n**Step 3: Cleaning text...**")
            cleaned_text = pdf_context.replace('__', '').replace('**', '').replace('~~', '').replace('*', '')
            # Remove extra spaces in dates and times
            import re
            cleaned_text = re.sub(r'(\d{4})\s+[-/]\s*(\d{2})\s*[-/]\s*(\d{2})', r'\1-\2-\3', cleaned_text)
            cleaned_text = re.sub(r'(\d{1,2})\s*:\s*(\d{2})', r'\1:\2', cleaned_text)
            
            st.success("✅ Text cleaned")
            st.text_area("🧹 Cleaned Text:", cleaned_text, height=150, key="debug_cleaned_text")
            
            # Step 4: Simple LLM Extraction (EXACTLY like working code)
            st.write("\n**Step 4: Calling LLM for extraction...**")
            
            extraction_prompt = f"""
You are an information extraction assistant.

The text below contains clinic appointment booking details.
Extract the structured booking information.

Fields to extract:
- name            (patient name)
- email
- phone
- booking_type    (type of consultation or appointment)
- date
- time

Important rules:
- Return ONLY a valid JSON object
- Use null if a field is missing
- Do NOT guess or assume values
- Convert dates to YYYY-MM-DD format
- Convert time to HH:MM (24-hour format)

Field interpretation rules:
- "Mail" or "Email ID" or anything with @ means email
- "Contact number", "Mobile", or "Phone" means phone
- "Consultation", "Appointment", or "Visit" or "Type" means booking_type
- Doctor name is NOT the patient name
- Ignore words like "Preferred" or "Tentative"

Text:
{cleaned_text}

Return ONLY the JSON object, no other text.
"""
            
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a precise data extraction assistant. Return only valid JSON with null for missing values."},
                        {"role": "user", "content": extraction_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                raw_response = response.choices[0].message.content.strip()
                st.success(f"✅ LLM responded ({len(raw_response)} chars)")
                
                st.write("\n**Step 4: LLM Raw Response:**")
                st.code(raw_response, language="text")
                
                # Clean markdown-style JSON (from working code)
                if raw_response.startswith("```"):
                    raw_response = raw_response.replace("```json", "").replace("```", "").strip()
                    st.info("Removed markdown formatting")
                
                st.write("\n**Step 4.2: Cleaned Response:**")
                st.code(raw_response, language="text")
                
                # Parse JSON
                st.write("\n**Step 4: Parsing JSON...**")
                llm_extracted = json.loads(raw_response)
                st.success("✅ JSON parsed successfully")
                st.json(llm_extracted)
                
                # Ensure only expected keys (from working code)
                allowed_keys = {"name", "email", "phone", "booking_type", "date", "time"}
                cleaned_extraction = {k: llm_extracted.get(k) for k in allowed_keys}
                
                st.write("\n**Step 4.5: Cleaned Extraction Keys:**")
                st.json(cleaned_extraction)
                st.write(f"Number of keys: {len(cleaned_extraction)}")
                for k, v in cleaned_extraction.items():
                    st.write(f"  - {k}: {v} (type: {type(v).__name__})")
                
                # Step 5: Validate each field
                st.write("\n**Step 5: Validating fields...**")
                from datetime import datetime, timedelta
                
                # 1. Name
                if cleaned_extraction.get('name') and cleaned_extraction['name'] is not None:
                    name_str = str(cleaned_extraction['name']).strip()
                    if name_str and name_str.lower() not in ['null', 'none', 'n/a']:
                        extracted['name'] = name_str.title()
                        st.success(f"✅ Name: {extracted['name']}")
                
                # 2. Email
                if cleaned_extraction.get('email') and cleaned_extraction['email'] is not None:
                    email_str = str(cleaned_extraction['email']).strip().lower()
                    if email_str and email_str.lower() not in ['null', 'none', 'n/a'] and '@' in email_str:
                        extracted['email'] = email_str
                        st.success(f"✅ Email: {extracted['email']}")
                
                # 3. Phone
                if cleaned_extraction.get('phone') and cleaned_extraction['phone'] is not None:
                    phone_str = re.sub(r'[^\d+]', '', str(cleaned_extraction['phone']))
                    if phone_str and len(phone_str) >= 10:
                        extracted['phone'] = phone_str
                        st.success(f"✅ Phone: {extracted['phone']}")
                
                # 4. Booking Type
                if cleaned_extraction.get('booking_type') and cleaned_extraction['booking_type'] is not None:
                    booking_type = str(cleaned_extraction['booking_type']).strip()
                    if booking_type and booking_type.lower() not in ['null', 'none', 'n/a']:
                        for valid_type in Config.BOOKING_TYPES:
                            if valid_type.lower() == booking_type.lower() or booking_type.lower() in valid_type.lower():
                                extracted['booking_type'] = valid_type
                                st.success(f"✅ Type: {valid_type}")
                                break
                
                # 5. Date
                if cleaned_extraction.get('date') and cleaned_extraction['date'] is not None:
                    date_str = str(cleaned_extraction['date']).strip()
                    if date_str and date_str.lower() not in ['null', 'none', 'n/a']:
                        try:
                            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                            today = datetime.now().date()
                            max_date = today + timedelta(days=90)
                            
                            if parsed_date.date() < today:
                                extracted['date_error'] = f"The date {date_str} has already passed."
                            elif parsed_date.date() > max_date:
                                extracted['date_error'] = f"The date {date_str} is too far in the future."
                            else:
                                extracted['date'] = date_str
                                st.success(f"✅ Date: {date_str}")
                        except ValueError:
                            st.error(f"❌ Invalid date format: {date_str}")
                
                # 6. Time
                if cleaned_extraction.get('time') and cleaned_extraction['time'] is not None:
                    time_str = str(cleaned_extraction['time']).strip()
                    if time_str and time_str.lower() not in ['null', 'none', 'n/a']:
                        try:
                            time_obj = datetime.strptime(time_str, '%H:%M').time()
                            start_time = datetime.strptime(Config.WORKING_HOURS["start"], '%H:%M').time()
                            end_time = datetime.strptime(Config.WORKING_HOURS["end"], '%H:%M').time()
                            
                            if start_time <= time_obj <= end_time:
                                extracted['time'] = time_str
                                st.success(f"✅ Time: {time_str}")
                        except ValueError:
                            st.error(f"❌ Invalid time format: {time_str}")
                
                # Summary
                valid_fields = len([k for k in extracted.keys() if k != 'date_error'])
                st.write(f"\n**📊 Extracted {valid_fields}/6 fields**")
                st.json(extracted)
                
                return extracted
                
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON parsing failed: {e}")
                st.warning("⚠️ Trying regex fallback...")
                return self._regex_fallback_extraction(cleaned_text)
            except Exception as e:
                st.error(f"❌ LLM error: {e}")
                import traceback
                st.code(traceback.format_exc())
                return {}
                
        except Exception as e:
            st.error(f"❌ Extraction error: {e}")
            import traceback
            st.code(traceback.format_exc())
            return {}

    def _regex_fallback_extraction(self, raw_text: str) -> Dict:
        """Fallback regex extraction"""
        st.info("🔄 Using regex-based extraction...")
        extracted = {}
        
        # Email
        email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', raw_text.replace(' ', ''))
        if email_match:
            extracted['email'] = email_match.group().lower()
            st.success(f"✅ Email: {extracted['email']}")
        
        # Phone
        phone_match = re.search(r'\d{10,}', raw_text)
        if phone_match:
            extracted['phone'] = phone_match.group()
            st.success(f"✅ Phone: {extracted['phone']}")
        
        # Date
        date_match = re.search(r'(\d{4})\s*[-/]\s*(\d{2})\s*[-/]\s*(\d{2})', raw_text)
        if date_match:
            # Remove any spaces from the matched date
            date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            extracted['date'] = date_str
            st.success(f"✅ Date: {extracted['date']}")
        
        # Time
        time_match = re.search(r'\b([0-2]?[0-9]):([0-5][0-9])\b', raw_text)
        if time_match:
            extracted['time'] = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
            st.success(f"✅ Time: {extracted['time']}")
        
        # Booking Type
        for booking_type in Config.BOOKING_TYPES:
            if booking_type.lower() in raw_text.lower():
                extracted['booking_type'] = booking_type
                st.success(f"✅ Type: {booking_type}")
                break
        
        # Name
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        for line in lines:
            words = line.split()
            if (1 <= len(words) <= 4 and 
                line[0].isupper() and
                all(w.replace('.', '').replace(',', '').isalpha() for w in words) and
                '@' not in line and not any(c.isdigit() for c in line)):
                extracted['name'] = line.title()
                st.success(f"✅ Name: {extracted['name']}")
                break
        
        return extracted

    def handle_booking_confirmation(self, confirmed: bool) -> str:
        """Handle booking confirmation"""
        st.session_state.awaiting_confirmation = False

        if not confirmed:
            self.booking_flow.reset_booking()
            st.session_state.booking_mode = None
            st.session_state.pdf_uploaded = False
            return "Booking cancelled. Feel free to start a new booking whenever you're ready!"

        success, booking_id, message = self.tools.save_booking(st.session_state.booking_data)
        if not success:
            return f"❌ {message}\n\nPlease try again or contact support."

        subject, body = self.tools.format_confirmation_email(st.session_state.booking_data, booking_id)
        email_success, email_message = self.tools.send_email(st.session_state.booking_data['email'], subject, body)

        response = f"✅ Booking confirmed! Your booking ID is #{booking_id}\n\n"
        if email_success:
            response += "📧 A confirmation email has been sent.\n\n"
        else:
            response += f"⚠️ Booking saved, but email failed to send.\n\n"
        
        response += "Thank you for booking with us! 🏥"

        self.booking_flow.reset_booking()
        st.session_state.booking_mode = None
        st.session_state.pdf_uploaded = False
        
        return response

    def handle_question(self, message: str, chat_history: List[Dict]) -> str:
        """Handle questions - check RAG first"""
        if self.tools.rag.is_ready():
            rag_response = self.tools.rag_query(message, chat_history)
            if "couldn't find" not in rag_response.lower():
                return rag_response
        return self.get_llm_response(message, chat_history)

    def handle_general(self, message: str, chat_history: List[Dict]) -> str:
        """Handle general conversation"""
        return self.get_llm_response(message, chat_history)

    def get_llm_response(self, message: str, chat_history: List[Dict], system_prompt: str = None) -> str:
        """Get response from Groq LLM"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({"role": "system", "content": "You are a helpful medical appointment booking assistant."})

            recent_history = chat_history[-20:]
            for msg in recent_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            messages.append({"role": "user", "content": message})

            response = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"LLM Error: {str(e)}")
            return "I apologize, but I'm having trouble. Please try again."