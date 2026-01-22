import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import streamlit as st
from app.config import Config
from db.database import Database
from app.rag_pipeline import RAGPipeline

class Tools:
    """Tool implementations for the booking assistant"""
    
    def __init__(self):
        self.db = Database()
        self.rag = RAGPipeline()
    
    def rag_query(self, query: str, chat_history: list = None) -> str:
        """
        Tool: RAG Query
        Search uploaded documents for relevant information
        """
        try:
            if not self.rag.is_ready():
                return "No documents have been uploaded yet. Please upload PDFs to search."
            
            return self.rag.query(query, chat_history)
        except Exception as e:
            return f"Error searching documents: {str(e)}"
    
    def save_booking(self, booking_data: Dict) -> tuple[bool, Optional[int], str]:
        """
        Tool: Save Booking
        Persist booking to database
        Returns: (success, booking_id, message)
        """
        try:
            booking_id = self.db.create_booking(booking_data)
            
            if booking_id:
                return True, booking_id, f"Booking saved successfully with ID: {booking_id}"
            else:
                return False, None, "Failed to save booking to database"
                
        except Exception as e:
            return False, None, f"Database error: {str(e)}"
    
    def send_email(self, to_email: str, subject: str, body: str) -> tuple[bool, str]:
        """
        Tool: Send Email
        Send confirmation email via SMTP
        Returns: (success, message)
        """
        try:
            if not Config.EMAIL_SENDER or not Config.EMAIL_PASSWORD:
                return False, "Email credentials not configured"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = Config.EMAIL_SENDER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # HTML body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #2c3e50;">Appointment Confirmation</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    {body}
                </div>
                <p style="margin-top: 20px; color: #7f8c8d;">
                    If you need to reschedule or cancel, please contact us.
                </p>
                <hr style="border: 1px solid #ecf0f1;">
                <p style="color: #95a5a6; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send via Gmail SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Email authentication failed. Please check credentials."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Email error: {str(e)}"
    
    def format_confirmation_email(self, booking_data: Dict, booking_id: int) -> tuple[str, str]:
        """
        Generate email subject and body
        Returns: (subject, body)
        """
        subject = f"Appointment Confirmation - Booking #{booking_id}"
        
        body = f"""
        <h3>Dear {booking_data['name']},</h3>
        <p>Your appointment has been confirmed!</p>
        
        <table style="width: 100%; margin-top: 15px;">
            <tr>
                <td style="padding: 8px; background-color: white;"><strong>Booking ID:</strong></td>
                <td style="padding: 8px; background-color: white;">#{booking_id}</td>
            </tr>
            <tr>
                <td style="padding: 8px; background-color: #f8f9fa;"><strong>Appointment Type:</strong></td>
                <td style="padding: 8px; background-color: #f8f9fa;">{booking_data['booking_type']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; background-color: white;"><strong>Date:</strong></td>
                <td style="padding: 8px; background-color: white;">{booking_data['date']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; background-color: #f8f9fa;"><strong>Time:</strong></td>
                <td style="padding: 8px; background-color: #f8f9fa;">{booking_data['time']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; background-color: white;"><strong>Contact Phone:</strong></td>
                <td style="padding: 8px; background-color: white;">{booking_data['phone']}</td>
            </tr>
        </table>
        
        <p style="margin-top: 20px;">
            <strong>Please arrive 10 minutes before your scheduled time.</strong>
        </p>
        """
        
        return subject, body
    
    def process_pdfs(self, pdf_files) -> bool:
        """Process uploaded PDFs for RAG"""
        return self.rag.process_pdfs(pdf_files)