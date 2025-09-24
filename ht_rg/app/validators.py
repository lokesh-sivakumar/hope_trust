# app/validators.py
import re

def validate_amount(amount: str) -> tuple[float | None, str | None]:
    """
    Validates that the amount is a positive number.
    Returns tuple of (amount_float, error_message)
    """
    if not amount:
        return None, "Amount cannot be empty"

    try:
        # Convert to string and strip whitespace
        amount_str = str(amount).strip()

        # Attempt to convert to float directly
        amount_float = float(amount_str)

        # Check if the amount is positive
        if amount_float > 0:
            return amount_float, None
        else:
            return None, "Amount must be a positive number greater than zero"

    except (ValueError, TypeError):
        return None, "Invalid numeric format. Amount must be a valid number."

def validate_amount(amount: str) -> tuple[float | None, str | None]:
    """
    Validates that the amount is a positive number.
    Returns tuple of (amount_float, error_message)
    """
    if not amount:
        return None, "Amount cannot be empty"

    try:
        if isinstance(amount, (int, float)):
            amount = str(amount)

        # Only keep digits, one dot, and a leading minus sign if present
        cleaned = str(amount).strip()
        # Use regex to extract a valid float (including negative)
        match = re.match(r'^-?\d+(\.\d+)?$', cleaned)
        if not match:
            return None, "Invalid numeric format"

        amount_float = float(cleaned)
        return (amount_float, None) if amount_float > 0 else (None, "Must be greater than zero")

    except (ValueError, TypeError) as e:
        return None, f"Validation error: {str(e)}"
    