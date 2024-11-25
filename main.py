import time

import streamlit as st
import sqlite3
import hashlib
import re
import time


# Utility Functions
def hash_password(password):
    """Hashes the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def is_valid_email(email):
    """Validates email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)


def get_database_connection():
    """Returns a database connection."""
    return sqlite3.connect("industry_registration.db")


def create_database_tables():
    """Creates the required database tables if not already present."""
    with get_database_connection() as conn:
        c = conn.cursor()
        # Create tables if they do not exist
        c.execute('''
                    CREATE TABLE IF NOT EXISTS user (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        password TEXT
                    )
                ''')
        # Industry Table
        c.execute('''
                    CREATE TABLE IF NOT EXISTS industry (
                        ind_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE,
                        industry_category TEXT,
                        state_ocmms_id TEXT,
                        industry_name TEXT,
                        address TEXT,
                        state TEXT,
                        district TEXT,
                        production_capacity TEXT,
                        num_stacks INTEGER,
                        industry_environment_head TEXT,
                        industry_instrument_head TEXT,
                        concerned_person_cems TEXT,
                        industry_representative_email TEXT,
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                ''')
        # Stacks Table
        c.execute('''
                    CREATE TABLE IF NOT EXISTS stacks (
                        stack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        process_attached TEXT,
                        apcd_details TEXT,
                        latitude REAL,
                        longitude REAL,
                        stack_condition TEXT,
                        stack_shape TEXT,
                        diameter REAL,
                        stack_height REAL,
                        parameters TEXT,
                        FOREIGN KEY (user_id) REFERENCES industry (ind_id)
                    )
                ''')
        # CEMS Instruments Table
        c.execute('''
                    CREATE TABLE IF NOT EXISTS cems_instruments (
                        cems_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stack_id INTEGER,
                        parameter TEXT,
                        make TEXT,
                        model TEXT,
                        serial_number TEXT,
                        measuring_range_low REAL,
                        measuring_range_high REAL,
                        certified TEXT,
                        certification_agency TEXT,
                        communication_protocol TEXT,
                        measurement_method TEXT,
                        technology TEXT,
                        connected_bspcb TEXT,
                        connected_cpcb TEXT,
                        FOREIGN KEY (stack_id) REFERENCES stacks (stack_id)
                    )
                ''')  # Keep the existing table creation code as is
        conn.commit()

category = ["Aluminium", "Cement", "Chlor Alkali", "Copper", "Distillery", "Dye & Dye Intermediates", "Fertilizer",
            "Iron & Steel", "Oil Refinery", "Pesticides", "Petrochemical", "Pharmaceuticals", "Power Plant",
            "Pulp And Paper", "Sugar", "Tannery", "Zinc", "CETP", "STP", "Slaughter House", "Textile",
            "Food, Dairy & Beverages", "Common Hazardous Waste Treatment Facility",
            "Common Biomedical Waste Incinerators"]

state_list = ["Bihar"]

dist = ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar",
        "Darbhanga", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur (Bhabua)", "Katihar", "Khagaria",
        "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda",
        "Nawada", "Pashchim Champaran", "Patna", "Purbi Champaran", "Purnia", "Rohtas", "Saharsa",
        "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali"]

def refresh_page():
    st.markdown("""
        <meta http-equiv="refresh" content="2">
        """, unsafe_allow_html=True)
def sidebar_forms(user_id):
    """Function to render the sidebar after login."""
    st.sidebar.title("Navigation")

    # Conditional rendering of sidebar options based on login status
    if st.session_state.get("logged_in", False):
        menu = ["Industry Dashboard", "Stack Details", "CEMS Details", "Logout"]
    else:
        menu = ["Login", "Register Industry"]

    choice = st.sidebar.selectbox("Select an option", menu)

    if choice == "Industry Dashboard":
        show_industry_dashboard(user_id)
    elif choice == "Stack Details":
        fill_stacks(user_id)
    elif choice == "CEMS Details":
        fill_cems_details(user_id)
    elif choice == "Logout":
        logout()
        # st.session_state["logged_in"] = False
        # st.session_state["user_id"] = None
        # st.experimental_rerun() # Rerun to reflect the logged-out state

def logout():
    """Function to log out the user and reset session state."""
    # Reset session state
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.session_state["current_page"] = "Login"  # Ensure it redirects to the login page
    refresh_page()
    st.session_state.clear()  # Clear other session variables as well (optional)

    # Display a success message
    st.success("You have successfully logged out.")

    # Rerun the app to update the state
    st.experimental_rerun()

def show_industry_dashboard(user_id):
    """Function to display the industry dashboard with industry details."""
    st.subheader("Industry Dashboard")

    # Retrieve the industry details from the database
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM industry WHERE user_id = ?", (f'ind_{user_id}',))
        industry_details = c.fetchone()

    if industry_details:
        # Display the details of the industry
        st.write(f"**Industry Category:** {industry_details[2]}")
        st.write(f"**State OCMMS ID:** {industry_details[3]}")
        st.write(f"**Industry Name:** {industry_details[4]}")
        st.write(f"**Address:** {industry_details[5]}")
        st.write(f"**State:** {industry_details[6]}")
        st.write(f"**District:** {industry_details[7]}")
        st.write(f"**Production Capacity:** {industry_details[8]}")
        st.write(f"**Number of Stacks:** {industry_details[9]}")
        st.write(f"**Environment Head:** {industry_details[10]}")
        st.write(f"**Instrument Head:** {industry_details[11]}")
        st.write(f"**Concerned Person for CEMS:** {industry_details[12]}")
        st.write(f"**Industry Representative Email:** {industry_details[13]}")
    else:
        st.error("Industry details not found. Please ensure the industry is registered.")



def fill_stacks(user_id):
    """Form to fill stack details."""
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT num_stacks FROM industry WHERE user_id = ?", (f'ind_{user_id}',))
        total_stacks = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM stacks WHERE user_id = ?", (f'ind_{user_id}',))
        completed_stacks = c.fetchone()[0]

        if completed_stacks >= total_stacks:
            st.success("All stack details are completed.")
            return

    # Display next stack form if not completed all
    current_stack = completed_stacks + 1
    st.subheader(f"Enter Details for Stack {current_stack} of {total_stacks}")

    if f"stack_{current_stack}" not in st.session_state:
        with st.form(f"stack_form_{current_stack}") as form:
            process_attached = st.text_input("Process Attached")
            apcd_details = st.text_input("APCD Details")
            latitude = st.number_input("Latitude", format="%.6f")
            longitude = st.number_input("Longitude", format="%.6f")
            stack_condition = st.selectbox("Stack Condition", ["Good", "Average", "Poor"])
            stack_shape = st.selectbox("Stack Shape", ["Circular", "Rectangular", "Square"])
            diameter = st.number_input("Diameter (in meters)", format="%.2f")
            stack_height = st.number_input("Stack Height (in meters)", format="%.2f")
            parameters = st.multiselect("Parameters Monitored", ["PM", "SO2", "NOx", "CO", "O2"])

            submit_stack = st.form_submit_button("Submit Stack Details")

        if submit_stack:
            if not parameters:
                st.error("Please select at least one parameter.")
                return

            with get_database_connection() as conn:
                c = conn.cursor()
                c.execute(""" 
                    INSERT INTO stacks (user_id, process_attached, apcd_details, latitude, longitude, stack_condition,
                                        stack_shape, diameter, stack_height, parameters)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    f'ind_{user_id}', process_attached, apcd_details, latitude, longitude, stack_condition,
                    stack_shape, diameter, stack_height, ",".join(parameters)
                ))
                stack_id = c.lastrowid
                conn.commit()

            # Save stack state in session
            st.session_state[f"stack_{current_stack}"] = True
            st.session_state["parameters"] = parameters  # Store parameters for CEMS form
            st.success("Stack details saved!")
            st.session_state["current_page"] = f"cems_{current_stack}"  # Move to CEMS details form
            time.sleep(1)
            st.rerun()


def fill_cems_details(user_id):
    """Form to fill CEMS details."""
    st.subheader("Enter CEMS Details")

    # Retrieve stack details from the session or database
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT stack_id, process_attached, parameters FROM stacks WHERE user_id = ?", (f'ind_{user_id}',))
        stack_details = c.fetchall()

    if not stack_details:
        st.error("No stack details found. Please fill in stack details first.")
        return

    # Filter stacks that have details filled (stack_id with non-null details)
    filled_stacks = [stack for stack in stack_details if stack[1]]  # Stack details should not be empty
    if not filled_stacks:
        st.error("No filled stack details found. Please fill in stack details first.")
        return

    # Dropdown to select stack based on 'process_attached'
    stack_options = [stack[1] for stack in filled_stacks]  # Using process_attached instead of stack_name
    selected_process = st.selectbox("Select Process", stack_options)

    # Get the stack ID and parameters based on selected process
    selected_stack = next(stack for stack in filled_stacks if stack[1] == selected_process)
    selected_stack_id = selected_stack[0]
    stack_parameters = selected_stack[2]

    if stack_parameters:
        available_parameters = stack_parameters.split(",")  # Assuming comma-separated parameters
    else:
        available_parameters = []

    # Retrieve CEMS parameters already filled for the selected stack
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT parameter FROM cems_instruments WHERE stack_id = ?
        """, (selected_stack_id,))
        filled_parameters = c.fetchall()

    filled_parameter_names = [param[0] for param in filled_parameters]  # List of filled parameter names
    available_parameters = [param.strip() for param in available_parameters if param.strip() not in filled_parameter_names]

    if not available_parameters:
        st.warning(f"All parameters for the stack with process '{selected_process}' have already been filled.")
        return

    # Dropdown to select parameter (filter out already filled ones)
    selected_parameter = st.selectbox("Select Parameter", options=available_parameters)

    # Form for entering CEMS details
    with st.form(f"cems_form_{selected_stack_id}") as form:
        make = st.text_input("Make")
        model = st.text_input("Model")
        serial_number = st.text_input("Serial Number")
        measuring_range_low = st.number_input("Measuring Range (Low)", format="%.2f")
        measuring_range_high = st.number_input("Measuring Range (High)", format="%.2f")
        certified = st.selectbox("Is Certified?", ["Yes", "No"])
        certification_agency = st.text_input("Certification Agency")
        communication_protocol = st.text_input("Communication Protocol")
        measurement_method = st.text_input("Measurement Method")
        technology = st.text_input("Technology")
        connected_bspcb = st.text_input("Connected to BSPCB?")
        connected_cpcb = st.text_input("Connected to CPCB?")

        submit_cems = st.form_submit_button("Submit CEMS Details")

    if submit_cems:
        # Debugging: Check the collected data
        st.write("CEMS Form Submitted:", {
            "user_id": user_id,
            "process_attached": selected_process,
            "parameter": selected_parameter,
            "make": make,
            "model": model,
            "serial_number": serial_number,
            "measuring_range_low": measuring_range_low,
            "measuring_range_high": measuring_range_high,
            "certified": certified,
            "certification_agency": certification_agency,
            "communication_protocol": communication_protocol,
            "measurement_method": measurement_method,
            "technology": technology,
            "connected_bspcb": connected_bspcb,
            "connected_cpcb": connected_cpcb,
        })

        # Save CEMS details to database
        try:
            with get_database_connection() as conn:
                c = conn.cursor()

                # Here, use the stack_id to associate the CEMS data with the correct stack
                c.execute(""" 
                    INSERT INTO cems_instruments (stack_id, parameter, make, model, serial_number, measuring_range_low,
                        measuring_range_high, certified, certification_agency, communication_protocol, measurement_method,
                        technology, connected_bspcb, connected_cpcb)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    selected_stack_id, selected_parameter, make, model, serial_number, measuring_range_low, measuring_range_high,
                    certified, certification_agency, communication_protocol, measurement_method, technology,
                    connected_bspcb, connected_cpcb
                ))
                conn.commit()

            st.success(f"CEMS details for {selected_parameter} saved!")
            st.session_state[f"cems_{selected_stack_id}_{selected_parameter}"] = True  # Mark CEMS form as completed for this parameter
            time.sleep(2)
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred while saving CEMS details: {e}")


# Main Function
def main():
    """Main application logic."""
    st.title("🌳 Industry Registration Portal")
    create_database_tables()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = None

    if not st.session_state["logged_in"]:
        st.header("Please log in or register to continue.")
        menu = ["Register Industry", "Login"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Register Industry":
            st.subheader("Register Industry")
            # Registration form
            with st.form("register_form"):
                industry_category = st.selectbox("Industry Category", options=category, placeholder="Select Category",
                                                 index=None)
                state_ocmms_id = st.text_input("State OCMMS Id")
                industry_name = st.text_input("Industry Name")
                address = st.text_input("Address")
                state = st.selectbox("State", options=state_list, placeholder="Select State", index=None)
                district = st.selectbox("District", options=dist, placeholder="Select District", index=None)
                production_capacity = st.text_input("Production Capacity")
                num_stacks = st.number_input("Number of Stacks", min_value=1)
                industry_environment_head = st.text_input("Industry Environment Head")
                industry_instrument_head = st.text_input("Industry Instrument Head")
                concerned_person_cems = st.text_input("Concerned Person for CEMS")

                # Industry Representative Email Id and Password at the end
                email = st.text_input("Industry Representative Email Id (used for login)")
                password = st.text_input("Password", type="password")

                submit = st.form_submit_button("Register Industry")

            # Validate mandatory fields
            if submit:
                if not (
                        industry_category and state_ocmms_id and industry_name and address and state and district and production_capacity
                        and num_stacks and industry_environment_head and industry_instrument_head and concerned_person_cems
                        and email and password):
                    st.error("All fields are mandatory. Please fill in all fields.")
                    return

                # Validate email format
                if not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                    return

                # Save data to the database
                try:
                    conn = get_database_connection()
                    c = conn.cursor()

                    # Insert user (with email used for login)
                    hashed_password = hash_password(password)
                    c.execute("INSERT INTO user (email, password) VALUES (?, ?)", (email, hashed_password))
                    user_id = c.lastrowid
                    user_id_str = f"ind_{user_id}"  # Format user_id like 'ind_1', 'ind_2', etc.

                    # Insert industry
                    c.execute('''INSERT INTO industry (user_id, industry_category, state_ocmms_id, industry_name, address,
                                                                        state, district, production_capacity, num_stacks, industry_environment_head,
                                                                        industry_instrument_head, concerned_person_cems, industry_representative_email)
                                                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (user_id_str, industry_category, state_ocmms_id, industry_name, address, state,
                               district, production_capacity, num_stacks, industry_environment_head,
                               industry_instrument_head,
                               concerned_person_cems, email))
                    conn.commit()
                    conn.close()

                    st.success("Industry registered successfully!")
                except sqlite3.IntegrityError:
                    st.error("This email is already registered. Please use a different email.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")  # Encapsulate registration logic

        elif choice == "Login":
            st.subheader("Login")

            # Login form
            email = st.text_input("Industry Representative Email Id")
            password = st.text_input("Password", type="password")
            login_button = st.button("Login")

            if login_button:
                try:
                    conn = get_database_connection()
                    c = conn.cursor()

                    # Verify email and password
                    c.execute("SELECT id, password FROM user WHERE email = ?", (email,))
                    user = c.fetchone()

                    if user and hash_password(password) == user[1]:
                        st.success("Login successful!")
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = user[0]
                        st.session_state["current_page"] = "Industry Details"
                        st.rerun()
                        st.write(f"User ID in session state: {st.session_state['user_id']}")  # Debugging

                    else:
                        st.error("Invalid email or password.")
                    conn.close()
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    else:
        user_id = st.session_state["user_id"]
        sidebar_forms(user_id)


if __name__ == "__main__":
    main()
