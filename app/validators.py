# app/validators.py
import re
from typing import Tuple, Optional
from datetime import datetime

def validate_amount(amount: any) -> Tuple[Optional[float], Optional[str]]:
    """
    Validates that the amount is a positive number.
    Returns tuple of (amount_float, error_message)
    """
    if amount is None:
        return None, "Amount cannot be empty"
    
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        return None, "Amount must be a valid number."

    if amount_float <= 0:
        return None, "Amount must be a positive value."

    return amount_float, None

def validate_pan(pan: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a PAN number. It's valid if empty or matches the format.
    - 10 characters long
    - First 5 are letters
    - Next 4 are numbers
    - Last character is a letter
    Returns (is_valid, error_message)
    """
    pan_str = str(pan).strip()
    if not pan_str:
        return True, None  # PAN is optional, so empty is valid.

    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan_str.upper()):
        return False, "Invalid PAN format. Must be 5 letters, 4 numbers, 1 letter (e.g., ABCDE1234F)."
    
    return True, None

def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validates that a person's name is not empty.
    Returns (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    return True, None

def validate_date(date_str: str) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Validates a date string is in 'dd.mm.yy' format and not empty.
    Returns (datetime_obj, error_message)
    """
    if not date_str or not date_str.strip():
        return None, "Date cannot be empty"
    
    try:
        # Use %y for two-digit year
        date_obj = datetime.strptime(date_str.strip(), '%d.%m.%y')
        return date_obj, None
    except ValueError:
        return None, "Invalid date format. Please use dd.mm.yy."