"""
Two Factor Authentication Service.

This service handles the generation and verification of two-factor authentication credentials,
including TOTP (Time-based One-Time Password) and backup codes.
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import List, Tuple
import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.models.user import User
from app.domain.models.two_factor_backup import TwoFactorBackup
from app.infrastructure.database.connection import get_db
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class TwoFactorService:
    """
    Service for managing two-factor authentication.
    
    This service provides methods for generating TOTP secrets, QR codes,
    backup codes, and verifying 2FA codes during authentication.
    """
    
    def __init__(self, db: AsyncSession = Depends(get_db)):
        """Initialize the service with database session."""
        self.db = db
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key.
        
        Returns:
            str: A new base32-encoded secret key
        """
        return pyotp.random_base32()
    
    def get_totp_uri(self, email: str, secret: str) -> str:
        """
        Generate a TOTP URI for QR code generation.
        
        Args:
            email: The user's email address
            secret: The TOTP secret key
            
        Returns:
            str: The TOTP URI for QR code generation
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email, 
            issuer_name=settings.APP_NAME
        )
    
    def get_qr_code(self, email: str, secret: str) -> str:
        """
        Generate a QR code for setting up 2FA in authenticator apps.
        
        Args:
            email: The user's email address
            secret: The TOTP secret key
            
        Returns:
            str: Base64-encoded QR code image
        """
        uri = self.get_totp_uri(email, secret)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        buffered = io.BytesIO()
        img.save(buffered)
        return base64.b64encode(buffered.getvalue()).decode()
    
    def verify_totp(self, secret: str, code: str) -> bool:
        """
        Verify a TOTP code against the secret.
        
        Args:
            secret: The TOTP secret key
            code: The code to verify
            
        Returns:
            bool: True if the code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {str(e)}")
            return False
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for 2FA recovery.
        
        Returns:
            List[str]: A list of 10 backup codes
        """
        codes = []
        for _ in range(10):
            # Generate a secure, readable code (4 blocks of 4 characters)
            code = '-'.join(secrets.token_hex(2) for _ in range(4))
            codes.append(code)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage.
        
        Args:
            code: The backup code to hash
            
        Returns:
            str: The hashed backup code
        """
        # Remove any dashes for consistent hashing
        clean_code = code.replace('-', '')
        return hashlib.sha256(
            (clean_code + settings.SECRET_KEY).encode()
        ).hexdigest()
    
    async def store_backup_codes(self, user_id: str, codes: List[str]) -> bool:
        """
        Store hashed backup codes for a user.
        
        Args:
            user_id: The ID of the user
            codes: The list of backup codes to store
            
        Returns:
            bool: True if codes were stored successfully
        """
        try:
            # Delete any existing backup codes
            await self.db.execute(
                self.db.query(TwoFactorBackup)
                .filter(TwoFactorBackup.user_id == user_id)
                .delete()
            )
            
            # Store new backup codes
            for code in codes:
                backup = TwoFactorBackup(
                    backup_id=generate_model_id("TwoFactorBackup"),
                    user_id=user_id,
                    code_hash=self.hash_backup_code(code)
                )
                self.db.add(backup)
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing backup codes: {str(e)}")
            await self.db.rollback()
            return False
            
    async def verify_backup_code(self, user_id: str, code: str, ip_address: str = None) -> bool:
        """
        Verify a backup code and mark it as used if valid.
        
        Args:
            user_id: The ID of the user
            code: The backup code to verify
            ip_address: The IP address of the user (optional)
            
        Returns:
            bool: True if the code is valid, False otherwise
        """
        try:
            # Hash the provided code
            code_hash = self.hash_backup_code(code)
            
            # Find a matching backup code that hasn't been used
            result = await self.db.execute(
                self.db.query(TwoFactorBackup)
                .filter(
                    TwoFactorBackup.user_id == user_id,
                    TwoFactorBackup.code_hash == code_hash,
                    TwoFactorBackup.is_used == False
                )
            )
            backup = result.scalar_one_or_none()
            
            if not backup:
                return False
                
            # Mark the code as used
            from datetime import datetime
            backup.is_used = True
            backup.used_at = datetime.utcnow()
            backup.used_ip = ip_address
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error verifying backup code: {str(e)}")
            await self.db.rollback()
            return False
            
    async def setup_2fa(self, user_id: str) -> Tuple[str, str, List[str]]:
        """
        Set up 2FA for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Tuple: (secret, qr_code_base64, backup_codes)
        """
        try:
            # Get user
            result = await self.db.execute(
                self.db.query(User).filter(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
                
            # Generate secret
            secret = self.generate_secret()
            
            # Generate QR code
            qr_code = self.get_qr_code(user.email, secret)
            
            # Generate backup codes
            backup_codes = self.generate_backup_codes()
            
            # Store backup codes
            if not await self.store_backup_codes(user_id, backup_codes):
                raise ValueError("Failed to store backup codes")
                
            # Update user
            user.two_factor_secret = secret
            user.two_factor_enabled = False  # Will be enabled after verification
            
            await self.db.commit()
            
            return secret, qr_code, backup_codes
        except Exception as e:
            logger.error(f"Error setting up 2FA: {str(e)}")
            await self.db.rollback()
            raise 