# app/main_ui.py
import streamlit as st
import uuid
from datetime import datetime
import os

from app.validators import validate_amount
from app.supabase_client import process_donor_and_get_receipt_no, set_receipt_generated_flag
from app.pdf_generator import create_receipt_pdf, ReceiptData

from config import (
    APP_TITLE_PREFIX, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    PAD_Y_LARGE, PAD_Y_MEDIUM, PAD_Y_SMALL, PAD_X_MEDIUM,
    UI_BACKGROUND_LIGHT, UI_PRIMARY_COLOR, UI_ACCENT_COLOR, UI_WARNING_COLOR, UI_ERROR_COLOR,
    UI_TEXT_PRIMARY, UI_TEXT_SECONDARY, UI_TEXT_ON_PRIMARY, BASE_PDF_OUTPUT_DIR
)

def ui_form_page():
    # Initialize session state for PDF path and receipt number
    if "pdf_path" not in st.session_state:
        st.session_state["pdf_path"] = None
    if "receipt_no" not in st.session_state:
        st.session_state["receipt_no"] = None
    if "show_form" not in st.session_state:
        st.session_state["show_form"] = True
    # Define keys for input widgets
    name_key = "name_input"
    address_key = "address_input"
    pan_key = "pan_input"
    amount_key = "amount_input"

    # This block now runs at the top of the script on a rerun
    if st.session_state.get("form_cleared"):
        st.session_state[name_key] = ""
        st.session_state[address_key] = ""
        st.session_state[pan_key] = ""
        st.session_state[amount_key] = ""
        st.session_state["form_cleared"] = False # Reset the flag

    if st.session_state["show_form"]:
        with st.form(key="single_donor_form"):
            date = st.date_input("Date", value=datetime.today())
            name = st.text_input("Donor Name", key=name_key)
            address = st.text_input("Address", key=address_key)
            pan = st.text_input("PAN Number", key=pan_key)
            amount = st.text_input("Amount (in numbers)", key=amount_key)
            
            submit_btn = st.form_submit_button("Generate Receipt")
            clear_btn = st.form_submit_button("Clear Form")

            if clear_btn:
                st.session_state["form_cleared"] = True
                st.rerun()

            if submit_btn:
                errors = []
                db_formatted_date = date.strftime("%Y-%m-%d")
                pdf_formatted_date = date.strftime("%d-%m-%Y")
                valid_amount, error_msg = validate_amount(amount)
                if error_msg:
                    st.error(error_msg)
                    return None

                # Name validation: only alphabetic and spaces
                if not name.replace(' ', '').isalpha():
                    errors.append("❌ Name must contain only alphabetic characters and spaces.")

                # Only validate date and amount
                if not valid_amount:
                    # This check is now redundant as validate_amount handles it,
                    # but we keep it as a fallback.
                    errors.append("❌ Amount must be a positive number")
                # (date is always valid from st.date_input)

                if errors:
                    for err in errors:
                        st.error(err)
                    st.session_state["pdf_path"] = None
                    st.session_state["receipt_no"] = None
                else:
                    st.info("⏳ Validating donor with database...")
                    user_email = st.session_state.get('user_email', 'UNKNOWN')
                    success, result_string = process_donor_and_get_receipt_no(
                        date=db_formatted_date,
                        name=name,
                        amount=valid_amount,
                        address=address,
                        pan=pan,
                        user_email=user_email,
                        entry_mode="single"
                    )
                    if not success:
                        st.error(f"❌ Error: {result_string}")
                        st.session_state["pdf_path"] = None
                        st.session_state["receipt_no"] = None
                    elif result_string == 'exists':
                        st.warning("⚠️ Duplicate: This record already exists.")
                        st.session_state["pdf_path"] = None
                        st.session_state["receipt_no"] = None
                    elif 'ONL' in result_string:
                        receipt_no = result_string
                        st.success(f"✅ Donor added. Generating PDF for {receipt_no}...")
                        receipt_data = ReceiptData(
                            receipt_no=receipt_no,
                            date=pdf_formatted_date,
                            name=name,
                            amount=valid_amount,
                            address=address,
                            pan=pan
                        )
                        if not st.session_state.get('current_pdf_session_dir'):
                            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            session_dir_name = f"ht_donation_receipt_{timestamp}"
                            from config import BASE_PDF_OUTPUT_DIR
                            full_session_dir_path = os.path.join(BASE_PDF_OUTPUT_DIR, session_dir_name)
                            os.makedirs(full_session_dir_path, exist_ok=True)
                            st.session_state['current_pdf_session_dir'] = full_session_dir_path
                            st.info(f"PDFs for this session will be saved in: {full_session_dir_path}", icon="🗂️")
                        pdf_path = create_receipt_pdf(receipt_data, st.session_state['current_pdf_session_dir'])
                        if pdf_path:
                            if set_receipt_generated_flag(receipt_no):
                                st.success(f"✅ Success! PDF saved to {pdf_path}")
                                st.session_state["pdf_path"] = pdf_path
                                st.session_state["receipt_no"] = receipt_no
                                # Do not hide the form after success
                            else:
                                st.warning(f"⚠️ PDF created, but DB update failed for {receipt_no}!")
                                st.session_state["pdf_path"] = None
                                st.session_state["receipt_no"] = None
                        else:
                            st.error(f"❌ PDF generation failed for {receipt_no}.")
                            st.session_state["pdf_path"] = None
                            st.session_state["receipt_no"] = None
                    else:
                        st.error(f"❌ Unknown Error: Server returned '{result_string}'")
                        st.session_state["pdf_path"] = None
                        st.session_state["receipt_no"] = None

    if st.button("← Back to Mode Selection"):
        st.session_state['mode'] = None
        st.rerun()
    if st.button("← Back to Main Dashboard"):
        st.session_state['mode'] = None
        st.session_state['active_section'] = None
        st.rerun()