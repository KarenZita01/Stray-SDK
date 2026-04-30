"""Input validation utilities."""
import re
from decimal import Decimal, InvalidOperation
from typing import Union

def is_valid_stellar_address(address: str) -> bool:
    """
    Validate Stellar public key format.
    
    Args:
        address: Public key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False
    
    # Stellar public keys start with 'G' and are 56 characters long
    pattern = r'^G[A-Z2-7]{55}$'
    return bool(re.match(pattern, address))

def is_valid_amount(amount: Union[float, str, Decimal]) -> bool:
    """
    Validate payment amount.
    
    Args:
        amount: Amount to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Convert to Decimal for precise validation
        decimal_amount = Decimal(str(amount))
        return decimal_amount > 0 and decimal_amount <= Decimal('1000000')  # Max 1M XLM for safety
    except (InvalidOperation, ValueError, TypeError):
        return False

def is_valid_stellar_secret(secret: str) -> bool:
    """
    Validate Stellar secret key format.
    
    Args:
        secret: Secret key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not secret:
        return False
    
    # Stellar secret keys start with 'S' and are 56 characters long
    pattern = r'^S[A-Z2-7]{55}$'
    return bool(re.match(pattern, secret))

def validate_amount_precision(amount: Union[float, str, Decimal]) -> bool:
    """
    Validate that amount has appropriate decimal places for Stellar.
    
    Args:
        amount: Amount to validate
        
    Returns:
        True if precision is valid, False otherwise
    """
    try:
        decimal_amount = Decimal(str(amount))
        # Stellar supports up to 7 decimal places
        return decimal_amount.as_tuple().exponent >= -7
    except (InvalidOperation, ValueError, TypeError):
        return False
