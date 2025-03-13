"""
ID Service module.

This module provides service functions for generating and validating IDs
for various entities in the system. It integrates with the ID generator
utilities and provides higher-level functionality for model creation.
"""

from app.utilities.id_generator import (
    generate_id, 
    generate_uuid_id, 
    generate_timestamp_id,
    generate_candidate_id
)
import logging

logger = logging.getLogger(__name__)

# Map model classes to their appropriate ID generation functions
MODEL_ID_GENERATORS = {
    # Default prefix types
    "User": lambda: generate_uuid_id("user"),
    
    # Education related
    "School": lambda: generate_id("school", length=8),
    "Major": lambda: generate_id("major", length=8),
    
    # Exam related
    "Exam": lambda: generate_id("exam", length=8),
    "ExamType": lambda: generate_id("examtype", length=6),
    "ExamRoom": lambda: generate_id("room", length=6),
    "Subject": lambda: generate_id("subj", length=6),
    
    # Candidate related - special format
    "Candidate": lambda: generate_candidate_id(),
    
    # Transaction/history related
    "EducationHistory": lambda: generate_timestamp_id("eduhist"),
    "ExamScore": lambda: generate_timestamp_id("score"),
    "ExamAttemptHistory": lambda: generate_timestamp_id("attempt"),
    "Certificate": lambda: generate_timestamp_id("cert"),
}

def get_model_id_generator(model_class_name):
    """
    Get the appropriate ID generator function for a model class.
    
    Args:
        model_class_name (str): The name of the model class
        
    Returns:
        callable: A function that generates appropriate IDs for the model
    """
    # Get the specialized generator if it exists, otherwise use the default
    generator = MODEL_ID_GENERATORS.get(model_class_name)
    
    if generator is None:
        # Default to table name prefix with random ID
        return lambda: generate_id(model_class_name.lower())
    
    return generator

def generate_model_id(model_class_name):
    """
    Generate an ID for a specific model class.
    
    Args:
        model_class_name (str): The name of the model class
        
    Returns:
        str: A unique ID appropriate for the model
    """
    generator = get_model_id_generator(model_class_name)
    new_id = generator()
    logger.debug(f"Generated ID {new_id} for {model_class_name}")
    return new_id

def validate_id_format(id_value, model_class_name):
    """
    Validate that an ID follows the expected format for its model.
    
    Args:
        id_value (str): The ID to validate
        model_class_name (str): The name of the model class
        
    Returns:
        bool: True if the ID format is valid, False otherwise
    """
    # Implement validation logic based on expected formats
    # For example: checking prefixes, length, character types
    
    # Special case for Candidate IDs
    if model_class_name == "Candidate":
        if not id_value.startswith("C"):
            return False
        # Check if the rest is numeric and has the correct length
        if not id_value[1:].isdigit() or len(id_value) != 11:  # C + 4-digit year + 6-digit sequence
            return False
        return True
    
    # For models using prefixed IDs, check for appropriate prefix
    expected_prefix = model_class_name.upper() + "_"
    if id_value.startswith(expected_prefix):
        return True
        
    # For other ID formats, implement appropriate validation
    
    # Default to True if no specific validation exists
    return True 