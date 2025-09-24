# app/main_ui.py
import streamlit as st
import uuid
from datetime import datetime
import os

from app.validators import validate_amount, validate_name, validate_pan, validate_date
from app.supabase_client import process_donor_and_get_receipt_no, set_receipt_generated_flag
from app.pdf_generator import create_receipt_pdf, ReceiptData

from config import (
    APP_TITLE_PREFIX, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    PAD_Y_LARGE, PAD_Y_MEDIUM, PAD_Y_SMALL, PAD_X_MEDIUM,
    UI_BACKGROUND_LIGHT, UI_PRIMARY_COLOR, UI_ACCENT_COLOR, UI_WARNING_COLOR, UI_ERROR_COLOR,
    UI_TEXT_PRIMARY, UI_TEXT_SECONDARY, UI_TEXT_ON_PRIMARY, BASE_PDF_OUTPUT_DIR
)

def ui_form_page():
    # Define keys for input widgets
    date_key = "date_input"
    name_key = "donor_name_input"
    address_key = "address_input"
    pan_key = "pan_input"
    amount_key = "amount_input"

    # Callback to reset form fields
    def clear_form():
        st.session_state[date_key] = datetime.now().strftime('%d.%m.%y')
        st.session_state[name_key] = ""
        st.session_state[address_key] = ""
        st.session_state[pan_key] = ""
        st.session_state[amount_key] = None
        st.session_state["pdf_path"] = None
        st.session_state["receipt_no"] = None

    # Initialize session state for PDF path and receipt number
    if "pdf_path" not in st.session_state:
        st.session_state["pdf_path"] = None
    if "receipt_no" not in st.session_state:
        st.session_state["receipt_no"] = None
    if "show_form" not in st.session_state:
        st.session_state["show_form"] = True

    # Initialize form fields in session state if they don't exist
    if date_key not in st.session_state:
        st.session_state[date_key] = datetime.now().strftime('%d.%m.%y')
    if name_key not in st.session_state:
        st.session_state[name_key] = ""
    if address_key not in st.session_state:
        st.session_state[address_key] = ""
    if pan_key not in st.session_state:
        st.session_state[pan_key] = ""
    if amount_key not in st.session_state:
        st.session_state[amount_key] = None # Use None for number_input


    # Display download button if a PDF has been generated
    if st.session_state.get("pdf_path") and st.session_state.get("receipt_no"):
        st.success(f"✅ Success! PDF for {st.session_state['receipt_no']} generated.")
        with open(st.session_state["pdf_path"], "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="Download Receipt",
            data=pdf_bytes,
            file_name=os.path.basename(st.session_state["pdf_path"]),
            mime="application/pdf"
        )

    if st.session_state["show_form"]:
        # Create a form for the input fields
        with st.form(key='donor_form'):
            # Input fields
            st.text_input("Date", key=date_key)
            st.text_input("Donor Name", key=name_key)
            st.number_input("Amount", format="%.2f", key=amount_key)
            st.text_input("PAN", key=pan_key)
            st.text_area("Address", key=address_key)

            col1, col2 = st.columns(2)
            with col1:
                submit_btn = st.form_submit_button("Generate Receipt", use_container_width=True)
            with col2:
                clear_btn = st.form_submit_button("Clear Form", on_click=clear_form, use_container_width=True)

            if submit_btn:
                errors = []

                date_obj, date_error = validate_date(st.session_state[date_key])
                if date_error:
                    errors.append(f"Date: {date_error}")

                # Validate form inputs
                _, name_error = validate_name(st.session_state[name_key])
                if name_error:
                    errors.append(name_error)

                _, pan_error = validate_pan(st.session_state[pan_key])
                if pan_error:
                    errors.append(f"PAN: {pan_error}")

                valid_amount, amount_error = validate_amount(st.session_state[amount_key])
                if amount_error:
                    errors.append(f"Amount: {amount_error}")

                if errors:
                    for err in errors:
                        st.error(err)
                    st.session_state["pdf_path"] = None
                    st.session_state["receipt_no"] = None
                else:
                    pdf_formatted_date = date_obj.strftime("%d-%m-%Y")
                    db_formatted_date = date_obj.strftime("%Y-%m-%d")

                    st.info("⏳ Validating donor with database...")
                    user_email = st.session_state.get('user_email', 'UNKNOWN')
                    success, result_string = process_donor_and_get_receipt_no(
                        date=db_formatted_date,
                        name=st.session_state[name_key],
                        amount=valid_amount,
                        address=st.session_state[address_key],
                        pan=st.session_state[pan_key],
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
                            name=st.session_state[name_key],
                            amount=valid_amount,
                            address=st.session_state[address_key],
                            pan=st.session_state[pan_key]
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
                                st.session_state["pdf_path"] = pdf_path
                                st.session_state["receipt_no"] = receipt_no
                                st.rerun()
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Mode Selection"):
            st.session_state['mode'] = None
            st.rerun()
    with col2:
        if st.button("← Back to Main Dashboard"):
            st.session_state['mode'] = None
            st.session_state['active_section'] = None
            st.rerun()