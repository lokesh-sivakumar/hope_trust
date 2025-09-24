# app/update_ui.py
import streamlit as st
from app.supabase_client import get_receipt_by_number, update_receipt_details
from app.validators import validate_name, validate_amount, validate_pan, validate_date
from datetime import datetime

def update_page():
    st.header("Update Receipt Details")

    # Initialize session state for the record
    if 'current_record' not in st.session_state:
        st.session_state['current_record'] = None
    if 'update_errors' not in st.session_state:
        st.session_state['update_errors'] = []
    if 'update_warnings' not in st.session_state:
        st.session_state['update_warnings'] = []

    # 1. Search for a receipt
    with st.form(key="search_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            receipt_number_to_find = st.text_input("Enter Receipt Number to Update", key="update_receipt_no_find")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True) # For alignment
            find_button = st.form_submit_button("Find Receipt")

    if find_button and receipt_number_to_find:
        st.session_state['current_record'] = None  # Reset on new search
        st.session_state['update_errors'] = []
        st.session_state['update_warnings'] = []
        success, record = get_receipt_by_number(receipt_number_to_find)
        if success and record:
            st.session_state['current_record'] = record
            st.success(f"Found record for receipt number: {record['receipt_no']}")
        else:
            st.error("Receipt number not found.")

    # 2. Display record and allow updates if a record has been found
    if st.session_state['current_record']:
        record = st.session_state['current_record']
        st.subheader("Editing Record")

        with st.form("update_form"):
            # Display non-editable fields
            st.text(f"Receipt Number: {record['receipt_no']}")

            # Editable fields in the correct order
            db_date = record.get('date', '')
            display_date = ""
            if db_date:
                try:
                    # Parse from 'YYYY-MM-DD' and format to 'dd.mm.yy'
                    display_date = datetime.strptime(db_date, '%Y-%m-%d').strftime('%d.%m.%y')
                except (ValueError, TypeError):
                    display_date = db_date  # Fallback if format is wrong or not a string

            new_date = st.text_input("Date (dd.mm.yy)", value=display_date)
            name = st.text_input("Name", value=record.get('name', ''))
            amount = st.number_input("Amount", value=float(record.get('amount', 0.0)), format="%.2f")
            pan = st.text_input("PAN", value=record.get('pan', ''))
            address = st.text_area("Address", value=record.get('address', ''))

            col_submit, col_clear = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Update Record")
            with col_clear:
                clear_button = st.form_submit_button("Clear Form")

            if clear_button:
                st.session_state['current_record'] = None
                st.session_state['update_errors'] = []
                st.session_state['update_warnings'] = []
                st.rerun()

            if submitted:
                st.session_state['update_errors'] = []
                st.session_state['update_warnings'] = []

                # Warning if name is unchanged
                if name.upper() == record.get('name', '').upper():
                    st.session_state['update_warnings'].append("Name is the same as the existing record.")

                # Validation
                is_valid = True
                valid_name, name_error = validate_name(name)
                if not valid_name:
                    st.session_state['update_errors'].append(name_error)
                    is_valid = False

                valid_amount, amount_error = validate_amount(str(amount))
                if not valid_amount:
                    st.session_state['update_errors'].append(amount_error)
                    is_valid = False

                valid_pan, pan_error = validate_pan(pan)
                if not valid_pan:
                    st.session_state['update_errors'].append(pan_error)
                    is_valid = False

                valid_date_obj, date_error = validate_date(new_date)
                if not valid_date_obj:
                    st.session_state['update_errors'].append(date_error)
                    is_valid = False

                if is_valid:
                    db_formatted_date = valid_date_obj.strftime('%Y-%m-%d')
                    updated_data = {
                        "name": name.upper(),
                        "amount": amount,
                        "address": address.upper(),
                        "pan": pan.upper(),
                        "date": db_formatted_date
                    }
                    success, message = update_receipt_details(record['receipt_no'], updated_data)
                    if success:
                        st.success("Record updated successfully!")
                        st.session_state['current_record'] = None # Clear after update
                        st.session_state['update_warnings'] = [] # Clear warnings
                    else:
                        st.error(f"Update failed: {message}")
                else:
                    # Errors will be displayed below
                    pass

    # Display any validation warnings
    if st.session_state['update_warnings']:
        for warning in st.session_state['update_warnings']:
            st.warning(warning)

    # Display any validation errors
    if st.session_state['update_errors']:
        for error in st.session_state['update_errors']:
            st.error(error)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Mode Selection"):
            st.session_state['mode'] = None
            st.session_state['current_record'] = None # Clean up
            st.session_state['update_errors'] = [] # Clean up
            st.session_state['update_warnings'] = [] # Clean up
            st.rerun()
    with col2:
        if st.button("← Back to Main Dashboard"):
            st.session_state['mode'] = None
            st.session_state['active_section'] = None
            st.session_state['current_record'] = None # Clean up
            st.session_state['update_errors'] = [] # Clean up
            st.session_state['update_warnings'] = [] # Clean up
            st.rerun()