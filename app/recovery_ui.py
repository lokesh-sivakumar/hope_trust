# app/recovery_ui.py
import streamlit as st
from datetime import datetime
from app.supabase_client import fetch_missing_receipts, set_receipt_generated_flag
from app.pdf_generator import create_receipt_pdf, ReceiptData
from app.config import (
    APP_TITLE_PREFIX, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    PAD_Y_LARGE, PAD_Y_MEDIUM, PAD_Y_SMALL, PAD_X_MEDIUM,
    UI_BACKGROUND_LIGHT, UI_PRIMARY_COLOR, UI_ACCENT_COLOR, UI_WARNING_COLOR, UI_ERROR_COLOR,
    UI_TEXT_PRIMARY, UI_TEXT_SECONDARY, UI_TEXT_ON_PRIMARY, BASE_PDF_OUTPUT_DIR
)
import os
from app.zip_utils import create_zip_from_directory

def recovery_page():
    # Initialize state
    if 'recovery_page_state' not in st.session_state:
        st.session_state.recovery_page_state = 'initial'
    if 'recovery_data' not in st.session_state:
        st.session_state.recovery_data = []
    if 'selected_receipts' not in st.session_state:
        st.session_state.selected_receipts = []
    if 'generated_receipts_info' not in st.session_state:
        st.session_state.generated_receipts_info = []

    # State Machine
    if st.session_state.recovery_page_state == 'initial':
        st.info("Click the button below to find receipts that haven't been generated.")
        if st.button("Find Missing Receipts"):
            st.session_state.recovery_page_state = 'fetching'
            st.rerun()

    elif st.session_state.recovery_page_state == 'fetching':
        # === PDF Session Directory Initialization ===
        if not st.session_state.get('current_pdf_session_dir'):
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            session_dir_name = f"ht_donation_receipt_{timestamp}"
            full_session_dir_path = os.path.join(BASE_PDF_OUTPUT_DIR, session_dir_name)
            os.makedirs(full_session_dir_path, exist_ok=True)
            st.session_state['current_pdf_session_dir'] = full_session_dir_path
            st.info(f"PDFs for this session will be saved in: {full_session_dir_path}", icon="🗂️")

        with st.spinner("⏳ Fetching missing receipts..."):
            success, data = fetch_missing_receipts()
            if success:
                st.session_state.recovery_data = data
            else:
                st.session_state.recovery_data = []
            st.session_state.recovery_page_state = 'show_list'
            st.rerun()

    elif st.session_state.recovery_page_state == 'show_list':
        if not st.session_state.recovery_data:
            st.error("❌ Failed to fetch missing receipts or none found.")
            if st.button("Try Again"):
                st.session_state.recovery_page_state = 'initial'
                st.rerun()
        else:
            st.success(f"✅ Found {len(st.session_state.recovery_data)} record(s) to regenerate. Please select from the list below.")
            display_list = [
                f"{item.get('receipt_no', 'N/A')} - {item.get('name', 'N/A')} - ₹{item.get('amount', 0):,.2f} - {item.get('date', 'N/A')}"
                for item in st.session_state.recovery_data
            ]
            st.session_state.selected_receipts = st.multiselect("Select receipts to regenerate:", options=display_list)

            if st.button("Regenerate Selected"):
                if not st.session_state.selected_receipts:
                    st.warning("Please select at least one receipt to regenerate.")
                else:
                    st.session_state.recovery_page_state = 'processing'
                    st.rerun()

    elif st.session_state.recovery_page_state == 'processing':
        successful_generations = 0
        st.session_state.generated_receipts_info = []
        total_selected = len(st.session_state.selected_receipts)
        data = st.session_state.recovery_data
        
        for display_str in st.session_state.selected_receipts:
            item_dict = next((item for item in data if display_str.startswith(item.get('receipt_no', ''))), None)
            if not item_dict:
                st.warning(f"⚠️ Could not find record for: {display_str}")
                continue

            receipt_no = item_dict.get('receipt_no', '').strip()
            name = item_dict.get('name')
            address = item_dict.get('address')
            pan = item_dict.get('pan')
            amount = item_dict.get('amount')
            date = item_dict.get('date')

            if not all([receipt_no, name, address, pan, amount, date]):
                st.error(f"❌ Skipped incomplete record: {receipt_no}")
                continue

            try:
                parsed_date = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = parsed_date.strftime('%d-%m-%Y')
            except ValueError:
                formatted_date = date

            receipt_data = ReceiptData(
                receipt_no=receipt_no,
                date=formatted_date,
                name=name,
                amount=amount,
                address=address,
                pan=pan
            )

            pdf_path = create_receipt_pdf(receipt_data, st.session_state['current_pdf_session_dir'])

            if pdf_path:
                if set_receipt_generated_flag(receipt_no):
                    successful_generations += 1
                    st.session_state.generated_receipts_info.append(display_str)
                else:
                    st.warning(f"⚠️ Generated PDF for {receipt_no}, but FAILED to update DB flag.")
            else:
                st.error(f"❌ Failed to generate PDF for: {receipt_no}")

        st.info(f"✅ Generated {successful_generations}/{total_selected} PDFs.")
        st.session_state.recovery_page_state = 'finished'
        st.rerun()

    elif st.session_state.recovery_page_state == 'finished':
        st.success("PDF generation process complete.")
        st.write("Successfully generated PDFs for:")
        for item in st.session_state.generated_receipts_info:
            st.write(item)

        # --- Download as ZIP ---
        if st.session_state.generated_receipts_info:
            zip_bytes = create_zip_from_directory(st.session_state['current_pdf_session_dir'])
            if zip_bytes:
                st.download_button(
                    label="Download All as ZIP",
                    data=zip_bytes,
                    file_name=f"{os.path.basename(st.session_state['current_pdf_session_dir'])}.zip",
                    mime="application/zip"
                )

        if st.button("Regenerate More"):
            st.session_state.recovery_page_state = 'initial'
            st.session_state.selected_receipts = []
            st.session_state.recovery_data = []
            st.session_state.generated_receipts_info = []
            st.rerun()

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Mode Selection"):
            st.session_state.recovery_page_state = 'initial'
            st.session_state.selected_receipts = []
            st.session_state.recovery_data = []
            st.session_state['mode'] = None
            st.rerun()
    with col2:
        if st.button("← Back to Main Dashboard"):
            st.session_state.recovery_page_state = 'initial'
            st.session_state.selected_receipts = []
            st.session_state.recovery_data = []
            st.session_state['mode'] = None
            st.session_state['active_section'] = None
            st.rerun()