import streamlit as st
from db.database import Database
import pandas as pd
from datetime import datetime


class AdminDashboard:
    """Admin dashboard for viewing and managing bookings"""
    
    def __init__(self):
        self.db = Database()
    
    def render(self):
        """Render the admin dashboard"""
        st.title("🏥 Admin Dashboard")
        st.markdown("---")
        
        # Stats overview
        self.render_stats()
        
        st.markdown("---")
        
        # Search and filters
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search by name or email", "")
        with col2:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Get bookings
        if search_term:
            bookings = self.db.search_bookings(search_term)
        else:
            bookings = self.db.get_all_bookings()
        
        # Display bookings
        if bookings:
            self.render_bookings_table(bookings)
        else:
            st.info("No bookings found.")
    
    def render_stats(self):
        """Render statistics cards"""
        bookings = self.db.get_all_bookings()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Bookings", len(bookings))
        
        with col2:
            today_bookings = [
                b for b in bookings 
                if b.get('date') == datetime.now().strftime('%Y-%m-%d')
            ]
            st.metric("📅 Today's Bookings", len(today_bookings))
        
        with col3:
            confirmed = [b for b in bookings if b.get('status') == 'confirmed']
            st.metric("✅ Confirmed", len(confirmed))
        
        with col4:
            unique_customers = len(set(b.get('customer_id') for b in bookings))
            st.metric("👥 Unique Customers", unique_customers)
    
    def render_bookings_table(self, bookings):
        """Render bookings in a table"""
        st.subheader("All Bookings")
        
        # Convert to DataFrame
        data = []
        for booking in bookings:
            customer = booking.get('customers', {})
            data.append({
                'ID': booking.get('id'),
                'Name': customer.get('name', 'N/A'),
                'Email': customer.get('email', 'N/A'),
                'Phone': customer.get('phone', 'N/A'),
                'Type': booking.get('booking_type', 'N/A'),
                'Date': booking.get('date', 'N/A'),
                'Time': booking.get('time', 'N/A'),
                'Status': booking.get('status', 'N/A').upper(),
                'Created': booking.get('created_at', 'N/A')[:10]
            })
        
        df = pd.DataFrame(data)
        
        # Display with styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn(
                    "ID",
                    width="small"
                ),
                "Status": st.column_config.TextColumn(
                    "Status",
                    width="small"
                )
            }
        )
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"bookings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )