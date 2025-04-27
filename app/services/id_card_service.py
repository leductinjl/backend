"""
IdCard Service module.

This module provides services for extracting information from ID cards (CMND/CCCD)
using OCR and other image processing techniques.
"""

import logging
from typing import Optional, Dict, Any
from datetime import date
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

from app.services.qr_code_service import QRCodeService

logger = logging.getLogger(__name__)

class IdCardService:
    """
    Service for extracting information from ID cards.
    
    This service uses OCR and image processing to extract text and information
    from ID card images, including:
    - ID number
    - Full name
    - Date of birth
    - Gender
    - Address
    """
    
    def __init__(self):
        """Initialize the ID card service."""
        # Configure Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.qr_service = QRCodeService()
        
    async def extract_info(self, image_path: str) -> Dict[str, Any]:
        """
        Extract information from an ID card image.
        
        This method tries to extract information using both QR code and OCR.
        If QR code extraction fails, it falls back to OCR.
        
        Args:
            image_path: Path to the ID card image file
            
        Returns:
            dict: Extracted information including:
                - id_number: ID number
                - full_name: Full name
                - birth_date: Date of birth
                - gender: Gender
                - address: Address
                - issue_date: Issue date (from QR code)
                - expiry_date: Expiry date (from QR code)
        """
        try:
            # First try to extract from QR code
            try:
                qr_info = await self.qr_service.extract_info(image_path)
                if self._validate_qr_info(qr_info):
                    return qr_info
            except Exception as qr_error:
                logger.warning(f"QR code extraction failed: {qr_error}")
                
            # If QR code extraction fails, fall back to OCR
            return await self._extract_info_from_ocr(image_path)
            
        except Exception as e:
            logger.error(f"Error extracting info from ID card: {e}", exc_info=True)
            raise
            
    async def _extract_info_from_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        Extract information from ID card image using OCR.
        
        Args:
            image_path: Path to the ID card image file
            
        Returns:
            dict: Extracted information
        """
        try:
            # Read and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image at {image_path}")
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to preprocess the image
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Try different OCR configurations
            # Configuration 1: Default with Vietnamese language
            text1 = pytesseract.image_to_string(thresh, lang='vie')
            
            # Configuration 2: With specific PSM mode (6: Assume uniform block of text)
            text2 = pytesseract.image_to_string(thresh, lang='vie', config='--psm 6')
            
            # Configuration 3: With specific PSM mode (3: Fully automatic page segmentation)
            text3 = pytesseract.image_to_string(thresh, lang='vie', config='--psm 3')
            
            # Configuration 4: With specific PSM mode (4: Assume a single column of text)
            text4 = pytesseract.image_to_string(thresh, lang='vie', config='--psm 4')
            
            # Log all extracted texts for debugging
            logger.debug(f"OCR extracted text (default): {text1}")
            logger.debug(f"OCR extracted text (psm 6): {text2}")
            logger.debug(f"OCR extracted text (psm 3): {text3}")
            logger.debug(f"OCR extracted text (psm 4): {text4}")
            
            # Try to extract information from each text
            info1 = self._extract_info_from_text(text1)
            info2 = self._extract_info_from_text(text2)
            info3 = self._extract_info_from_text(text3)
            info4 = self._extract_info_from_text(text4)
            
            # Combine results, prioritizing the one with the most information
            combined_info = {}
            
            # Helper function to merge dictionaries, keeping non-empty values
            def merge_dicts(d1, d2):
                result = d1.copy()
                for key, value in d2.items():
                    if key not in result or not result[key]:
                        result[key] = value
                return result
            
            # Merge all results
            combined_info = merge_dicts(combined_info, info1)
            combined_info = merge_dicts(combined_info, info2)
            combined_info = merge_dicts(combined_info, info3)
            combined_info = merge_dicts(combined_info, info4)
            
            # If we still don't have a full name, try a more aggressive approach
            if 'full_name' not in combined_info or not combined_info['full_name'] or combined_info['full_name'] == "/ Full name:":
                # Try to extract name using a more aggressive approach
                # Look for text that appears to be a name (no numbers, reasonable length)
                name_candidates = []
                
                # Combine all texts
                all_texts = [text1, text2, text3, text4]
                
                for text in all_texts:
                    # Split by newlines and look for lines that might be names
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Skip empty lines, lines with numbers, or lines that are too short/long
                        if not line or any(c.isdigit() for c in line) or len(line) < 5 or len(line) > 50:
                            continue
                        # Skip lines that are likely headers or labels
                        if any(label in line.lower() for label in ['họ', 'tên', 'ngày', 'sinh', 'giới', 'tính', 'địa', 'chỉ']):
                            continue
                        name_candidates.append(line)
                
                # If we found any candidates, use the longest one as it's likely to be the full name
                if name_candidates:
                    combined_info['full_name'] = max(name_candidates, key=len)
            
            return combined_info
            
        except Exception as e:
            logger.error(f"Error extracting info from OCR: {e}", exc_info=True)
            raise
            
    def _extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract information from OCR text using regex patterns.
        
        Args:
            text: Text extracted from ID card image
            
        Returns:
            dict: Extracted information
        """
        info = {}
        
        # Log the extracted text for debugging
        logger.debug(f"OCR extracted text: {text}")
        
        # Extract ID number (12 digits)
        id_match = re.search(r'\b\d{12}\b', text)
        if id_match:
            info['id_number'] = id_match.group()
            
        # Extract full name - try multiple patterns
        # Pattern 1: "Full name:" followed by text
        name_match = re.search(r'Full name:?\s*([^\n]+)', text, re.IGNORECASE)
        if name_match:
            info['full_name'] = self._clean_name(name_match.group(1).strip())
        else:
            # Pattern 2: "Họ và tên:" followed by text
            name_match = re.search(r'Họ và tên:?\s*([^\n]+)', text, re.IGNORECASE)
            if name_match:
                info['full_name'] = self._clean_name(name_match.group(1).strip())
            else:
                # Pattern 3: "Họ tên:" followed by text
                name_match = re.search(r'Họ tên:?\s*([^\n]+)', text, re.IGNORECASE)
                if name_match:
                    info['full_name'] = self._clean_name(name_match.group(1).strip())
                else:
                    # Pattern 4: Look for text between "Họ và tên" and "Ngày sinh"
                    name_match = re.search(r'Họ và tên.*?([^\n]+).*?Ngày sinh', text, re.IGNORECASE | re.DOTALL)
                    if name_match:
                        info['full_name'] = self._clean_name(name_match.group(1).strip())
                    else:
                        # Pattern 5: Look for text between "Full name" and "Date of birth"
                        name_match = re.search(r'Full name.*?([^\n]+).*?Date of birth', text, re.IGNORECASE | re.DOTALL)
                        if name_match:
                            info['full_name'] = self._clean_name(name_match.group(1).strip())
                        else:
                            # Pattern 6: Look for text between "Full name" and any other field
                            name_match = re.search(r'Full name.*?([^\n]+)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
                            if name_match:
                                info['full_name'] = self._clean_name(name_match.group(1).strip())
            
        # Extract date of birth - try multiple patterns
        # Pattern 1: "Date of birth:" followed by date
        dob_match = re.search(r'Date of birth:?\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if dob_match:
            dob_str = dob_match.group(1)
            try:
                day, month, year = map(int, dob_str.split('/'))
                info['birth_date'] = date(year, month, day)
            except (ValueError, TypeError):
                pass
        else:
            # Pattern 2: "Ngày sinh:" followed by date
            dob_match = re.search(r'Ngày sinh:?\s*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if dob_match:
                dob_str = dob_match.group(1)
                try:
                    day, month, year = map(int, dob_str.split('/'))
                    info['birth_date'] = date(year, month, day)
                except (ValueError, TypeError):
                    pass
            else:
                # Pattern 3: Look for date format between "Ngày sinh" and "Giới tính"
                dob_match = re.search(r'Ngày sinh.*?(\d{2}/\d{2}/\d{4}).*?Giới tính', text, re.IGNORECASE | re.DOTALL)
                if dob_match:
                    dob_str = dob_match.group(1)
                    try:
                        day, month, year = map(int, dob_str.split('/'))
                        info['birth_date'] = date(year, month, day)
                    except (ValueError, TypeError):
                        pass
                else:
                    # Pattern 4: Look for date format between "Date of birth" and "Gender"
                    dob_match = re.search(r'Date of birth.*?(\d{2}/\d{2}/\d{4}).*?Gender', text, re.IGNORECASE | re.DOTALL)
                    if dob_match:
                        dob_str = dob_match.group(1)
                        try:
                            day, month, year = map(int, dob_str.split('/'))
                            info['birth_date'] = date(year, month, day)
                        except (ValueError, TypeError):
                            pass
                    else:
                        # Pattern 5: Look for any date format in the text
                        dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
                        if dob_match:
                            dob_str = dob_match.group(1)
                            try:
                                day, month, year = map(int, dob_str.split('/'))
                                # Check if the date is reasonable (not in the future)
                                if year < 2100 and year > 1900:
                                    info['birth_date'] = date(year, month, day)
                            except (ValueError, TypeError):
                                pass
            
        # Extract gender - try multiple patterns
        # Pattern 1: "Gender:" followed by gender
        gender_match = re.search(r'Gender:?\s*([^\n]+)', text, re.IGNORECASE)
        if gender_match:
            gender_str = gender_match.group(1).strip()
            if 'Male' in gender_str or 'Nam' in gender_str:
                info['gender'] = 'Nam'
            elif 'Female' in gender_str or 'Nữ' in gender_str:
                info['gender'] = 'Nữ'
        else:
            # Pattern 2: "Giới tính:" followed by gender
            gender_match = re.search(r'Giới tính:?\s*([^\n]+)', text, re.IGNORECASE)
            if gender_match:
                gender_str = gender_match.group(1).strip()
                if 'Nam' in gender_str:
                    info['gender'] = 'Nam'
                elif 'Nữ' in gender_str:
                    info['gender'] = 'Nữ'
            else:
                # Pattern 3: Look for gender between "Giới tính" and "Địa chỉ"
                gender_match = re.search(r'Giới tính.*?(Nam|Nữ).*?Địa chỉ', text, re.IGNORECASE | re.DOTALL)
                if gender_match:
                    gender_str = gender_match.group(1).strip()
                    if 'Nam' in gender_str:
                        info['gender'] = 'Nam'
                    elif 'Nữ' in gender_str:
                        info['gender'] = 'Nữ'
                else:
                    # Pattern 4: Look for gender between "Gender" and "Address"
                    gender_match = re.search(r'Gender.*?(Male|Female).*?Address', text, re.IGNORECASE | re.DOTALL)
                    if gender_match:
                        gender_str = gender_match.group(1).strip()
                        if 'Male' in gender_str:
                            info['gender'] = 'Nam'
                        elif 'Female' in gender_str:
                            info['gender'] = 'Nữ'
                    else:
                        # Pattern 5: Look for "Nam" or "Nữ" anywhere in the text
                        if 'Nam' in text:
                            info['gender'] = 'Nam'
                        elif 'Nữ' in text:
                            info['gender'] = 'Nữ'
                        elif 'Male' in text:
                            info['gender'] = 'Nam'
                        elif 'Female' in text:
                            info['gender'] = 'Nữ'
                
        # Extract nationality - try multiple patterns
        # Pattern 1: "Nationality:" followed by nationality
        nationality_match = re.search(r'Nationality:?\s*([^\n]+)', text, re.IGNORECASE)
        if nationality_match:
            info['nationality'] = self._clean_text(nationality_match.group(1).strip())
        else:
            # Pattern 2: "Quốc tịch:" followed by nationality
            nationality_match = re.search(r'Quốc tịch:?\s*([^\n]+)', text, re.IGNORECASE)
            if nationality_match:
                info['nationality'] = self._clean_text(nationality_match.group(1).strip())
            else:
                # Pattern 3: Look for nationality between "Quốc tịch" and "Dân tộc"
                nationality_match = re.search(r'Quốc tịch.*?([^\n]+).*?Dân tộc', text, re.IGNORECASE | re.DOTALL)
                if nationality_match:
                    info['nationality'] = self._clean_text(nationality_match.group(1).strip())
                else:
                    # Pattern 4: Look for nationality between "Nationality" and "Ethnicity"
                    nationality_match = re.search(r'Nationality.*?([^\n]+).*?Ethnicity', text, re.IGNORECASE | re.DOTALL)
                    if nationality_match:
                        info['nationality'] = self._clean_text(nationality_match.group(1).strip())
                    else:
                        # Default to "Việt Nam" if not found
                        info['nationality'] = "Việt Nam"
                
        # Extract place of origin - try multiple patterns
        # Pattern 1: "Place of origin:" followed by place
        origin_match = re.search(r'Place of origin:?\s*([^\n]+)', text, re.IGNORECASE)
        if origin_match:
            info['place_of_origin'] = self._clean_text(origin_match.group(1).strip())
        else:
            # Pattern 2: "Quê quán:" followed by place
            origin_match = re.search(r'Quê quán:?\s*([^\n]+)', text, re.IGNORECASE)
            if origin_match:
                info['place_of_origin'] = self._clean_text(origin_match.group(1).strip())
            else:
                # Pattern 3: Look for place of origin between "Quê quán" and "Nơi thường trú"
                origin_match = re.search(r'Quê quán.*?([^\n]+).*?Nơi thường trú', text, re.IGNORECASE | re.DOTALL)
                if origin_match:
                    info['place_of_origin'] = self._clean_text(origin_match.group(1).strip())
                else:
                    # Pattern 4: Look for place of origin between "Place of origin" and "Place of residence"
                    origin_match = re.search(r'Place of origin.*?([^\n]+).*?Place of residence', text, re.IGNORECASE | re.DOTALL)
                    if origin_match:
                        info['place_of_origin'] = self._clean_text(origin_match.group(1).strip())
                    else:
                        # Pattern 5: Look for "Place of ongin:" (common OCR error)
                        origin_match = re.search(r'Place of ongin:?\s*([^\n]+)', text, re.IGNORECASE)
                        if origin_match:
                            info['place_of_origin'] = self._clean_text(origin_match.group(1).strip())
                
        # Extract place of residence - try multiple patterns
        # Pattern 1: "Place of residence:" followed by place
        residence_match = re.search(r'Place of residence:?\s*([^\n]+)', text, re.IGNORECASE)
        if residence_match:
            info['place_of_residence'] = self._clean_text(residence_match.group(1).strip())
        else:
            # Pattern 2: "Nơi thường trú:" followed by place
            residence_match = re.search(r'Nơi thường trú:?\s*([^\n]+)', text, re.IGNORECASE)
            if residence_match:
                info['place_of_residence'] = self._clean_text(residence_match.group(1).strip())
            else:
                # Pattern 3: Look for place of residence between "Nơi thường trú" and end of text
                residence_match = re.search(r'Nơi thường trú.*?([^\n]+(?:\n[^\n]+)*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
                if residence_match:
                    info['place_of_residence'] = self._clean_text(residence_match.group(1).strip())
                else:
                    # Pattern 4: Look for place of residence between "Place of residence" and end of text
                    residence_match = re.search(r'Place of residence.*?([^\n]+(?:\n[^\n]+)*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
                    if residence_match:
                        info['place_of_residence'] = self._clean_text(residence_match.group(1).strip())
                    else:
                        # Pattern 5: Look for "Nơi thường trú" anywhere in the text
                        residence_match = re.search(r'Nơi thường trú.*?([^\n]+(?:\n[^\n]+)*?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
                        if residence_match:
                            info['place_of_residence'] = self._clean_text(residence_match.group(1).strip())
                
        # Extract address - try multiple patterns
        # Pattern 1: "Address:" followed by address
        address_match = re.search(r'Address:?\s*([^\n]+)', text, re.IGNORECASE)
        if address_match:
            info['address'] = self._clean_text(address_match.group(1).strip())
        else:
            # Pattern 2: "Địa chỉ:" followed by address
            address_match = re.search(r'Địa chỉ:?\s*([^\n]+)', text, re.IGNORECASE)
            if address_match:
                info['address'] = self._clean_text(address_match.group(1).strip())
            else:
                # Pattern 3: Look for text between "Địa chỉ" and end of text
                address_match = re.search(r'Địa chỉ.*?([^\n]+(?:\n[^\n]+)*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
                if address_match:
                    info['address'] = self._clean_text(address_match.group(1).strip())
                else:
                    # Pattern 4: Look for text between "Address" and end of text
                    address_match = re.search(r'Address.*?([^\n]+(?:\n[^\n]+)*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
                    if address_match:
                        info['address'] = self._clean_text(address_match.group(1).strip())
            
        return info
        
    def _clean_name(self, name: str) -> str:
        """
        Clean extracted name by removing unwanted characters.
        
        Args:
            name: The extracted name
            
        Returns:
            str: Cleaned name
        """
        # Remove common OCR artifacts and unwanted characters
        # Remove special characters like ¡, ¿, etc.
        name = re.sub(r'[¡¿]', '', name)
        
        # Remove other punctuation except spaces
        name = re.sub(r'[^\w\sÀ-ỹ]', '', name)
        
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
        
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing unwanted characters and OCR artifacts.
        
        Args:
            text: The extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove common OCR artifacts
        text = re.sub(r'[/\\]', '', text)  # Remove slashes
        text = re.sub(r'^[:\s]+', '', text)  # Remove leading colons and spaces
        text = re.sub(r'[^\w\sÀ-ỹ,.-]', '', text)  # Keep only letters, numbers, spaces, commas, periods, and hyphens
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _validate_qr_info(self, info: Dict[str, Any]) -> bool:
        """
        Validate information extracted from QR code.
        
        Args:
            info: Information dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['id_number', 'full_name', 'birth_date', 'gender', 'address']
        return all(field in info and info[field] for field in required_fields)
        
    def validate_id_number(self, id_number: str) -> bool:
        """
        Validate ID number format (12 digits).
        
        Args:
            id_number: ID number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return bool(re.match(r'^\d{12}$', id_number))
        
    def validate_birth_date(self, birth_date: date) -> bool:
        """
        Validate birth date (must be in the past).
        
        Args:
            birth_date: Date to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return birth_date < date.today()
        
    def validate_gender(self, gender: str) -> bool:
        """
        Validate gender value.
        
        Args:
            gender: Gender to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return gender in ['Nam', 'Nữ'] 