from supabase import create_client, Client
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st
from app.config import Config

class Database:
    """Database operations using Supabase"""
    
    def __init__(self):
        try:
            self.client: Client = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY
            )
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            self.client = None
    
    def create_customer(self, name: str, email: str, phone: str) -> Optional[int]:
        """Create or get existing customer"""
        try:
            # Check if customer exists
            result = self.client.table("customers")\
                .select("customer_id")\
                .eq("email", email)\
                .execute()
            
            if result.data:
                return result.data[0]["customer_id"]
            
            # Create new customer
            result = self.client.table("customers").insert({
                "name": name,
                "email": email,
                "phone": phone
            }).execute()
            
            return result.data[0]["customer_id"]
        except Exception as e:
            st.error(f"Error creating customer: {str(e)}")
            return None
    
    def create_booking(self, booking_data: Dict) -> Optional[int]:
        """Create a new booking"""
        try:
            # First, create/get customer
            customer_id = self.create_customer(
                booking_data["name"],
                booking_data["email"],
                booking_data["phone"]
            )
            
            if not customer_id:
                return None
            
            # Create booking
            result = self.client.table("bookings").insert({
                "customer_id": customer_id,
                "booking_type": booking_data["booking_type"],
                "date": booking_data["date"],
                "time": booking_data["time"],
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return result.data[0]["id"]
        except Exception as e:
            st.error(f"Error creating booking: {str(e)}")
            return None
    
    def get_all_bookings(self) -> List[Dict]:
        """Fetch all bookings with customer details"""
        try:
            result = self.client.table("bookings")\
                .select("*, customers(*)")\
                .order("created_at", desc=True)\
                .execute()
            return result.data
        except Exception as e:
            st.error(f"Error fetching bookings: {str(e)}")
            return []
    
    def search_bookings(self, search_term: str) -> List[Dict]:
        """Search bookings by name or email"""
        try:
            result = self.client.table("bookings")\
                .select("*, customers(*)")\
                .or_(f"customers.name.ilike.%{search_term}%,customers.email.ilike.%{search_term}%")\
                .execute()
            return result.data
        except Exception as e:
            st.error(f"Error searching bookings: {str(e)}")
            return []
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict]:
        """Get specific booking details"""
        try:
            result = self.client.table("bookings")\
                .select("*, customers(*)")\
                .eq("id", booking_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error fetching booking: {str(e)}")
            return None