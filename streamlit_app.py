import streamlit as st
import os
import sys
from datetime import datetime
import base64

# Add the 'app' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# === Import config elements including BASE_PDF_OUTPUT_DIR ===
from app.config import (
    get_supabase_client, APP_TITLE_PREFIX, LOGO_PATH, BASE_PDF_OUTPUT_DIR,
    UI_PRIMARY_COLOR, UI_PRIMARY_COLOR_DARK, UI_NEUTRAL_WHITE, UI_NEUTRAL_BLACK,
    UI_GREY_LIGHTEST, UI_GREY_LIGHT, UI_GREY_MEDIUM, UI_GREY_DARK, UI_GREY_DARKER,
    UI_SUCCESS_GREEN, UI_ERROR_RED, UI_WARNING_ORANGE, UI_TEXT_ON_PRIMARY
)

from app.excel_ui import excel_upload_page
from app.recovery_ui import recovery_page
from app.main_ui import ui_form_page
from app.update_ui import update_page

#
# === Set page configuration at the very top ===
st.set_page_config(
    page_title="Hope Trust App",
    page_icon=LOGO_PATH,  # Use NGO logo as page icon
    layout="centered",
    initial_sidebar_state="auto"
)

# === Function to inject custom CSS ===
def inject_custom_css():
    st.markdown(f"""
    <style>
    /* Make sidebar wider and font smaller/minimalistic */
    section[data-testid="stSidebar"] > div:first-child {{
        width: 280px !important;
        min-width: 280px !important;
        max-width: 320px !important;
    }}
    .stSidebar, .stSidebarContent, .stSidebar .stMarkdown, .stSidebar .stHeader, .stSidebar .stImage, .stSidebar .stButton {{
        font-size: 0.92rem !important;
        color: {UI_GREY_DARKER};
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.2px;
    }}
    .stSidebar .stHeader {{
        font-size: 1.05rem !important;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    .stSidebar .stImage {{
        margin-bottom: 1rem;
    }}
    /* Main app styles remain unchanged */
    body, .stApp {{
        background-color: {UI_NEUTRAL_WHITE};
        color: {UI_GREY_DARKER};
        font-family: 'Poppins', sans-serif;
    }}
    .stApp {{
        padding: 0;
    }}
    .modern-card {{
        background: {UI_GREY_LIGHTEST};
        border-radius: 18px;
        box-shadow: 0 2px 12px rgba(44,44,44,0.04);
        padding: 2.5rem 2rem 2rem 2rem;
        margin: 2rem auto;
        max-width: 420px;
    }}
    .modern-title {{
        color: {UI_GREY_DARKER};
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: center;
        letter-spacing: -1px;
    }}
    .modern-subtitle {{
        color: {UI_PRIMARY_COLOR};
        font-size: 1.1rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 1.5rem;
        letter-spacing: 1px;
    }}
    .modern-input input {{
        background: {UI_NEUTRAL_WHITE};
        border: 1.5px solid {UI_GREY_LIGHT};
        border-radius: 8px;
        padding: 0.75em 1em;
        font-size: 1rem;
        margin-bottom: 1.2rem;
        transition: border 0.2s;
    }}
    .modern-input input:focus {{
        border: 1.5px solid {UI_PRIMARY_COLOR};
        outline: none;
    }}
    .modern-btn {{
        background: {UI_PRIMARY_COLOR};
        color: {UI_NEUTRAL_BLACK};
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.7em 0;
        width: 100%;
        margin-top: 1rem;
        transition: background 0.2s, color 0.2s;
        box-shadow: 0 1px 4px rgba(44,44,44,0.07);
    }}
    .modern-btn:hover {{
        background: {UI_PRIMARY_COLOR_DARK};
        color: {UI_GREY_DARKER};
    }}
    .modern-logo {{
        display: block;
        margin: 0 auto 1.5rem auto;
        width: 90px;
    }}
    </style>
    """, unsafe_allow_html=True)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def render_header(title):
    with st.container():
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; background-color: {UI_GREY_LIGHTEST}; border-radius: 10px; margin-bottom: 2rem;">
                <div style="display: flex; align-items: center;">
                    <img src="data:image/png;base64,{get_base64_image(LOGO_PATH)}" style="width: 50px; height: 50px; margin-right: 15px;" />
                    <div>
                        <h1 style="color: {UI_GREY_DARKER}; margin: 0; font-size: 1.5rem; font-weight: 700;">HOPE TRUST</h1>
                    </div>
                </div>
                <h2 style="color: {UI_PRIMARY_COLOR}; margin: 0; font-size: 1.2rem; font-weight: 600;">{title}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

# === Session State Initialization ===
for key, default in [
    ('logged_in', False),
    ('mode', None),
    ('selected_role', None),
    ('user_email', None),
    ('user_metadata', None),
    ('current_pdf_session_dir', None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Initialize a new session state variable for the active section
if 'active_section' not in st.session_state:
    st.session_state['active_section'] = None

# === Inject custom CSS FIRST ===
inject_custom_css()

# === PAGE FUNCTIONS ===

def login_page():
    with st.form("login_form"):
        st.markdown('<div class="modern-input">', unsafe_allow_html=True)
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        st.markdown('</div>', unsafe_allow_html=True)
        login_button = st.form_submit_button("Login", type="primary")
        if login_button:
            if not email or not password:
                st.error("Email and password cannot be empty.")
                return
            try:
                supabase_client = get_supabase_client()
                if supabase_client is None:
                    st.error("Supabase client not available.")
                    return
                auth_response = supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                if auth_response.user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_email'] = auth_response.user.email
                    st.session_state['user_metadata'] = auth_response.user.user_metadata
                    user_app_meta = getattr(auth_response.user, "app_metadata", None) or getattr(auth_response.user, "raw_app_meta_data", None)
                    user_role = None
                    if user_app_meta and "roles" in user_app_meta and user_app_meta["roles"]:
                        user_role = user_app_meta["roles"][0]  # Take the first role
                    st.session_state['selected_role'] = user_role
                    st.success(f"✅ Login Successful. Welcome, {auth_response.user.email}!", icon="👋")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.", icon="🚫")
            except Exception as e:
                st.error(f"❌ Login Failed: {e}. Check credentials or network.", icon="🚨")

def mode_selection_page():
    st.markdown("---")
    active_section = st.session_state.get('active_section')
    selected_role = st.session_state.get('selected_role')

    if active_section is None:
        if selected_role in ['admin', 'super_volunteer']:
            if st.button("🧾 Data Management", use_container_width=True, key="cat_data_mgmt"):
                st.session_state['active_section'] = 'data_management'
                st.rerun()
        if st.button("📊 Metrics & Reporting", use_container_width=True, key="cat_metrics"):
            st.session_state['active_section'] = 'metrics'
            st.rerun()
        if st.button("🗓️ Events", use_container_width=True, key="cat_events"):
            st.session_state['active_section'] = 'events'
            st.rerun()
        if selected_role == 'admin':
            if st.button("👑 Admin Tools", use_container_width=True, key="cat_admin"):
                st.session_state['active_section'] = 'admin_tools'
                st.rerun()

    # If a section is active, show the sub-buttons for that section
    else:
        if st.button("← Back to Main Dashboard"):
            st.session_state['active_section'] = None
            st.rerun()
        st.markdown("---")

        # --- Data Management Sub-menu ---
        if active_section == 'data_management' and selected_role in ['admin', 'super_volunteer']:
            st.markdown(f"<h2 style='color: {UI_GREY_DARK};'>🧾 Data Management</h2>", unsafe_allow_html=True)
            st.write("Manage donor receipts and organizational data.")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("➕ Add Single Donor", key="btn_single_donor", use_container_width=True):
                    st.session_state['mode'] = 'ui_form'
                    st.rerun()
            with col2:
                if st.button("📄 Upload Excel File", key="btn_excel_upload", use_container_width=True):
                    st.session_state['mode'] = 'excel_upload'
                    st.rerun()
            with col3:
                if st.button("🔄 Recover Missing", key="btn_recover_receipts", use_container_width=True):
                    st.session_state['mode'] = 'recovery'
                    st.rerun()
            with col4:
                if st.button("✏️ Update Record", key="btn_update_record", use_container_width=True):
                    st.session_state['mode'] = 'update'
                    st.rerun()

        # --- Metrics & Reporting Sub-menu ---
        elif active_section == 'metrics':
            st.markdown(f"<h2 style='color: {UI_GREY_DARK};'>📊 Metrics & Reporting</h2>", unsafe_allow_html=True)
            st.write("View reports and key performance indicators.")
            col1, col2, col3 = st.columns(3)
            if selected_role in ['admin', 'super_volunteer']:
                with col1:
                    if st.button("📈 Donation Metrics", key="btn_donor_reports", use_container_width=True):
                        st.info("Donation Metrics page (Coming Soon!)", icon="📊")
            with col2:
                if st.button("👥 Volunteer Metrics", key="btn_volunteer_metrics", use_container_width=True):
                    st.info("Volunteer Metrics page (Coming Soon!)", icon="👥")

        # --- Events Sub-menu ---
        elif active_section == 'events':
            st.markdown(f"<h2 style='color: {UI_GREY_DARK};'>🗓️ Events</h2>", unsafe_allow_html=True)
            st.write("Manage and view upcoming NGO events.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📅 Event Calendar", key="btn_event_calendar", use_container_width=True):
                    st.info("Event Calendar page (Coming Soon!)", icon="📅")
            if selected_role in ['admin', 'super_volunteer']:
                with col2:
                    if st.button("📝 Manage Events", key="btn_event_registration", use_container_width=True):
                        st.info("Event Management page (Coming Soon!)", icon="📝")

        # --- Admin Tools Sub-menu ---
        elif active_section == 'admin_tools' and selected_role == 'admin':
            st.markdown(f"<h2 style='color: {UI_GREY_DARK};'>👑 Admin Tools</h2>", unsafe_allow_html=True)
            st.write("Manage application users and settings.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚙️ User Management", key="btn_user_management", use_container_width=True):
                    st.info("User Management page (Coming Soon!)", icon="⚙️")

    st.markdown("---")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['selected_role'] = None
        st.session_state['active_section'] = None # Reset on logout
        st.rerun()

# === MAIN APP LOGIC ===
if __name__ == "__main__":
    if not st.session_state['logged_in']:
        render_header("User Login")
        login_page()
    elif not st.session_state.get('selected_role') or st.session_state['selected_role'] not in ["admin", "super_volunteer", "volunteer"]:
        st.error("No valid role assigned. Please contact admin.")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['selected_role'] = None
            st.session_state['user_email'] = None
            st.session_state['user_metadata'] = None
            st.rerun()
    else:
        with st.sidebar:
            st.image(LOGO_PATH, width=80)
            st.header("Navigation")
            st.write(f"Logged in as: **{st.session_state.get('user_email', 'N/A')}**")
            st.write(f"Current Role: **{st.session_state.get('selected_role', 'N/A')}**")
            st.markdown("---")
            # Remove Home (Role Dashboard) and Change Role buttons
            if st.button("Logout", key="sidebar_logout"):
                st.session_state['logged_in'] = False
                st.session_state['user_email'] = None
                st.session_state['user_metadata'] = None
                st.session_state['selected_role'] = None
                st.session_state['mode'] = None
                st.session_state['active_section'] = None # Reset on logout
                st.rerun()

        if st.session_state['mode'] == 'ui_form':
            page_title = "Add Single Donor"
        elif st.session_state['mode'] == 'excel_upload':
            page_title = "Upload Excel File"
        elif st.session_state['mode'] == 'recovery':
            page_title = "Recover Missing Receipts"
        elif st.session_state['mode'] == 'update':
            page_title = "Update Receipt Details"
        else:
            page_title = "Dashboard"
        
        render_header(page_title)
        
        # Main content area based on 'mode'
        if st.session_state['mode'] == 'ui_form':
            ui_form_page()
        elif st.session_state['mode'] == 'excel_upload':
            excel_upload_page()
        elif st.session_state['mode'] == 'recovery':
            recovery_page()
        elif st.session_state['mode'] == 'update':
            update_page()
        else:
            mode_selection_page()