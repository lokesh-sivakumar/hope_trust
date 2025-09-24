# app/config.py
import os
import sys
from supabase import create_client, Client
import streamlit as st

# --- Supabase Configuration ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

_supabase_client_instance: Client = None

def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client, cached across reruns."""
    global _supabase_client_instance
    if _supabase_client_instance is None:
        try:
            _supabase_client_instance = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            st.error(f"❌ Failed to initialize Supabase client: {e}. Check API keys and URL in .streamlit/secrets.toml.", icon="❌")
            st.stop()
    return _supabase_client_instance

# --- Asset Paths ---
def get_streamlit_app_dir():
    """Helper to get the directory of the main streamlit_app.py file."""
    return os.path.dirname(os.path.abspath(sys.argv[0]))

ASSETS_DIR_STREAMLIT = os.path.join(get_streamlit_app_dir(), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR_STREAMLIT, "LOGO.png")
SIGNATURE_PATH = os.path.join(ASSETS_DIR_STREAMLIT, "SIGNU.png")
QR_CODE_PATH = os.path.join(ASSETS_DIR_STREAMLIT, "qr.png")
FONT_PATH = os.path.join(ASSETS_DIR_STREAMLIT, "Poppins-Regular.ttf")
FONT_BOLD_PATH = os.path.join(ASSETS_DIR_STREAMLIT, "Poppins-Bold.ttf")

# --- PDF Output Configuration ---
BASE_PDF_OUTPUT_DIR = "ht_donation_receipt"
os.makedirs(BASE_PDF_OUTPUT_DIR, exist_ok=True)

# --- UI Color Palette ---
UI_PRIMARY_COLOR = "#FFD100"
UI_PRIMARY_COLOR_DARK = "#CCA700"
UI_NEUTRAL_WHITE = "#FFFFFF"
UI_NEUTRAL_BLACK = "#000000"
UI_GREY_LIGHTEST = "#F5F5F5"
UI_GREY_LIGHT = "#E0E0E0"
UI_GREY_MEDIUM = "#B0B0B0"
UI_GREY_DARK = "#4A4A4A"
UI_GREY_DARKER = "#2C2C2C"
UI_BACKGROUND_LIGHT = "#F5F5F5"  # <-- Add this
UI_SUCCESS_GREEN = "#4CAF50"
UI_ERROR_RED = "#F44336"
UI_WARNING_ORANGE = "#FF9800"
UI_WARNING_COLOR = UI_WARNING_ORANGE
UI_ERROR_COLOR = UI_ERROR_RED
UI_TEXT_PRIMARY = "#2C2C2C"      # Or any color you want for primary text
UI_TEXT_SECONDARY = "#4A4A4A"    # Or any color you want for secondary text
UI_ACCENT_COLOR = "#FF4081"  # Add this line for accent color (choose any color you prefer)
UI_TEXT_ON_PRIMARY = UI_NEUTRAL_BLACK

# --- UI Font Settings ---
FONT_FAMILY_REGULAR = 'sans-serif'
FONT_FAMILY_BOLD = 'sans-serif'
FONT_FALLBACK = 'sans-serif'

# --- UI General Settings ---
APP_TITLE_PREFIX = "HOPE TRUST - "
PAD_Y_LARGE = 20
PAD_Y_MEDIUM = 10
PAD_Y_SMALL = 5
PAD_X_MEDIUM = 10

# --- Window Size Defaults (for compatibility with all imports) ---
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768

# --- Tkinter specific styling (obsolete for Streamlit) ---
def initialize_app_style(root_window):
    pass

LISTBOX_BG = None
LISTBOX_FG = None
LISTBOX_SELECT_BG = None
LISTBOX_SELECT_FG = None