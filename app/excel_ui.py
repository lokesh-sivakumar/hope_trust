# app/excel_ui.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dateutil.parser import parse

from app.validators import validate_amount, validate_pan, validate_name, validate_date
from app.supabase_client import process_donor_and_get_receipt_no, set_receipt_generated_flag
from app.pdf_generator import create_receipt_pdf, ReceiptData
from app.config import BASE_PDF_OUTPUT_DIR
from app.zip_utils import create_zip_from_directory

def excel_upload_page():
    # === PDF Session Directory Initialization ===
    if not st.session_state.get('current_pdf_session_dir'):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir_name = f"ht_donation_receipt_{timestamp}"
        full_session_dir_path = os.path.join(BASE_PDF_OUTPUT_DIR, session_dir_name)
        os.makedirs(full_session_dir_path, exist_ok=True)
        st.session_state['current_pdf_session_dir'] = full_session_dir_path
        st.info(f"PDFs for this session will be saved in: {full_session_dir_path}", icon="🗂️")

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
    process_btn = st.button("Process Excel File")

    if process_btn:
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file, dtype=str).fillna('')
                st.info(f"📄 Reading {len(df)} rows...")
            except Exception as e:
                st.error(f"❌ Failed to read Excel file: {e}")
                return

            # Normalize column headers to uppercase for consistent mapping
            df.columns = [str(c).strip().upper() for c in df.columns]

            # Define the mapping from client headers to application headers
            column_mapping = {
                'S.NO': 'Serial No',
                'D.O.D': 'Date',
                'DONOR NAME': 'Name',
                'AMOUNT': 'Amount',
                'RECEIPT NUMBER': 'RECEIPT NUMBER'
            }

            # Rename the columns based on the mapping
            df.rename(columns=column_mapping, inplace=True)

            # After renaming, check for and add default columns if they are missing
            if 'Address' not in df.columns:
                df['Address'] = 'Tamil Nadu'  # Default value

            if 'Pan' not in df.columns:
                df['Pan'] = 'xxxxx1234x'  # Default value

            # Define the columns that MUST have data in the Excel file
            required_columns = ['Name', 'Amount', 'Date', 'RECEIPT NUMBER']
            if not all(col in df.columns for col in required_columns):
                # This check ensures the essential columns were found and mapped correctly
                st.error(f"Excel file is missing one or more required columns: {required_columns}")
                return

            success_count, skipped_count, error_count = 0, 0, 0
            total_rows = len(df)
            log_messages = []

            progress_bar = st.progress(0)
            for index, row in df.iterrows():
                row_num = index + 2
                progress_bar.progress((index + 1) / total_rows)
                errors = []

                # Skip if receipt number is present (already has a physical receipt or marked as DUM)
                receipt_no = str(row.get('RECEIPT NUMBER', '')).strip().upper()
                if receipt_no and (receipt_no.startswith('R7-') or receipt_no == 'DUM'):
                    log_messages.append(f"Skipped Row {row_num}: Receipt number present or marked as DUM ({receipt_no}).")
                    skipped_count += 1
                    continue

                # --- Validation using new functions ---
                date_str = str(row.get('Date', '')).strip()
                date_obj, date_error = validate_date(date_str)
                if date_error:
                    errors.append(f"Date ('{date_str}'): {date_error}")

                name = str(row.get('Name', '')).strip()
                is_valid_name, name_error = validate_name(name)
                if not is_valid_name:
                    errors.append(name_error)

                amount_str = str(row.get('Amount', '')).strip()
                amount_float, amount_error = validate_amount(amount_str)
                if amount_error:
                    errors.append(f"Amount ('{amount_str}'): {amount_error}")

                pan = str(row.get('Pan', '')).strip().upper()
                is_valid_pan, pan_error = validate_pan(pan)
                if not is_valid_pan:
                    errors.append(f"PAN ('{pan}'): {pan_error}")

                address = str(row.get('Address', '')).strip()

                # If any validation errors occurred, log them and skip the row
                if errors:
                    log_messages.append(f"Skipped Row {row_num}: " + ", ".join(errors))
                    skipped_count += 1
                    continue
                
                # --- Proceed with valid data ---
                db_date = date_obj.strftime('%Y-%m-%d')
                pdf_date = date_obj.strftime('%d-%m-%Y')
                address = str(row.get('Address', '')).strip()
                user_email = st.session_state.get('user_email', 'UNKNOWN')
                
                serial_no = None
                if 'Serial No' in row and str(row['Serial No']).strip().isdigit():
                    serial_no = int(row['Serial No'])

                success, result_string = process_donor_and_get_receipt_no(
                    date=db_date,
                    name=name,
                    amount=amount_float,
                    address=address,
                    pan=pan,
                    serial_no=serial_no,
                    user_email=user_email,
                    entry_mode="excel"
                )
                if not success:
                    log_messages.append(f"Error Row {row_num} ({pan}): Supabase error - {result_string}")
                    error_count += 1
                    continue

                if result_string.startswith('exists:'):
                    existing_receipt_no = result_string.split(':', 1)[1]
                    log_messages.append(f"Row {row_num}: Record already exists with receipt number {existing_receipt_no}.")
                    skipped_count += 1
                elif 'ONL' in result_string:
                    receipt_no = result_string
                    receipt_data = ReceiptData(
                        receipt_no=receipt_no,
                        date=pdf_date,
                        name=name,
                        amount=amount_float,
                        address=address,
                        pan=pan
                    )
                    if not st.session_state.get('current_pdf_session_dir'):
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        session_dir_name = f"ht_donation_receipt_{timestamp}"
                        full_session_dir_path = os.path.join(BASE_PDF_OUTPUT_DIR, session_dir_name)
                        os.makedirs(full_session_dir_path, exist_ok=True)
                        st.session_state['current_pdf_session_dir'] = full_session_dir_path
                        st.info(f"PDFs for this session will be saved in: {full_session_dir_path}", icon="🗂️")
                    pdf_path = create_receipt_pdf(receipt_data, st.session_state['current_pdf_session_dir'])
                    if pdf_path:
                        if set_receipt_generated_flag(receipt_no):
                            log_messages.append(f"Success Row {row_num}: Generated {receipt_no}.pdf")
                            success_count += 1
                        else:
                            log_messages.append(f"Error Row {row_num}: Generated PDF for {receipt_no} but FAILED to update DB flag.")
                            error_count += 1
                    else:
                        log_messages.append(f"Error Row {row_num}: Failed to generate PDF, it has already generated {receipt_no}.")
                        error_count += 1
                else:
                    log_messages.append(f"Error Row {row_num} ({pan}): Unknown response from server - '{result_string}'")
                    error_count += 1

            st.success(f"Processing Complete! Success: {success_count}, Skipped: {skipped_count}, Errors: {error_count}")
            st.text_area("Processing Log", value="\n".join(log_messages), height=300)

            # --- Download as ZIP ---
            if success_count > 0:
                zip_bytes = create_zip_from_directory(st.session_state['current_pdf_session_dir'])
                if zip_bytes:
                    st.download_button(
                        label="Download All as ZIP",
                        data=zip_bytes,
                        file_name=f"{os.path.basename(st.session_state['current_pdf_session_dir'])}.zip",
                        mime="application/zip"
                    )
        else:
            st.warning("⚠️ Please choose a file before processing.")

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