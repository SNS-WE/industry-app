import streamlit as st
import sqlite3
import sqlitecloud
import hashlib
import re
import time
import pandas as pd


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
    conn = sqlitecloud.connect(
        "sqlitecloud://cqssetgvhz.sqlite.cloud:8860/industry_registration?apikey=v1hNkVAkbMH6JLN7FSU71ARA3aaEodfbuxJ9Cl9HbVQ"
    )
    conn.execute("PRAGMA foreign_keys = ON;")
      # Explicitly enable foreign keys
    return conn

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
        # Admin table for admin login
        c.execute('''
                    CREATE TABLE IF NOT EXISTS admin (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )
                ''')
        # Industry Table
        c.execute('''
                    CREATE TABLE IF NOT EXISTS industry (
                        ind_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        user_id_ind TEXT UNIQUE,
                        industry_category TEXT,
                        state_ocmms_id TEXT UNIQUE,
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
                        completed_stacks INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                ''')
        # Stacks Table
        c.execute('''
                    CREATE TABLE IF NOT EXISTS stacks (
                        stack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        user_id_ind TEXT,
                        process_attached TEXT,
                        apcd_details TEXT,
                        latitude REAL,
                        longitude REAL,
                        stack_condition TEXT,
                        stack_shape TEXT,
                        diameter REAL,
                        length REAL,
                        width REAL,
                        stack_material TEXT,
                        stack_height REAL,
                        platform_height REAL,
                        platform_approachable TEXT,
                        approaching_media TEXT,
                        cems_installed TEXT,
                        stack_params TEXT,
                        duct_params TEXT,
                        follows_formula TEXT,
                        manual_port_installed TEXT,
                        cems_below_manual TEXT,
                        parameters TEXT,
                        number_params INTEGER DEFAULT 0,
                        completed_parameters INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES industry (ind_id)
                    )
                ''')
        # CEMS Instruments Table
        c.execute('''
                    CREATE TABLE IF NOT EXISTS cems_instruments (
                        cems_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stack_id INTEGER,
                        user_id_ind TEXT,
                        parameter TEXT,
                        make TEXT,
                        model TEXT,
                        serial_number TEXT,
                        emission_limit REAL,
                        measuring_range_low REAL,
                        measuring_range_high REAL,
                        certified TEXT,
                        certification_agency TEXT,
                        communication_protocol TEXT,
                        measurement_method TEXT,
                        technology TEXT,
                        connected_bspcb TEXT,
                        bspcb_url TEXT,
                        cpcb_url TEXT,
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

st.set_page_config(layout="wide")

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

# Admin login page
def admin_login_page():
    st.subheader("Admin Login")
    username = st.text_input("Username", key="admin_username")
    password = st.text_input("Password", type="password", key="admin_password")
    login_button = st.button("Login as Admin")

    if login_button:
        with get_database_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM admin WHERE username = ?", (username,))
            admin = c.fetchone()
            if admin and hash_password(password) == admin[0]:
                st.success("Admin login successful!")
                st.session_state["admin_logged_in"] = True
                st.rerun()  # Redirect to refresh the session
            else:
                st.error("Invalid admin credentials.")
    
def admin_dashboard():
    st.subheader("Admin Dashboard")

    # Add a "Home" button to return to the industry list
    if st.sidebar.button("Return to Dasboard"):
        st.session_state["selected_ind_id"] = None  # Clear the selected industry
        st.rerun()  # Refresh the page to go back to the main list
        
    # Logout button
    if st.sidebar.button("Logout", key="admin_logout"):
        st.session_state["admin_logged_in"] = False
        st.rerun()  # Redirect back to login

    # Check if an industry has been selected
    if "selected_ind_id" in st.session_state and st.session_state["selected_ind_id"]:
        # Show industry details if an industry is selected
        show_industry_details(st.session_state["selected_ind_id"])
    else:
        # Display the list of all industries
        display_all_details()


def display_all_details():
    """Display all user-filled industry details with buttons in each row using `st.columns`."""
    st.subheader("All User-Filled Industry Details")  # Display the heading once at the top
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM industry")
        industries = c.fetchall()

        if industries:
            # Create a DataFrame for better visualization
            df = pd.DataFrame(industries, columns=[col[0] for col in c.description])
            ind_df = df[['state_ocmms_id', 'industry_name', 'industry_category', 'address', 'district',
                         'production_capacity', 'num_stacks', 'industry_environment_head',
                         'concerned_person_cems', 'industry_representative_email', 'ind_id']]

            # Search functionality
            search_term = st.text_input("Search Industry", "")
            if search_term:
                ind_df = ind_df[ind_df['industry_name'].str.contains(search_term, case=False, na=False)]

            # Display the headers just once
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])  # Adjust column widths as needed
            with col1:
                st.markdown("**Industry Name**")
            with col2:
                st.markdown("**Category**")
            with col3:
                st.markdown("**District**")
            with col4:
                st.markdown("**Production Capacity**")
            with col5:
                st.markdown("**Actions**")  # For the View button

            # Iterate over rows and create a layout with columns for each row
            for _, row in ind_df.iterrows():
                # Define columns for the row
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])  # Adjust column widths as needed

                # Display data fields in the columns
                with col1:
                    st.markdown(f"{row['industry_name']}")
                with col2:
                    st.markdown(f"{row['industry_category']}")
                with col3:
                    st.markdown(f"{row['district']}")
                with col4:
                    st.markdown(f"{row['production_capacity']}")
                with col5:
                    # Add a "View" button in the last column, using ind_id as the key
                    if st.button("View", key=f"view_{row['ind_id']}"):
                        # Store both the ind_id and state_ocmms_id in session state
                        st.session_state["selected_ind_id"] = row["ind_id"]
                        st.session_state["selected_state_ocmms_id"] = row["state_ocmms_id"]
                        st.rerun()  # Refresh the page to load the details

        else:
            st.warning("No industry details found.")


# # Display all user-filled details for the admin
# def display_all_details():
#     st.subheader("All User-Filled Industry Details")
#     with get_database_connection() as conn:
#         c = conn.cursor()
#         c.execute("SELECT * FROM industry")
#         industries = c.fetchall()

#         if industries:
#             # Create a DataFrame for better visualization
#             df = pd.DataFrame(industries, columns=[col[0] for col in c.description])
#             ind_df = df[['state_ocmms_id', 'industry_name', 'industry_category', 'address', 'district',
#                          'production_capacity', 'num_stacks', 'industry_environment_head',
#                          'concerned_person_cems', 'industry_representative_email']]

#             # Search functionality
#             search_term = st.text_input("Search Industry", "")
#             if search_term:
#                 ind_df = ind_df[ind_df['industry_name'].str.contains(search_term, case=False, na=False)]

#             st.dataframe(ind_df, column_config={
#                 'state_ocmms_id': 'State OCMMS Code',
#                 'industry_category': 'Category',
#                 'industry_name': 'Industry Name',
#                 'address': 'Address',
#                 'district': 'District',
#                 'production_capacity': 'Production Capacity',
#                 'num_stacks': 'Number of Stacks',
#                 'industry_environment_head': 'Industry Environment Head',
#                 'concerned_person_cems': 'Concerned Person for CEMS',
#                 'industry_representative_email': 'Industry Representative Email ID'
#             }, hide_index=True)  # Customize column display

#             # Add a "View" button for each industry
#             for index, row in df.iterrows():
#                 if st.button(f"View {row['industry_name']}", key=f"view_{row['ind_id']}"):
#                     # Store the selected industry ID in session state
#                     st.session_state["selected_ind_id"] = row["ind_id"]
#                     st.rerun()  # Refresh the page to load the details
#         else:
#             st.warning("No industry details found.")

def show_industry_details(ind_id):
    """Show detailed information for the selected industry."""
    st.subheader(f"Details for Industry ID: {ind_id}")
    with get_database_connection() as conn:
        c = conn.cursor()

        # Fetch industry details
        c.execute("SELECT * FROM industry WHERE ind_id = ?", (ind_id,))
        industry_details = c.fetchone()

        if industry_details:
            # Convert details to a dictionary for display
            industry_dict = {desc[0]: value for desc, value in zip(c.description, industry_details)}

            # Display the details in a readable format
            for key, value in industry_dict.items():
                st.markdown(f"**{key.replace('_', ' ').capitalize()}:** {value}")
            
        else:
            st.warning("No details found for the selected industry.")

# def admin_dashboard():
#     st.subheader("Admin Dashboard")

#     # Logout button
#     if st.sidebar.button("Logout", key="admin_logout"):
#         st.session_state["admin_logged_in"] = False
#         st.rerun()  # Redirect back to login

#     # Display all user-filled industry details
#     display_all_details()

# # Display all user-filled details for the admin
# def display_all_details():
#     st.subheader("All User-Filled Industry Details")
#     with get_database_connection() as conn:
#         c = conn.cursor()
#         c.execute("SELECT * FROM industry")
#         industries = c.fetchall()
#         if industries:
#             # Create a DataFrame for better visualization
#             df = pd.DataFrame(industries, columns=[col[0] for col in c.description])
#             ind_df = df[['state_ocmms_id','industry_name', 'industry_category','address','district',
#                          'production_capacity','num_stacks','industry_environment_head','concerned_person_cems',
#                          'industry_representative_email']]


#             # Search functionality
#             search_term = st.text_input("Search Industry", "")
#             if search_term:
#                 df = df[df['industry_name'].str.contains(search_term, case=False, na=False)]
#             col1,col2 = st.columns([6,1])
#             # Display the DataFrame without the Action column first
#             with col1:
#                 st.dataframe(ind_df,column_config={
#                     'state_ocmms_id':'State OCMMS Code',
#                     'industry_category': 'Category',
#                     'industry_name' : 'Industry Name',
#                     'address':'Address',
#                     'district':'District',
#                     'state':'State',
#                     'production_capacity':'Production Capacity',
#                     'num_stacks':'Number of stacks',
#                     'industry_environment_head':'Industry Environment Head',
#                     'industry_instrument_head':'Instrument Head',
#                     'concerned_person_cems':'Concerned Person for CEMS',
#                     'industry_representative_email':'Industry Representative Email Id'
#                 }, hide_index=True)  # Replace with actual column names
#             with col2:
#                 # Add a "View" button for each industry
#                 for index, row in df.iterrows():
#                     if st.button(f"View {row['industry_name']}", key=f"view_{row['ind_id']}"):
#                         show_industry_details(row['ind_id'])  # Call function to show details for the selected industry
#         else:
#             st.warning("No industry details found.")
            
# def show_industry_details(ind_id):
#     """Show detailed information for the selected industry."""
#     st.subheader(f"Details for Industry ID: {ind_id}")
#     with get_database_connection() as conn:
#         c = conn.cursor()

#         # Fetch industry details
#         c.execute("SELECT * FROM industry WHERE ind_id = ?", (ind_id,))
#         industry_details = c.fetchone()

#         if industry_details:
#             # Convert details to a dictionary for display
#             industry_dict = {desc[0]: value for desc, value in zip(c.description, industry_details)}

#             # Display the details in a readable format
#             for key, value in industry_dict.items():
#                 st.markdown(f"**{key.replace('_', ' ').capitalize()}:** {value}")
#         else:
#             st.warning("No details found for the selected industry.")

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


def show_industry_dashboard(user_id):
    """Function to display the industry dashboard with industry details."""
    # st.subheader("Industry Dashboard")
    st.markdown("<h1 style='text-align: center; color: black;'>Industry Dashboard</h1>", unsafe_allow_html=True)

    def fetch_data(query, params=None):
        """Fetch data from the database."""
        with get_database_connection() as conn:
            c = conn.cursor()
            c.execute(query, params or ())
            data = c.fetchall()
            columns = [desc[0] for desc in c.description]  # Extract column names
            return pd.DataFrame(data, columns=columns) if data else None

    # Fetch Industry Details
    industry_query = "SELECT * FROM industry WHERE user_id = ?"
    industry_data = fetch_data(industry_query, (user_id,))

    # Fetch Stack Details
    stack_query = "SELECT * FROM stacks WHERE user_id = ?"
    stack_data = fetch_data(stack_query, (user_id,))
    #
    # Fetch CEMS Details
    cems_query = "SELECT * FROM cems_instruments WHERE user_id_ind = ?"
    cems_data = fetch_data(cems_query, (f"ind_{user_id}",))

    # Display Industry Details
    if industry_data is not None:
        st.markdown("### Industry Details")
        industry = industry_data.iloc[0]  # Assuming one industry per user
        industry_details = {
            "Industry State OCMMS Code": industry['state_ocmms_id'],
            "Industry Category": industry['industry_category'],
            "Industry Name": industry['industry_name'],
            "Address": industry['address'],
            "District": industry['district'],
            "State": industry['state'],
            "Production Capacity": industry['production_capacity'],
            "Number of stacks": industry['num_stacks'],
            "Industry Environment Head": industry['industry_environment_head'],
            "Instrument Head": industry['industry_instrument_head'],
            "Concerned Person for CEMS": industry['concerned_person_cems'],
            "Industry Representative Email Id": industry['industry_representative_email'],
        }
        for field, value in industry_details.items():
            with st.container():
                cols = st.columns([1, 3])  # Adjust widths as needed
                cols[0].markdown(f"<p style='font-weight: bold; text-align: left;'>{field}:</p>",
                                 unsafe_allow_html=True)
                cols[1].markdown(f"<p style='text-align: left;'>{value}</p>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
    else:
        st.warning("No Industry Details Found.")

    # Display Stack Details with Associated CEMS Parameters Horizontally
    if stack_data is not None:
        st.markdown("### Stack and CEMS Details")
        for i, stack in stack_data.iterrows():
            st.markdown(f"#### Stack {i + 1} Details")
            table_data = {
                # "Stack ID": stack_data["stack_id"],
                "Process Attached": stack_data["process_attached"],
                "Stack Type": stack_data["apcd_details"],
                "Latitude": stack_data["latitude"],
                "Longitude": stack_data["longitude"],
                "Stack Shape": stack_data["stack_shape"],
                "Diameter (m)": stack_data["diameter"],
                "Length (m)": stack_data["length"],
                "Width (m)": stack_data["width"],
                "Stack Material": stack_data["stack_material"],
                "Stack Height (m)": stack_data["stack_height"],
                "Platform Height (m)": stack_data["platform_height"],
                "Platform Approachable": stack_data["platform_approachable"],
                "Approaching Media": stack_data["approaching_media"],
                "CEMS Installed": stack_data["cems_installed"],
                "Stack Params": stack_data["stack_params"],
                "Duct Params": stack_data["duct_params"],
                "Follows Formula": stack_data["follows_formula"],
                "Manual Port Installed": stack_data["manual_port_installed"],
                "CEMS Below Manual": stack_data["cems_below_manual"],
                "Parameters": stack_data["parameters"],
            }

            # Convert dictionary to DataFrame
            stck_df = pd.DataFrame(table_data)
            stck_df.index = [f"Stack_{i + 1}" for i in range(len(stck_df))]
            stck_x = stck_df.iloc[i:i+1]
            stck_x.dropna(axis=1, how='all', inplace=True)
            # Display as a table
            # st.table(stck_x)

            # Convert DataFrame to HTML
            html = stck_x.to_html(index=False)

            # Generate CSS for column widths
            column_count = len(stck_x.columns)
            default_width = 100  # Default width for all columns
            specific_widths = {
                # 2: 50,  # Width for the first column
                 # Width for the second column
                # Add more specific widths as needed
            }

            # Create CSS rules
            css_rules = []
            for i in range(1, column_count + 1):
                width = specific_widths.get(i, default_width)  # Use specific width or default
                css_rules.append(f"th:nth-child({i}), td:nth-child({i}) {{ width: {width}px; }}")

            # Combine CSS rules
            custom_css = f"""
            <style>
                table {{
                    width: 100%;  /* Set the table width */
                    border-collapse: collapse;  /* Optional: for better border handling */
                }}
                th, td {{
                    border: 1px solid #ddd;  /* Optional: add borders to cells */
                    padding: 8px;  /* Optional: add padding to cells */
                    text-align: center;  /* Optional: align text to the left */
                }}
                {" ".join(css_rules)}  /* Add all CSS rules */
            </style>
            """

            # Display the table with custom CSS
            st.markdown(custom_css, unsafe_allow_html=True)
            st.markdown(html, unsafe_allow_html=True)

            
            cems_for_stack = pd.DataFrame() # default to an empty DF

            
            # Filter CEMS details for this stack
            if cems_data is not None:
                cems_for_stack = cems_data[cems_data['stack_id'] == stack['stack_id']]
            st.markdown("##### Parameter Details")
            if not cems_for_stack.empty:
                for j, cems in cems_for_stack.iterrows():
                    table_param = {
                        "Parameter": cems['parameter'],
                        "Make": cems['make'],
                        "Model": cems['model'],
                        "Serial Number": cems['serial_number'],
                        "SPCB Approved Emission Limit": cems['emission_limit'],
                        "Measuring Range (Low)": cems['measuring_range_low'],
                        "Measuring Range (High)": cems['measuring_range_high'],
                        "Is Certified?": cems['certified'],
                        "Certification Agency": cems['certification_agency'],
                        "Communication Protocol": cems['communication_protocol'],
                        "Measurement Method": cems['measurement_method'],
                        "Technology": cems['technology'],
                        "Connected to BSPCB?": cems['connected_bspcb'],
                        "BSPCB URL": cems['bspcb_url'],
                        "Connected to CPCB?": cems['connected_cpcb'],
                        "CPCB URL": cems['cpcb_url'],
                    }
    
                    # Convert dictionary to DataFrame
                    param_df = pd.DataFrame(table_param, index=[0])  # Create a DataFrame with a single row
                    param_df.dropna(axis=1, how='all', inplace=True)
    
                    # Convert DataFrame to HTML
                    html = param_df.to_html(index=False)
    
                    # Generate CSS for column widths
                    column_count = len(param_df.columns)
                    default_width = 100  # Default width for all columns
                    specific_widths = {
                        # 2: 50,  # Width for the first column
                        # Width for the second column
                        # Add more specific widths as needed
                    }
    
                    # Create CSS rules
                    css_rules = []
                    for i in range(1, column_count + 1):
                        width = specific_widths.get(i, default_width)  # Use specific width or default
                        css_rules.append(f"th:nth-child({i}), td:nth-child({i}) {{ width: {width}px; }}")
    
                    # Combine CSS rules
                    custom_css = f"""
                                <style>
                                    table {{
                                        width: 100%;  /* Set the table width */
                                        border-collapse: collapse;  /* Optional: for better border handling */
                                    }}
                                    th, td {{
                                        border: 1px solid #ddd;  /* Optional: add borders to cells */
                                        padding: 8px;  /* Optional: add padding to cells */
                                        text-align: center;  /* Optional: align text to the left */
                                    }}
                                    {" ".join(css_rules)}  /* Add all CSS rules */
                                </style>
                                """
    
                    # Display the table with custom CSS
                    st.markdown(custom_css, unsafe_allow_html=True)
                    st.markdown(html, unsafe_allow_html=True)
            else:
                st.warning(f"No CEMS Details Found for Stack {stack['stack_id']}.")
    else:
        st.warning("No Stack Details Found.")

def fill_stacks(user_id):
    """Form to fill stack details."""
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT num_stacks FROM industry WHERE user_id = ?", (user_id,))
        total_stacks = c.fetchone()[0]
        # st.write(total_stacks)
        conn.commit()

        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM stacks WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        # st.write(result)
        completed_stacks = result[0] if result else 0  # Default to 0 if no stacks are completed
        conn.commit()

        # c = conn.cursor()
        # c.execute("SELECT completed_stacks FROM industry WHERE user_id = ?", (user_id,))
        # completed_stacks = c.fetchone()[0]
        # st.write(completed_stacks)
        # conn.commit()

        if completed_stacks >= total_stacks:
            st.success("All stack details are completed.")
            return

    # Display next stack form if not completed all
    current_stack = completed_stacks + 1
    st.subheader(f"Enter Details for Stack {current_stack} of {total_stacks}")

    if f"stack_{current_stack}" not in st.session_state:
        # Simple input fields (without st.form)
        process_attached = st.text_input("Process Attached")
        apcd_details = st.text_input("APCD Details")
        latitude = st.number_input(
            "Latitude", value=None, min_value=24.33611111, max_value=27.52083333, format="%.6f"
        )
        longitude = st.number_input(
            "Longitude", value=None, min_value=83.33055556, max_value=88.29444444, format="%.6f"
        )
        stack_condition = st.selectbox("Stack Condition", ["Wet", "Dry"])
        stack_shape = st.selectbox(
            "Is it a Circular Stack/Rectangular Stack", ["Circular", "Rectangular"]
        )
        if stack_shape == "Circular":
            diameter = st.number_input("Diameter (in meters)", min_value=0.0, format="%.2f")
            length, width = None, None
        else:
            length = st.number_input("Length (in meters)", value=None, min_value=0.0, format="%.2f")
            width = st.number_input("Width (in meters)", value=None, min_value=0.0, format="%.2f")
            diameter = None
        stack_material = st.text_input("Stack Construction Material"
                                       )
        stack_height = st.number_input(
            "Stack Height (in meters)", value=None, min_value=0.0, format="%.2f"
        )
        platform_height = st.number_input(
            "Platform for Manual Monitoring location height from Ground level(in meters)",
            value=None, min_value=0.0, format="%.2f"
        )
        if stack_height is not None and platform_height is not None:
            if platform_height >= stack_height:
                st.error(
                    "Kindly enter valid details. Platform height cannot be greater than or equal to stack height.",
                    icon="🚨"
                )
        platform_approachable = st.selectbox(
            "Is Platform approachable?", ["Yes", "No"]
        )
        if platform_approachable == "Yes":
            approaching_media = st.selectbox(
                "Choose one", ["Ladder", "Lift", "Staircase"]
            )
        else:
            approaching_media = None
            st.error(
                "Platform must be approachable, Follow CPCB Guidelines"
            )
        cems_installed = st.selectbox(
            "Where is CEMS Installed?", ["Stack/Chimney", "Duct", "Both"]
        )
        if cems_installed == "Both":
            stack_params = st.multiselect(
                "Parameters Monitored in Stack",
                ["PM", "SO2", "NOx", "CO", "O2", "NH3", "HCL", "Total Fluoride", "HF", "Hg", "H2S", "CL2"]
            )
            duct_params = st.multiselect(
                "Parameters Monitored in Duct",
                ["PM", "SO2", "NOx", "CO", "O2", "NH3", "HCL", "Total Fluoride", "HF", "Hg", "H2S", "CL2"]
            )
        elif cems_installed == "Duct":
            duct_params = st.multiselect(
                "Parameters Monitored in Duct",
                ["PM", "SO2", "NOx", "CO", "O2", "NH3", "HCL", "Total Fluoride", "HF", "Hg", "H2S", "CL2"]
            )
            stack_params = None
        else:
            stack_params = None  # Ensure it is always a list
            duct_params = None

        # Check if stack_params is not None and is a list
        if stack_params and isinstance(stack_params, list):
            stack_params = ",".join(stack_params)  # Safely join list items into a string
        else:
            stack_params = None  # Fallback in case of no parameters selected or invalid data

        # Check if stack_params is not None and is a list
        if duct_params and isinstance(duct_params, list):
            duct_params = ",".join(duct_params)  # Safely join list items into a string
        else:
            duct_params = None  # Fallback in case of no parameters selected or invalid data

        if stack_shape == "Circular":
            follows_formula = st.selectbox(
                "Does the Installation follows 8D/2D formula?", ["Yes", "No"]
            )
        else:
            follows_formula = st.selectbox(
                "Does the Installation follows (2LW/L+W) criteria (Rectangular)?", ["Yes", "No"]
            )

        if cems_installed in ["Duct"]:
            manual_port_installed = st.selectbox(
                "Has a Manual Monitoring Port been installed in the duct?", ["Yes", "No"]
            )
            if manual_port_installed == "No":
                st.write("Please, Refer CPCB Guidelines")

        elif cems_installed in ["Both"]:
            manual_port_installed = st.selectbox(
                "Has a Manual Monitoring Port been installed in the duct?", ["Yes", "No"]
            )
            if manual_port_installed == "No":
                st.write("Please, Refer CPCB Guidelines")
        else:
            manual_port_installed = None

        cems_below_manual = st.selectbox(
            "Is CEMS Installation point at least 500mm below the Manual monitoring point? ", ["Yes", "No"]
        )
        if cems_below_manual == "No":
            st.write("Please, Refer CPCB Guidelines")

        parameters = st.multiselect(
            "Parameters Monitored",
            ["PM", "SO2", "NOx", "CO", "O2", "NH3", "HCL", "Total Fluoride", "HF", "Hg", "H2S", "CL2", "others"],
        )

        # Submit button
        if st.button("Submit Stack Details"):
            # Collecting all mandatory fields into a list for easy checking
            mandatory_fields = [
                process_attached, apcd_details, latitude, longitude, stack_condition, stack_shape,
                stack_material, stack_height, platform_height, platform_approachable,
                cems_installed, follows_formula, cems_below_manual
            ]

            # Additional conditional fields (check based on shape or type)
            if stack_shape == "Circular":
                mandatory_fields.append(diameter)
            else:
                mandatory_fields.extend([length, width])

            if cems_installed == "Both":
                mandatory_fields.extend([stack_params, duct_params])
            elif cems_installed == "Duct":
                mandatory_fields.append(duct_params)
            if platform_approachable == "Yes":
                mandatory_fields.append(approaching_media)

            # Check if any mandatory field is empty
            if any(field is None or field == "" or field == [] for field in mandatory_fields):
                st.error("All fields are mandatory. Please fill in all required fields.")
                return

            if not parameters:
                st.error("Please select at least one parameter.")
                return
            else:
                st.success("Stack details submitted successfully!")

            with get_database_connection() as conn:
                c = conn.cursor()
                c.execute(""" 
                    INSERT INTO stacks (user_id, user_id_ind, process_attached, apcd_details, latitude, longitude, stack_condition,
                                        stack_shape, diameter, length, width, stack_material, stack_height, 
                                        platform_height, platform_approachable, approaching_media, cems_installed,
                                        stack_params, duct_params, follows_formula, manual_port_installed, 
                                        cems_below_manual, parameters)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    user_id, f'ind_{user_id}', process_attached, apcd_details, latitude, longitude, stack_condition,
                    stack_shape, diameter, length, width, stack_material, stack_height, platform_height,
                    platform_approachable, approaching_media, cems_installed, stack_params,
                    duct_params, follows_formula, manual_port_installed, cems_below_manual,
                    ",".join(parameters)
                ))
                stack_id = c.lastrowid
                conn.commit()

                c.execute("""
                        UPDATE stacks
                        SET number_params = 
                            CASE 
                                WHEN parameters IS NULL OR parameters = '' THEN 0
                                ELSE (LENGTH(parameters) - LENGTH(REPLACE(parameters, ',', '')) + 1)
                            END
                        WHERE stack_id = ?
                    """, (stack_id,))
                conn.commit()

                # Increment the completed_stacks counter
                c.execute("""
                        UPDATE industry
                        SET completed_stacks = completed_stacks + 1
                        WHERE user_id = ?
                    """, (user_id,))
                conn.commit()


            # Save stack state in session
            st.session_state[f"stack_{current_stack}"] = True
            st.session_state["parameters"] = parameters  # Store parameters for CEMS form
            st.success("Stack details saved!")
            st.session_state["current_page"] = f"cems_{current_stack}"  # Move to CEMS details form
            st.rerun()


def fill_cems_details(user_id):
    """Form to fill CEMS details."""
    st.subheader("Enter CEMS Details")

    # Retrieve stack details from the session or database
    with get_database_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT stack_id, process_attached, parameters FROM stacks WHERE user_id = ?", (user_id,))
        stack_details = c.fetchall()

        st.write(stack_details)
        x = stack_details[0][0]
        st.write(x)


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
    available_parameters = [param.strip() for param in available_parameters if
                            param.strip() not in filled_parameter_names]

    if not available_parameters:
        st.warning(f"All parameters for the stack with process '{selected_process}' have already been filled.")
        return

    # Dropdown to select parameter (filter out already filled ones)
    selected_parameter = st.selectbox("Select Parameter", options=available_parameters)

    # Initialize session state to track form reset
    if f"form_reset_{selected_stack_id}" not in st.session_state:
        st.session_state[f"form_reset_{selected_stack_id}"] = False

    # Form for entering CEMS details
    with st.form(f"cems_form_{selected_stack_id}",
                 clear_on_submit=st.session_state[f"form_reset_{selected_stack_id}"]) as form:
        make = st.text_input("Make")
        model = st.text_input("Model")
        serial_number = st.text_input("Serial Number")
        emission_limit = st.number_input("SPCB Approved Emission Limit", min_value=0, value=0)
        measuring_range_low = st.number_input("Measuring Range (Low)", min_value=0, value=0)
        measuring_range_high = st.number_input("Measuring Range (High)", min_value=0, value=0)
        certified = st.selectbox("Is Certified?", ["Yes", "No"])
        if certified == "Yes":
            certification_agency = st.text_input("Certification Agency")
        else:
            certification_agency = None
        communication_protocol = st.selectbox("Communication Protocol", ["4-20 mA", "RS-485", "RS-232"], index=None)
        measurement_method = st.selectbox("Measurement Method", ["In-situ", "Extractive"], index=None)
        technology = st.text_input("Technology")
        connected_bspcb = st.selectbox("Connected to BSPCB?", ["Yes", "No"])
        if connected_bspcb == "Yes":
            bspcb_url = st.text_input("BSPCB URL")
        else:
            bspcb_url = None
        connected_cpcb = st.selectbox("Connected to CPCB?", ["Yes", "No"])
        if connected_cpcb == "Yes":
            cpcb_url = st.text_input("CPCB URL")
        else:
            cpcb_url = None

        submit_cems = st.form_submit_button("Submit CEMS Details")

    if submit_cems:
        if not all([make, model, serial_number, communication_protocol, measurement_method, technology]):
            st.error("All fields are mandatory. Please fill in all fields.")
            return

        # Check for numeric fields: Handle 0.0 as valid input
        if emission_limit is None or measuring_range_low is None or measuring_range_high is None:
            st.error("Numeric fields must have valid values.")
            return

        if measuring_range_low >= measuring_range_high:
            st.error("Measuring Range (Low) must be less than Measuring Range (High).")
            return

        # Check if certification is required
        if certified == "Yes" and not certification_agency:
            st.error("Kindly fill the Certification Agency name.")
            return

        # Validate URLs if needed
        if connected_bspcb == "Yes" and not bspcb_url:
            st.error("Kindly fill the BSPCB URL.")
            return

        if connected_cpcb == "Yes" and not cpcb_url:
            st.error("Kindly fill the CPCB URL.")
            return

        # st.success("CEMS Details submitted successfully!")

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
                    INSERT INTO cems_instruments (stack_id, user_id_ind, parameter, make, model, serial_number, emission_limit, 
                    measuring_range_low, measuring_range_high, certified, certification_agency, communication_protocol, 
                    measurement_method, technology, connected_bspcb, bspcb_url, cpcb_url, connected_cpcb)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    selected_stack_id, f'ind_{user_id}', selected_parameter, make, model, serial_number, measuring_range_low,
                    emission_limit, measuring_range_high, certified, certification_agency, communication_protocol,
                    measurement_method, technology, connected_bspcb, bspcb_url, connected_cpcb, cpcb_url
                ))
                conn.commit()

                c.execute("""
                                        UPDATE stacks
                                        SET completed_parameters = completed_parameters + 1
                                        WHERE stack_id = ?
                                    """, (selected_stack_id,))
                conn.commit()

                st.session_state[f"form_reset_{selected_stack_id}"] = True  # Allow form reset

            st.success(f"CEMS details for {selected_parameter} saved!")
            st.session_state[
                f"cems_{selected_stack_id}_{selected_parameter}"] = True  # Mark CEMS form as completed for this parameter

            st.rerun()

        except Exception as e:
            st.error(f"An error occurred while saving CEMS details: {e}")
            st.session_state[f"form_reset_{selected_stack_id}"] = False  # Prevent reset on error


# Main Function
def main():
    """Main application logic."""
    col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,1,1,1])
    with col1:
        st.image("usaid.png" )  # Display logo
    with col4:
        st.image("bspcb.png")  # Display logo
    with col6:
        st.image("CEEW.png")  # Display logo

    st.markdown(f"<h1 style='text-align: center'>Industry Registration Portal</h1>", unsafe_allow_html=True)


    # st.title("Industry Registration Portal")
    create_database_tables()
    if "selected_ind_id" not in st.session_state:
        st.session_state["selected_ind_id"] = None
    
    # Initialize session state
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = None

    # Show navigation only before login
    if not st.session_state["logged_in"] and not st.session_state["admin_logged_in"]:
        st.sidebar.title("User Login")
        navigation = ["Admin Login","Industry Login/New Industry Registration"]
        selected_page = st.sidebar.selectbox("Select User Type", navigation)


        # Admin Login and Dashboard
        if selected_page == "Admin Login":
                admin_login_page()
                

        # User Login/Registration
        elif selected_page == "Industry Login/New Industry Registration":

            if not st.session_state["logged_in"]:
                # st.header("Please log in or register to continue.")
                menu = ["Login", "Register Industry"]
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

                        def is_email_and_ocmms_unique(email, state_ocmms_id):
                            with get_database_connection() as conn:
                                c = conn.cursor()
                                # Check email uniqueness
                                c.execute("SELECT COUNT(*) FROM user WHERE email = ?", (email,))
                                if c.fetchone()[0] > 0:
                                    return "Email already exists."
                                c = conn.cursor()
                                # Check state_ocmms_id uniqueness
                                c.execute("SELECT COUNT(*) FROM industry WHERE state_ocmms_id = ?", (state_ocmms_id,))
                                if c.fetchone()[0] > 0:
                                    return "State OCMMS ID already exists."
                            return None  # Both are unique

                        # Example during registration:
                        error_message = is_email_and_ocmms_unique(email, state_ocmms_id)
                        if error_message:
                            st.error(error_message)
                        else:
                            # Save data to the database
                            try:
                                conn = get_database_connection()
                                c = conn.cursor()

                                # Insert user (with email used for login)
                                hashed_password = hash_password(password)
                                c.execute("INSERT INTO user (email, password) VALUES (?, ?)", (email, hashed_password))
                                user_id = c.lastrowid
                                conn.commit()
                                user_id_str = f"ind_{user_id}"  # Format user_id like 'ind_1', 'ind_2', etc.

                                # Insert industry
                                c.execute('''INSERT INTO industry (user_id, user_id_ind, industry_category, state_ocmms_id, industry_name, address,
                                                                                    state, district, production_capacity, num_stacks, industry_environment_head,
                                                                                    industry_instrument_head, concerned_person_cems, industry_representative_email)
                                                                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                          (user_id, user_id_str, industry_category, state_ocmms_id, industry_name, address,
                                           state,
                                           district, production_capacity, num_stacks, industry_environment_head,
                                           industry_instrument_head,
                                           concerned_person_cems, email))
                                conn.commit()
                                conn.close()

                                st.success("Industry registered successfully!")
                            except sqlite3.IntegrityError:
                                st.error("This email is already registered. Please use a different email.")
                            except Exception as e:
                                st.write()  # Encapsulate registration logic

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

    # Admin Dashboard
    elif st.session_state["admin_logged_in"]:
        admin_dashboard()

    # User-Specific Dashboard
    elif st.session_state["logged_in"]:
        user_id = st.session_state["user_id"]
        sidebar_forms(user_id)

        # else:
        #     user_id = st.session_state["user_id"]
        #     sidebar_forms(user_id)



if __name__ == "__main__":
    main()

