"""
Input validation utilities
"""
import re
from email_validator import validate_email, EmailNotValidError


def validate_email_format(email):
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        tuple: (is_valid, normalized_email, error_message)
    """
    try:
        # Validate and normalize email
        emailinfo = validate_email(email, check_deliverability=False)
        return True, emailinfo.normalized, None
    except EmailNotValidError as e:
        return False, None, str(e)


def validate_password_strength(password, min_length=8):
    """
    Validate password strength
    
    Requirements:
    - Minimum length (default 8)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < min_length:
        return False, f'Password must be at least {min_length} characters long'
    
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit'
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)'
    
    return True, None


def validate_username(username):
    """
    Validate username format
    
    Requirements:
    - 3-30 characters
    - Alphanumeric and underscores only
    - Must start with a letter
    
    Args:
        username: Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(username) < 3:
        return False, 'Username must be at least 3 characters long'
    
    if len(username) > 30:
        return False, 'Username must be no more than 30 characters long'
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, 'Username must start with a letter and contain only letters, numbers, and underscores'
    
    return True, None


def sanitize_input(text, max_length=None):
    """
    Sanitize text input by stripping whitespace and optionally limiting length
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
        
    Returns:
        str: Sanitized text
    """
    if text is None:
        return None
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text if text else None
