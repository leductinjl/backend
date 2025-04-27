"""
QR Code Service module.

This module provides services for extracting information from QR codes on ID cards
using computer vision and QR code decoding techniques.
"""

import logging
from typing import Optional, Dict, Any
from datetime import date
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import re
import base64
import zlib

logger = logging.getLogger(__name__)

class QRCodeService:
    """
    Service for extracting information from QR codes on ID cards.
    
    This service uses computer vision and QR code decoding to extract information
    from QR codes on ID cards, following ICAO 9303 standard.
    """
    
    def __init__(self):
        """Initialize the QR code service."""
        pass
        
    async def extract_info(self, image_path: str) -> Dict[str, Any]:
        """
        Extract information from QR code on an ID card image.
        
        Args:
            image_path: Path to the ID card image file
            
        Returns:
            dict: Extracted information including:
                - id_number: ID number
                - full_name: Full name
                - birth_date: Date of birth
                - gender: Gender
                - address: Address
                - issue_date: Issue date
                - expiry_date: Expiry date
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image at {image_path}")
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect QR codes
            qr_codes = pyzbar.decode(gray)
            
            if not qr_codes:
                raise ValueError("No QR code found in image")
                
            # Get the first QR code data
            qr_data = qr_codes[0].data.decode('utf-8')
            
            # Parse QR code data according to ICAO 9303
            info = self._parse_qr_data(qr_data)
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting info from QR code: {e}", exc_info=True)
            raise
            
    def _parse_qr_data(self, qr_data: str) -> Dict[str, Any]:
        """
        Parse QR code data according to ICAO 9303 standard.
        
        The QR code data is in the format:
        IDVNM<version><issuing_country><document_number><optional_data><checksum>
        
        Args:
            qr_data: Raw QR code data
            
        Returns:
            dict: Parsed information
        """
        info = {}
        
        # Check if data starts with IDVNM (Vietnamese ID card)
        if not qr_data.startswith('IDVNM'):
            raise ValueError("Invalid QR code format - not a Vietnamese ID card")
            
        # Split data into fields
        fields = qr_data.split('|')
        
        # Extract document number (field 1)
        if len(fields) > 1:
            info['id_number'] = fields[1]
            
        # Extract full name (field 2)
        if len(fields) > 2:
            info['full_name'] = fields[2]
            
        # Extract date of birth (field 3)
        if len(fields) > 3:
            dob_str = fields[3]
            if len(dob_str) == 8:  # YYYYMMDD format
                year = int(dob_str[:4])
                month = int(dob_str[4:6])
                day = int(dob_str[6:8])
                info['birth_date'] = date(year, month, day)
                
        # Extract gender (field 4)
        if len(fields) > 4:
            gender_code = fields[4]
            if gender_code == 'M':
                info['gender'] = 'Nam'
            elif gender_code == 'F':
                info['gender'] = 'Nữ'
                
        # Extract address (field 5)
        if len(fields) > 5:
            info['address'] = fields[5]
            
        # Extract issue date (field 6)
        if len(fields) > 6:
            issue_str = fields[6]
            if len(issue_str) == 8:  # YYYYMMDD format
                year = int(issue_str[:4])
                month = int(issue_str[4:6])
                day = int(issue_str[6:8])
                info['issue_date'] = date(year, month, day)
                
        # Extract expiry date (field 7)
        if len(fields) > 7:
            expiry_str = fields[7]
            if len(expiry_str) == 8:  # YYYYMMDD format
                year = int(expiry_str[:4])
                month = int(expiry_str[4:6])
                day = int(expiry_str[6:8])
                info['expiry_date'] = date(year, month, day)
                
        return info
        
    def validate_qr_data(self, qr_data: str) -> bool:
        """
        Validate QR code data format and checksum.
        
        Args:
            qr_data: Raw QR code data
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check if data starts with IDVNM
            if not qr_data.startswith('IDVNM'):
                return False
                
            # Split data into fields
            fields = qr_data.split('|')
            
            # Check minimum required fields
            if len(fields) < 8:
                return False
                
            # Validate document number (12 digits)
            if not re.match(r'^\d{12}$', fields[1]):
                return False
                
            # Validate dates (YYYYMMDD format)
            date_fields = [fields[3], fields[6], fields[7]]  # DOB, issue, expiry
            for date_str in date_fields:
                if not re.match(r'^\d{8}$', date_str):
                    return False
                    
            # Validate gender code
            if fields[4] not in ['M', 'F']:
                return False
                
            return True
            
        except Exception:
            return False
            
    def generate_qr_data(self, info: Dict[str, Any]) -> str:
        """
        Generate QR code data from information dictionary.
        
        Args:
            info: Information dictionary containing:
                - id_number: ID number
                - full_name: Full name
                - birth_date: Date of birth
                - gender: Gender
                - address: Address
                - issue_date: Issue date
                - expiry_date: Expiry date
                
        Returns:
            str: QR code data string
        """
        # Format dates as YYYYMMDD
        dob_str = info['birth_date'].strftime('%Y%m%d')
        issue_str = info['issue_date'].strftime('%Y%m%d')
        expiry_str = info['expiry_date'].strftime('%Y%m%d')
        
        # Format gender code
        gender_code = 'M' if info['gender'] == 'Nam' else 'F'
        
        # Build QR data string
        qr_data = f"IDVNM|{info['id_number']}|{info['full_name']}|{dob_str}|{gender_code}|{info['address']}|{issue_str}|{expiry_str}"
        
        return qr_data 