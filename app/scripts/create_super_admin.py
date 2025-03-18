"""
Super Admin Creation Script.

This script creates a super admin user and the required roles and permissions
when the application is first deployed. It only runs if no super admin exists.
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import sys
import logging
import passlib.hash
import traceback

# Add the application root to the Python path
sys.path.append(".")

from app.infrastructure.database.connection import get_db
from app.domain.models.user import User
from app.domain.models.role import Role
from app.domain.models.permission import Permission
from app.domain.models.role_permission import RolePermission
from app.services.id_service import generate_model_id
from sqlalchemy import select, and_

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("create_super_admin")

def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: The plain-text password to hash
        
    Returns:
        str: Hashed password
    """
    return passlib.hash.bcrypt.hash(password)

async def create_super_admin():
    """
    Create super admin user, roles and permissions if they don't exist.
    
    This function:
    1. Loads super admin credentials from environment variables
    2. Creates the super_admin role with required permissions
    3. Creates the super admin user if one doesn't exist
    """
    try:
        # Load environment variables
        logger.info("Loading environment variables...")
        load_dotenv()
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
        super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD")
        super_admin_name = os.getenv("SUPER_ADMIN_NAME", "System Super Administrator")
        
        if not super_admin_email or not super_admin_password:
            logger.error("ERROR: SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD must be set in .env file")
            logger.info(f"Current values - Email: {super_admin_email}, Password: {'Set' if super_admin_password else 'Not set'}")
            return
        
        logger.info(f"Attempting to create super admin with email: {super_admin_email}")
        
        # Connect to database
        logger.info("Connecting to database...")
        db = None
        db_gen = get_db()
        
        try:
            db = await anext(db_gen)
            logger.info("Successfully connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            logger.error(traceback.format_exc())
            return
        
        # Check if super admin already exists
        logger.info("Checking if super admin already exists...")
        result = await db.execute(
            select(User).where(User.role == "super_admin")
        )
        if result.scalar_one_or_none():
            logger.info("Super admin already exists")
            return
        
        # Create necessary roles if they don't exist
        # 1. Super Admin Role
        logger.info("Checking/creating super_admin role...")
        super_admin_role_result = await db.execute(
            select(Role).where(Role.name == "super_admin")
        )
        super_admin_role = super_admin_role_result.scalar_one_or_none()
        
        if not super_admin_role:
            logger.info("Creating super_admin role")
            super_admin_role = Role(
                role_id=generate_model_id("Role"),
                name="super_admin",
                description="Super Administrator with highest privileges"
            )
            db.add(super_admin_role)
            await db.flush()  # Flush to get the ID
            logger.info(f"Created super_admin role with ID: {super_admin_role.role_id}")
        
        # 2. Admin Role
        logger.info("Checking/creating admin role...")
        admin_role_result = await db.execute(
            select(Role).where(Role.name == "admin")
        )
        admin_role = admin_role_result.scalar_one_or_none()
        
        if not admin_role:
            logger.info("Creating admin role")
            admin_role = Role(
                role_id=generate_model_id("Role"),
                name="admin",
                description="Regular administrator with standard privileges"
            )
            db.add(admin_role)
            await db.flush()
            logger.info(f"Created admin role with ID: {admin_role.role_id}")
        
        # Create permissions
        logger.info("Setting up permissions...")
        permissions_data = [
            {
                "name": "admin:invite", 
                "description": "Can create invitation codes for new admins",
                "resource": "admin",
                "action": "invite"
            },
            {
                "name": "system:configure", 
                "description": "Can configure system settings",
                "resource": "system",
                "action": "configure" 
            },
            {
                "name": "admin:manage", 
                "description": "Can manage admin users",
                "resource": "admin",
                "action": "manage"
            },
            {
                "name": "candidates:manage", 
                "description": "Can manage candidates",
                "resource": "candidates",
                "action": "manage"
            },
            {
                "name": "exams:manage", 
                "description": "Can manage exams",
                "resource": "exams",
                "action": "manage"
            },
            {
                "name": "schools:manage", 
                "description": "Can manage schools",
                "resource": "schools",
                "action": "manage"
            }
        ]
        
        # Mapping of which permissions belong to which roles
        role_permissions = {
            "super_admin": ["admin:invite", "system:configure", "admin:manage", "candidates:manage", "exams:manage", "schools:manage"],
            "admin": ["candidates:manage", "exams:manage", "schools:manage"]
        }
        
        # Create all permissions and assign to roles
        created_permissions = {}
        
        for perm_data in permissions_data:
            # Check if permission exists
            perm_result = await db.execute(
                select(Permission).where(Permission.name == perm_data["name"])
            )
            perm = perm_result.scalar_one_or_none()
            
            if not perm:
                logger.info(f"Creating permission: {perm_data['name']}")
                perm = Permission(
                    permission_id=generate_model_id("Permission"),
                    name=perm_data["name"],
                    description=perm_data["description"],
                    resource=perm_data["resource"],
                    action=perm_data["action"]
                )
                db.add(perm)
                await db.flush()
                logger.info(f"Created permission {perm_data['name']} with ID: {perm.permission_id}")
            
            created_permissions[perm_data["name"]] = perm
        
        # Assign permissions to roles
        logger.info("Assigning permissions to roles...")
        for role_name, perm_names in role_permissions.items():
            role = super_admin_role if role_name == "super_admin" else admin_role
            
            for perm_name in perm_names:
                # Check if role-permission mapping exists
                rp_result = await db.execute(
                    select(RolePermission).where(
                        and_(
                            RolePermission.role_id == role.role_id,
                            RolePermission.permission_id == created_permissions[perm_name].permission_id
                        )
                    )
                )
                
                if not rp_result.scalar_one_or_none():
                    logger.info(f"Assigning permission {perm_name} to role {role_name}")
                    role_perm = RolePermission(
                        role_id=role.role_id,
                        permission_id=created_permissions[perm_name].permission_id
                    )
                    db.add(role_perm)
        
        # Create super admin user
        logger.info("Creating super admin user...")
        super_admin = User(
            user_id=generate_model_id("User"),
            email=super_admin_email,
            name=super_admin_name,
            password_hash=get_password_hash(super_admin_password),
            role="super_admin",
            role_id=super_admin_role.role_id,
            is_active=True,
            require_2fa=True,  # Require 2FA for super admin
            created_at=datetime.utcnow()
        )
        
        db.add(super_admin)
        
        # Commit changes
        logger.info("Committing changes to database...")
        await db.commit()
        logger.info(f"Super admin created successfully with email: {super_admin_email}")
    
    except Exception as e:
        logger.error(f"Error creating super admin: {str(e)}")
        logger.error(traceback.format_exc())
        if db and db.is_active:
            await db.rollback()
            logger.info("Database transaction rolled back")

if __name__ == "__main__":
    asyncio.run(create_super_admin()) 