import streamlit as st
from app.config import Config
from app.chat_logic import ChatLogic
from app.admin_dashboard import AdminDashboard
from app.tools import Tools

# Page config
st.set_page_config(
    page_title="AI Booking Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .main-title {
        text-align: center;
        color: #2c3e50;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'booking_data' not in st.session_state:
        st.session_state.booking_data = {
            "name": None,
            "email": None,
            "phone": None,
            "booking_type": None,
            "date": None,
            "time": None
        }
    if 'awaiting_confirmation' not in st.session_state:
        st.session_state.awaiting_confirmation = False
    if 'booking_confirmed' not in st.session_state:
        st.session_state.booking_confirmed = False
    if 'chat_logic' not in st.session_state:
        st.session_state.chat_logic = ChatLogic()
    if 'tools' not in st.session_state:
        st.session_state.tools = Tools()

def render_sidebar():
    """Render sidebar with PDF upload and info"""
    with st.sidebar:
        st.title("🏥 Medical Booking Assistant")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate",
            ["💬 Chat", "📊 Admin Dashboard"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # PDF Upload
        st.subheader("📄 Upload Documents")
        st.write("Upload PDFs for the assistant to reference")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if st.button("Process PDFs", type="primary", use_container_width=True):
                with st.spinner("Processing PDFs..."):
                    # FIXED: Use chat_logic.tools (same instance used for extraction)
                    success = st.session_state.chat_logic.tools.process_pdfs(uploaded_files)
                    
                    if success:
                        st.success(f"✅ Processed {len(uploaded_files)} PDF(s)")
                        
                        # FIXED: Get raw text from same tools instance
                        raw_text = st.session_state.chat_logic.tools.rag.get_raw_text()
                        
                        st.write("=" * 50)
                        st.write("### 📊 PDF PROCESSING DEBUG")
                        st.write("=" * 50)
                        st.write(f"**Raw text length:** {len(raw_text)} chars")
                        st.write(f"**Raw text empty?** {not raw_text}")
                        
                        if not raw_text:
                            st.error("❌ CRITICAL: Raw text is empty!")
                            st.stop()
                        
                        st.text_area("📄 Raw Text Preview:", raw_text[:500], height=150, key="pdf_raw_preview")
                        
                        # Check if booking PDF
                        booking_keywords = ['email', 'phone', 'dental', 'cardiology', 'appointment', 
                                          'pediatric', 'dermatology', 'orthopedic', 'consultation',
                                          'booking', 'patient', 'name', 'contact', 'mail', 'mobile',
                                          '@', 'date', 'time']
                        
                        is_booking_pdf = any(keyword in raw_text.lower() for keyword in booking_keywords)
                        
                        st.write(f"**Is booking PDF?** {is_booking_pdf}")
                        st.write(f"**Current booking mode:** {st.session_state.get('booking_mode', 'None')}")
                        
                        # FORCE extraction if looks like booking
                        if is_booking_pdf:
                            st.session_state.booking_mode = 'pdf'
                            st.write("✅ **Forced booking mode to 'pdf'**")
                            
                            st.write("=" * 50)
                            st.write("### 🤖 STARTING EXTRACTION")
                            st.write("=" * 50)
                            
                            # CRITICAL: Actually call the extraction
                            st.write("**Calling extract_from_pdf()...**")
                            
                            try:
                                extracted = st.session_state.chat_logic.extract_from_pdf()
                                
                                st.write("=" * 50)
                                st.write("### 📊 EXTRACTION COMPLETE")
                                st.write("=" * 50)
                                st.write(f"**Extracted type:** {type(extracted)}")
                                st.write(f"**Extracted keys:** {list(extracted.keys()) if extracted else 'None'}")
                                st.write(f"**Extracted values:**")
                                st.json(extracted)
                                
                            except Exception as e:
                                st.error(f"❌ EXTRACTION FAILED WITH ERROR:")
                                st.error(str(e))
                                import traceback
                                st.code(traceback.format_exc())
                                st.stop()
                            
                            # IMPROVED: Better field validation function
                            def is_valid_extracted_field(value):
                                """Check if extracted value is valid"""
                                if value is None:
                                    return False
                                if isinstance(value, str):
                                    stripped = value.strip().lower()
                                    if stripped in ['null', 'none', '', 'n/a', 'na']:
                                        return False
                                    if len(stripped) == 0:
                                        return False
                                return True
                            
                            # Count valid fields with improved logic
                            valid_fields = {
                                k: v for k, v in extracted.items() 
                                if k != 'date_error' and is_valid_extracted_field(v)
                            }
                            
                            st.write("=" * 50)
                            st.write(f"### ✅ VALID FIELDS: {len(valid_fields)}/6")
                            st.write("=" * 50)
                            st.json(valid_fields)
                            
                            # Check what went wrong if no fields
                            if len(valid_fields) == 0:
                                st.error("❌ NO VALID FIELDS EXTRACTED!")
                                st.write("**🔍 Field-by-field Analysis:**")
                                st.write(f"- Total extracted keys: {len(extracted)}")
                                
                                for key, value in extracted.items():
                                    is_valid = is_valid_extracted_field(value)
                                    st.write(f"\n**Field: {key}**")
                                    st.write(f"  - Value: '{value}'")
                                    st.write(f"  - Type: {type(value)}")
                                    st.write(f"  - Is None: {value is None}")
                                    st.write(f"  - Is Valid: {is_valid}")
                                    
                                    if not is_valid and isinstance(value, str):
                                        st.write(f"  - Stripped: '{value.strip()}'")
                                        st.write(f"  - Lower: '{value.lower()}'")
                                        st.write(f"  - Length: {len(value.strip())}")
                                
                                st.warning("⚠️ No valid fields found. Check the analysis above!")
                                
                                # Show fallback message
                                st.session_state.pdf_uploaded = True
                                fallback_msg = f"""I processed your PDF and found {len(raw_text)} characters of text.

**Raw content preview:**
{raw_text[:300]}

**However, I couldn't extract valid booking fields automatically.**

This could be because:
1. ❌ The PDF format isn't recognized by the AI
2. ❌ The fields need clear labels (Name:, Email:, Phone:, etc.)
3. ❌ The text extraction had issues

**💡 Suggested PDF Format:**
```
Name: John Doe
Email: john@example.com
Phone: 1234567890
Appointment Type: Dental
Date: 2026-02-01
Time: 10:00
```

Let me help you book manually instead. May I have your full name?"""
                                
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": fallback_msg
                                })
                                st.rerun()  # Re-enabled!
                            
                            # SUCCESS PATH - Fields were extracted
                            else:
                                st.success(f"🎉 Successfully extracted {len(valid_fields)} field(s)!")
                                
                                # Handle date errors
                                if 'date_error' in extracted:
                                    error_msg = f"❌ **Date Validation Error**\n\n{extracted['date_error']}\n\n"
                                    error_msg += "Please provide a valid date to continue."
                                    
                                    st.session_state.pdf_uploaded = True
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": error_msg
                                    })
                                    st.rerun()
                                    return page
                                
                                # Update booking data
                                st.session_state.chat_logic.booking_flow.update_booking_data(extracted)
                                st.session_state.pdf_uploaded = True
                                
                                # Create message
                                field_names = {
                                    'name': '👤 Name',
                                    'email': '📧 Email',
                                    'phone': '📱 Phone',
                                    'booking_type': '🏥 Type',
                                    'date': '📅 Date',
                                    'time': '🕐 Time'
                                }
                                
                                extracted_list = [f"{field_names.get(k, k)}: **{v}**" 
                                                for k, v in valid_fields.items()]
                                
                                extraction_msg = "✅ **PDF processed successfully!**\n\n"
                                extraction_msg += "**Extracted Details:**\n" + "\n".join(extracted_list)
                                
                                # Check for missing
                                missing = st.session_state.chat_logic.booking_flow.get_missing_fields()
                                
                                if missing:
                                    missing_names = {
                                        'name': 'Full Name',
                                        'email': 'Email',
                                        'phone': 'Phone',
                                        'booking_type': 'Appointment Type',
                                        'date': 'Date',
                                        'time': 'Time'
                                    }
                                    extraction_msg += f"\n\n⚠️ **Still Missing:** {', '.join([missing_names.get(f, f) for f in missing])}"
                                    extraction_msg += f"\n\n{st.session_state.chat_logic.booking_flow.generate_next_prompt()}"
                                else:
                                    st.session_state.awaiting_confirmation = True
                                    extraction_msg += "\n\n" + st.session_state.chat_logic.booking_flow.get_confirmation_message()
                                
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": extraction_msg
                                })
                                st.rerun()  # Re-enabled!
                        
                        else:
                            st.info("📚 PDF processed for general reference (not booking data)")
                    else:
                        st.error("❌ Failed to process PDFs")
        
        st.markdown("---")
        
        # Info sections
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            **Chat Mode:**
            - Ask questions about our services
            - Book appointments by providing details
            - Get information about procedures
            
            **PDF Booking:**
            - Upload a PDF with your booking details
            - System will auto-extract information
            - Fill in any missing details manually
            
            **Recommended PDF Format:**
            ```
            Name: Your Full Name
            Email: your@email.com
            Phone: 1234567890
            Appointment Type: Dental
            Date: 2026-02-01
            Time: 10:00
            ```
            
            **Admin Dashboard:**
            - View all bookings
            - Search and filter appointments
            - Export data
            """)
        
        with st.expander("🏥 Available Services"):
            for service in Config.BOOKING_TYPES:
                st.write(f"• {service}")
        
        with st.expander("🕐 Working Hours"):
            st.write(f"⏰ {Config.WORKING_HOURS['start']} - {Config.WORKING_HOURS['end']}")
            st.write("📅 Monday to Saturday")
        
        st.markdown("---")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_logic.booking_flow.reset_booking()
            st.session_state.booking_mode = None
            st.session_state.pdf_uploaded = False
            st.rerun()
        
        return page

def render_chat():
    """Render chat interface"""
    st.markdown("<h1 class='main-title'>💬 Chat with our AI Assistant</h1>", unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_logic.handle_message(
                    prompt,
                    st.session_state.messages
                )
            st.markdown(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Maintain message limit
        if len(st.session_state.messages) > Config.MAX_MEMORY_MESSAGES * 2:
            st.session_state.messages = st.session_state.messages[-Config.MAX_MEMORY_MESSAGES * 2:]
        
        st.rerun()
    
    # Welcome message
    if not st.session_state.messages:
        st.info("""
        👋 **Welcome!** I'm your AI booking assistant.
        
        I can help you:
        - Answer questions about our services
        - Book medical appointments
        - Provide information about our facilities
        
        Just start chatting or upload a PDF with your booking details!
        """)

def main():
    """Main application entry point"""
    # Validate configuration
    if not Config.validate():
        st.stop()
    
    # Initialize
    initialize_session_state()
    
    # Render sidebar and get page selection
    page = render_sidebar()
    
    # Render selected page
    if page == "💬 Chat":
        render_chat()
    else:
        admin = AdminDashboard()
        admin.render()

if __name__ == "__main__":
    main()