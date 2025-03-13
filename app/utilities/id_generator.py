"""
ID Generator module.

This module provides utility functions for generating unique IDs for various entities
in the system, with table name prefixes for better readability and debugging.
"""

import uuid
import datetime
import random
import string

def generate_id(table_name, length=10):
    """
    Generate a unique ID with table name prefix.
    
    Args:
        table_name (str): The name of the table (will be converted to uppercase)
        length (int, optional): Length of the random part. Defaults to 10.
        
    Returns:
        str: A unique ID in the format <TABLE_NAME>_<random_alphanumeric>
    """
    # Convert table name to uppercase for consistency
    prefix = table_name.upper()
    
    # Generate random alphanumeric string
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    return f"{prefix}_{random_part}"

def generate_uuid_id(table_name):
    """
    Generate a UUID-based ID with table name prefix.
    
    Args:
        table_name (str): The name of the table (will be converted to uppercase)
        
    Returns:
        str: A unique ID in the format <TABLE_NAME>_<uuid>
    """
    # Convert table name to uppercase for consistency
    prefix = table_name.upper()
    
    # Generate UUID
    unique_id = str(uuid.uuid4())
    
    return f"{prefix}_{unique_id}"

def generate_timestamp_id(table_name):
    """
    Generate a timestamp-based ID with table name prefix.
    
    Args:
        table_name (str): The name of the table (will be converted to uppercase)
        
    Returns:
        str: A unique ID in the format <TABLE_NAME>_<timestamp>_<random>
    """
    # Convert table name to uppercase for consistency
    prefix = table_name.upper()
    
    # Get current timestamp in a sortable format
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Add random suffix to avoid collisions
    random_suffix = ''.join(random.choices(string.digits, k=4))
    
    return f"{prefix}_{timestamp}_{random_suffix}"

def generate_candidate_id(year=None, sequence=None):
    """
    Generate a candidate ID with a specific format.
    
    Args:
        year (int, optional): Year to use in the ID. Defaults to current year.
        sequence (int, optional): Sequence number. If None, uses a random number.
        
    Returns:
        str: A candidate ID in the format C<YEAR><SEQUENCE>
    """
    # Use current year if not provided
    if year is None:
        year = datetime.datetime.now().year
    
    # Use random 6-digit number if sequence not provided
    if sequence is None:
        sequence = random.randint(100000, 999999)
    else:
        # Ensure sequence is 6 digits
        sequence = int(sequence) % 1000000
    
    return f"C{year}{sequence:06d}"

# Example usage:
# user_id = generate_id("user")  # USER_ABC123XYZ
# uuid_id = generate_uuid_id("user")  # USER_550e8400-e29b-41d4-a716-446655440000
# timestamp_id = generate_timestamp_id("transaction")  # TRANSACTION_20230615123045_7890
# candidate_id = generate_candidate_id()  # C2023456789 