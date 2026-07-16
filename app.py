import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import random

# Page Configuration
st.set_page_config(page_title="eJatra Ride-Sharing Portal", layout="wide")
st.title("🛺 eJatra DBMS Portal")
st.markdown("Welcome to the eJatra Ride-Sharing Mini-Project Interface.")

# --- SECURE SUPABASE CONNECTION ---
@st.cache_resource
def get_connection():
    """Establishes connection to Supabase using Streamlit secrets."""
    try:
        conn = psycopg2.connect(
            host=st.secrets["db_host"],
            port=st.secrets["db_port"],
            database=st.secrets["db_name"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"]
        )
        return conn
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {e}")
        st.info("Check your settings in `.streamlit/secrets.toml` and ensure you are using the correct connection pooler port.")
        return None

conn = get_connection()

if conn is None:
    st.stop()

# Helper function to run query and return DataFrame
def run_query(query, params=None):
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                return pd.DataFrame(data, columns=columns)
            conn.commit()
            return None
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        conn.rollback()
        return None

# --- APP NAVIGATION ---
role = st.sidebar.selectbox(
    "Choose Your Role / View", 
    [
        "Rider (Passenger)", 
        "Driver", 
        "⚠️ File a Complaint",  # <-- New Navigation Option
        "Admin Portal", 
        "📊 Database Tables Explorer"
    ]
)

# -------------------------------------------------------------
# ROLE 1: RIDER (PASSENGER)
# -------------------------------------------------------------
if role == "Rider (Passenger)":
    st.header("🚶 Rider Console")
    
    # Fetch existing riders for dropdown selection
    users_df = run_query("SELECT id, name FROM users;")
    
    if users_df is not None and not users_df.empty:
        user_options = {row['name']: row['id'] for _, row in users_df.iterrows()}
        selected_user_name = st.selectbox("Select User Profile", list(user_options.keys()))
        user_id = user_options[selected_user_name]
        
        st.subheader("📍 Book a Ride")
        col1, col2 = st.columns(2)
        with col1:
            pickup = st.text_input("Pickup Address", value="Kathmandu University, Dhulikhel")
            vehicle_choice = st.selectbox("Preferred Vehicle Type", ["bike", "car", "bus"])
        with col2:
            dropoff = st.text_input("Drop-off Address", value="Banepa Chowk")
            estimated_price = st.number_input("Estimated Price (Rs.)", min_value=50, max_value=5000, value=150)
            
        if st.button("Request Ride"):
            # Step 1: Find an available vehicle and driver of preferred type
            find_driver_query = """
                SELECT v.id as vehicle_id, d.id as driver_id, d.name as driver_name 
                FROM vehicles v
                JOIN driver d ON v.driver_id = d.id
                WHERE v.vec_type = %s AND d.driver_status = 'ready' AND v.vechile_status = 'active'
                LIMIT 1;
            """
            available_driver = run_query(find_driver_query, (vehicle_choice,))
            
            if available_driver is not None and not available_driver.empty:
                driver_id = int(available_driver.iloc[0]['driver_id'])
                vehicle_id = int(available_driver.iloc[0]['vehicle_id'])
                driver_name = available_driver.iloc[0]['driver_name']
                
                # Step 2: Book the trip (Insert)
                book_query = """
                    INSERT INTO trip (user_id, driver_id, pickup_address, drop_off, price, vehicle_used, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'ongoing') RETURNING trip_id;
                """
                new_trip = run_query(book_query, (user_id, driver_id, pickup, dropoff, estimated_price, vehicle_id))
                
                # Step 3: Update driver status to 'driving'
                run_query("UPDATE driver SET driver_status = 'driving' WHERE id = %s;", (driver_id,))
                
                if new_trip is not None:
                    new_id = new_trip.iloc[0]['trip_id']
                    st.success(f"🎉 Ride Booked Successfully! Trip ID: {new_id}")
                    st.info(f"Driver **{driver_name}** is on the way in a **{vehicle_choice}**!")
            else:
                st.error(f"No available {vehicle_choice} drivers right now. Please try again later!")
    else:
        st.warning("No users found in the database. Please add users first.")

# -------------------------------------------------------------
# ROLE 2: DRIVER
# -------------------------------------------------------------
elif role == "Driver":
    st.header("🚗 Driver Console")
    
    # Fetch drivers
    drivers_df = run_query("SELECT id, name FROM driver;")
    
    if drivers_df is not None and not drivers_df.empty:
        driver_options = {row['name']: row['id'] for _, row in drivers_df.iterrows()}
        selected_driver_name = st.selectbox("Select Driver Profile", list(driver_options.keys()))
        driver_id = driver_options[selected_driver_name]
        
        # Section 1: Update Active Status
        st.subheader("🔄 Change Availability Status")
        current_status_df = run_query("SELECT driver_status FROM driver WHERE id = %s;", (driver_id,))
        if current_status_df is not None and not current_status_df.empty:
            current_status = current_status_df.iloc[0]['driver_status']
            st.write(f"Your current status: **{current_status}**")
            
            new_status = st.selectbox("Set Status", ["ready", "busy", "offline"])
            if st.button("Update Status"):
                run_query("UPDATE driver SET driver_status = %s WHERE id = %s;", (new_status, driver_id))
                st.success("Status updated!")
                st.rerun()
                
        # Section 2: View and Complete Trips
        st.subheader("🗺️ Your Ongoing Trips")
        ongoing_trips = run_query(
            "SELECT trip_id, user_id, pickup_address, drop_off, price FROM trip WHERE driver_id = %s AND status = 'ongoing';",
            (driver_id,)
        )
        
        if ongoing_trips is not None and not ongoing_trips.empty:
            for _, row in ongoing_trips.iterrows():
                st.write(f"**Trip #{row['trip_id']}** to **{row['drop_off']}**")
                st.write(f"Price: Rs. {row['price']} | Pickup: {row['pickup_address']}")
                
                # Payment method choice and complete transaction
                pay_method = st.radio(f"Payment Gateway for Trip #{row['trip_id']}", ["esewa", "khalti"], key=f"pay_{row['trip_id']}")
                
                if st.button(f"Complete Trip & Collect Payment", key=f"btn_{row['trip_id']}"):
                    # Mark trip as completed
                    run_query("UPDATE trip SET status = 'completed' WHERE trip_id = %s;", (row['trip_id'],))
                    
                    # Generate transaction code and log the payment
                    txn_code = f"TXN-{random.randint(100000000, 999999999)}"
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    payment_query = """
                        INSERT INTO payment (trip_instance, transcation_code, paidd_from, paid_at)
                        VALUES (%s, %s, %s, %s);
                    """
                    run_query(payment_query, (row['trip_id'], txn_code, pay_method, now_str))
                    
                    # Set driver status back to 'ready'
                    run_query("UPDATE driver SET driver_status = 'ready' WHERE id = %s;", (driver_id,))
                    
                    st.success(f"Trip #{row['trip_id']} Completed! Payment of Rs. {row['price']} logged via {pay_method.capitalize()}.")
                    st.rerun()
        else:
            st.info("No ongoing trips assigned to you at the moment.")
    else:
        st.warning("No drivers registered in the system.")

# -------------------------------------------------------------
# ROLE 3: FILE A COMPLAINT (New Code Component 🌟)
# -------------------------------------------------------------
elif role == "⚠️ File a Complaint":
    st.header("⚠️ Customer and Rider Dispute Portal")
    st.markdown("Encountered an issue during your journey? Register your grievance here.")
    
    # Step 1: Identify complainant role
    complainant_role = st.selectbox("I want to register a complaint as a:", ["passenger", "rider"])
    
    selected_entity_id = None
    trips_query = ""
    query_params = ()

    # Step 2: Select Profile & query relevant trips dynamically
    if complainant_role == "passenger":
        users_df = run_query("SELECT id, name FROM users;")
        if users_df is not None and not users_df.empty:
            user_options = {row['name']: row['id'] for _, row in users_df.iterrows()}
            selected_user_name = st.selectbox("Select Your User Profile", list(user_options.keys()))
            selected_entity_id = user_options[selected_user_name]
            
            # Fetch trips belonging to this user
            trips_query = """
                SELECT trip_id, drop_off, price 
                FROM trip 
                WHERE user_id = %s 
                ORDER BY trip_id DESC;
            """
            query_params = (selected_entity_id,)
    else:
        # 'rider' corresponds to our driver table in this system
        drivers_df = run_query("SELECT id, name FROM driver;")
        if drivers_df is not None and not drivers_df.empty:
            driver_options = {row['name']: row['id'] for _, row in drivers_df.iterrows()}
            selected_driver_name = st.selectbox("Select Your Driver Profile", list(driver_options.keys()))
            selected_entity_id = driver_options[selected_driver_name]
            
            # Fetch trips completed/serviced by this driver
            trips_query = """
                SELECT trip_id, drop_off, price 
                FROM trip 
                WHERE driver_id = %s 
                ORDER BY trip_id DESC;
            """
            query_params = (selected_entity_id,)

    # Step 3: Select Trip and Submit Complaint details
    if selected_entity_id is not None:
        user_trips = run_query(trips_query, query_params)
        
        if user_trips is not None and not user_trips.empty:
            trip_options = {f"Trip #{row['trip_id']} to {row['drop_off']} (Rs. {row['price']})": row['trip_id'] for _, row in user_trips.iterrows()}
            selected_trip_label = st.selectbox("Select Trip associated with complaint", list(trip_options.keys()))
            trip_id = trip_options[selected_trip_label]
            
            complaint_text = st.text_area("Provide detail description of your complaint", placeholder="Type your issue here...")
            
            if st.button("Submit Complaint"):
                if complaint_text.strip() == "":
                    st.error("Please provide description details before submitting.")
                else:
                    # Execute database insert
                    insert_query = """
                        INSERT INTO complaints (complaint_by, trip_id, complaint)
                        VALUES (%s, %s, %s);
                    """
                    run_query(insert_query, (complainant_role, trip_id, complaint_text))
                    st.success("🎉 Your complaint has been recorded successfully. An administrator will look into it shortly!")
        else:
            st.warning("You do not have any registered trips in the system to complain about yet.")

# -------------------------------------------------------------
# ROLE 4: ADMIN PORTAL
# -------------------------------------------------------------
elif role == "Admin Portal":
    st.header("🛡️ Administrative Command Center")
    
    # Simple Metrics Row
    st.subheader("📊 Business Metrics")
    col1, col2, col3 = st.columns(3)
    
    total_revenue_df = run_query("SELECT SUM(price) as rev FROM trip WHERE status = 'completed';")
    total_trips_df = run_query("SELECT COUNT(*) as cnt FROM trip;")
    open_complaints_df = run_query("SELECT COUNT(*) as cnt FROM complaints WHERE response IS NULL OR response = '';")
    
    with col1:
        rev = total_revenue_df.iloc[0]['rev'] if total_revenue_df is not None and pd.notna(total_revenue_df.iloc[0]['rev']) else 0
        st.metric("Total Revenue", f"Rs. {rev}")
    with col2:
        cnt = total_trips_df.iloc[0]['cnt'] if total_trips_df is not None else 0
        st.metric("Total Trips Registered", cnt)
    with col3:
        comp_count = open_complaints_df.iloc[0]['cnt'] if open_complaints_df is not None else 0
        st.metric("Pending Complaints", comp_count)
        
    st.markdown("---")
    
    # Complaint Resolution Engine
    st.subheader("📬 Resolve Pending Customer Complaints")
    pending_complaints = run_query("""
        SELECT id, complaint_by, trip_id, complaint 
        FROM complaints 
        WHERE response IS NULL OR response = '';
    """)
    
    if pending_complaints is not None and not pending_complaints.empty:
        selected_complaint_id = st.selectbox("Select Complaint ID to Address", pending_complaints['id'].tolist())
        comp_detail = pending_complaints[pending_complaints['id'] == selected_complaint_id].iloc[0]
        
        st.warning(f"**By:** {comp_detail['complaint_by'].capitalize()} | **Trip ID:** {comp_detail['trip_id']}")
        st.info(f"**Description:** {comp_detail['complaint']}")
        
        # Select an Admin handling this
        admins_df = run_query("SELECT id, name FROM admin;")
        if admins_df is not None and not admins_df.empty:
            admin_options = {row['name']: row['id'] for _, row in admins_df.iterrows()}
            selected_admin = st.selectbox("Assign Resolving Admin", list(admin_options.keys()))
            admin_id = admin_options[selected_admin]
            
            resolution_text = st.text_area("Write official resolution response")
            
            if st.button("Submit Official Response"):
                run_query(
                    "UPDATE complaints SET response = %s, admin_assigned = %s WHERE id = %s;",
                    (resolution_text, admin_id, selected_complaint_id)
                )
                st.success(f"Complaint #{selected_complaint_id} resolved and saved.")
                st.rerun()
        else:
            st.error("No Admins found in the system. Create an Admin profile first.")
    else:
        st.success("All customer disputes have been fully resolved!")

# -------------------------------------------------------------
# ROLE 5: DATABASE TABLES EXPLORER
# -------------------------------------------------------------
elif role == "📊 Database Tables Explorer":
    st.header("📊 Database Tables Explorer")
    st.markdown("Direct read access to your PostgreSQL tables hosted on Supabase.")
    
    # Defining our 7 interactive tabs
    tab_users, tab_drivers, tab_vehicles, tab_trips, tab_payments, tab_complaints, tab_admins = st.tabs([
        "👤 Users", 
        "🚗 Drivers", 
        "🚲 Vehicles", 
        "🗺️ Trips", 
        "💳 Payments", 
        "⚠️ Complaints", 
        "🛡️ Admins"
    ])
    
    # --- TAB 1: USERS ---
    with tab_users:
        st.subheader("👤 Registered Users Profile Directory")
        users_df = run_query("SELECT * FROM users;")
        if users_df is not None and not users_df.empty:
            st.metric("Total Users", len(users_df))
            st.dataframe(users_df, use_container_width=True)
        else:
            st.info("No records present in the `users` table.")
            
    # --- TAB 2: DRIVERS ---
    with tab_drivers:
        st.subheader("🚗 Driver Registry & Availability status")
        drivers_df = run_query("SELECT * FROM driver;")
        if drivers_df is not None and not drivers_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Drivers", len(drivers_df))
            with col2:
                driving_count = len(drivers_df[drivers_df['driver_status'] == 'driving']) if 'driver_status' in drivers_df.columns else 0
                st.metric("Drivers On Trips", driving_count)
            st.dataframe(drivers_df, use_container_width=True)
        else:
            st.info("No records present in the `driver` table.")
            
    # --- TAB 3: VEHICLES ---
    with tab_vehicles:
        st.subheader("🚲 Active Vehicle Fleet")
        vehicles_df = run_query("SELECT * FROM vehicles;")
        if vehicles_df is not None and not vehicles_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Vehicles Registered", len(vehicles_df))
            with col2:
                type_counts = vehicles_df['vec_type'].value_counts() if 'vec_type' in vehicles_df.columns else {}
                most_common = type_counts.index[0] if not type_counts.empty else "N/A"
                st.metric("Primary Fleet Type", most_common.capitalize())
            st.dataframe(vehicles_df, use_container_width=True)
        else:
            st.info("No records present in the `vehicles` table.")
            
    # --- TAB 4: TRIPS ---
    with tab_trips:
        st.subheader("🗺️ Trip Transaction History")
        trip_df = run_query("SELECT * FROM trip;")
        if trip_df is not None and not trip_df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Bookings", len(trip_df))
            with col2:
                completed_trips = len(trip_df[trip_df['status'] == 'completed']) if 'status' in trip_df.columns else 0
                st.metric("Completed Rides", completed_trips)
            with col3:
                avg_fare = round(trip_df['price'].mean(), 2) if 'price' in trip_df.columns else 0
                st.metric("Average Trip Fare", f"Rs. {avg_fare}")
            st.dataframe(trip_df, use_container_width=True)
        else:
            st.info("No records present in the `trip` table.")
            
    # --- TAB 5: PAYMENTS ---
    with tab_payments:
        st.subheader("💳 Digital Wallet Transactions")
        payments_df = run_query("SELECT * FROM payment;")
        if payments_df is not None and not payments_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Successfully Logged Payments", len(payments_df))
            with col2:
                wallet_counts = payments_df['paidd_from'].value_counts() if 'paidd_from' in payments_df.columns else {}
                fav_wallet = wallet_counts.index[0] if not wallet_counts.empty else "N/A"
                st.metric("Top Payment Gateway", fav_wallet.upper())
            st.dataframe(payments_df, use_container_width=True)
        else:
            st.info("No records present in the `payment` table.")
            
    # --- TAB 6: COMPLAINTS ---
    with tab_complaints:
        st.subheader("⚠️ Customer Grievance Log")
        complaints_df = run_query("SELECT * FROM complaints;")
        if complaints_df is not None and not complaints_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Complaints Filed", len(complaints_df))
            with col2:
                resolved_count = complaints_df['response'].notna().sum() if 'response' in complaints_df.columns else 0
                st.metric("Resolved Cases", resolved_count)
            st.dataframe(complaints_df, use_container_width=True)
        else:
            st.info("No records present in the `complaints` table.")
            
    # --- TAB 7: ADMINS ---
    with tab_admins:
        st.subheader("🛡️ Administrative Profiles")
        admin_df = run_query("SELECT * FROM admin;")
        if admin_df is not None and not admin_df.empty:
            st.metric("Total System Admins", len(admin_df))
            st.dataframe(admin_df, use_container_width=True)
        else:
            st.info("No records present in the `admin` table.")