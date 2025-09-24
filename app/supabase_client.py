# app/supabase_client.py
from typing import Tuple, List, Dict, Any
from config import get_supabase_client, SUPABASE_URL, SUPABASE_KEY
import requests


def direct_api_test() -> list:
    """
    Bypasses the supabase-python library to make a direct HTTP request.
    Returns all rows from the Hope_Trust table.
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/Hope_Trust?select=*"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error during direct API test: {e}")
        if 'response' in locals():
            print("Raw response text:", response.text)
        return []

from typing import Optional

def supabase_client():
    # Get a client instance
    return get_supabase_client()

# Function to process a donor and get a receipt number
def process_donor_and_get_receipt_no(date, name, amount, pan, address, user_email, entry_mode, serial_no=None):
    client = supabase_client()
    try:
        # Check for existing record
        rpc_args = {
            "p_name": name.upper(),
            "p_address": address.upper(),
            "p_pan": pan.upper(),
            "p_amount": float(amount),
            "p_date": date,
            "p_serial_no": serial_no,
            "p_user_email": user_email,
            "p_entry_mode": entry_mode
        }
        response = client.rpc("process_and_generate_receipt", rpc_args).execute()
        return True, response.data
    except Exception as e:
        return False, f"Supabase RPC error: {e}"

# Function to update an existing donation record
def update_donation_record(receipt_no, date, name, amount, pan, address):
    client = supabase_client()
    try:
        # Call the stored procedure to update the record
        result = client.rpc('update_donation_record', {
            'p_receipt_no': receipt_no,
            'p_date': date,
            'p_name': name,
            'p_amount': amount,
            'p_address': address,
            'p_pan': pan
        }).execute()
        return True, result
    except Exception as e:
        return False, str(e)

# Function to set the receipt generated flag
def set_receipt_generated_flag(receipt_no: str) -> bool:
    """
    Updates the 'report' flag to TRUE for a specific receipt number via RPC.
    Returns True on success, False on failure.
    """
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Database client not initialized (in set_receipt_generated_flag).")
        return False
    try:
        trimmed_receipt_no = receipt_no.strip()
        response = supabase.rpc("mark_report_true", {
            "p_receipt_no": trimmed_receipt_no
        }).execute()
        actual_response = response.data[0] if isinstance(response.data, list) and response.data else response.data
        if actual_response == 'success':
            print(f"✅ Report flag updated for {trimmed_receipt_no} via RPC.")
            return True
        else:
            print(f"❌ Report flag update failed via RPC for {trimmed_receipt_no}. Actual response: {actual_response}")
            return False
    except Exception as e:
        print(f"❌ Report flag update failed for {receipt_no} (RPC error): {e}")
        return False

def fetch_missing_receipts() -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Fetches all records from Hope_Trust where 'report' is false.
    Uses a direct HTTP request to bypass a suspected library bug.
    Returns a tuple: (success_boolean, list_of_records).
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/Hope_Trust?select=*&report=is.false"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Found {len(data)} missing receipts (via direct API).")
        return True, data
    except Exception as e:
        print(f"❌ Failed to fetch missing receipts (via direct API): {e}")
        if 'response' in locals():
            print("Raw response text:", response.text)
        return False, []

def get_receipt_by_number(receipt_no: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Fetches a single record from Hope_Trust by its receipt number.
    Returns a tuple: (success_boolean, record_dictionary_or_none).
    """
    supabase = get_supabase_client()
    if not supabase:
        return False, None
    try:
        response = supabase.table("Hope_Trust").select("*").eq("receipt_no", receipt_no).execute()
        if response.data:
            return True, response.data[0]
        else:
            return True, None
    except Exception as e:
        print(f"Error fetching receipt {receipt_no}: {e}")
        return False, None

def update_receipt_details(receipt_no: str, updated_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Updates a record in the Hope_Trust table.
    Returns a tuple: (success_boolean, message_string).
    """
    supabase = get_supabase_client()
    if not supabase:
        return False, "Database client not initialized."
    try:
        response = supabase.table("Hope_Trust").update(updated_data).eq("receipt_no", receipt_no).execute()
        if len(response.data) > 0:
            return True, "Record updated successfully."
        else:
            return False, "Failed to update record or record not found."
    except Exception as e:
        return False, f"Supabase update error: {e}"