#!/usr/bin/env python3
"""
Student Services Platform - Database Initialization Script
Initialize database tables and create admin user
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.database import init_database, get_db
from app.models.models import User
from config.config import settings
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def create_admin_user():
    """
    Create admin user if it doesn't exist
    """
    try:
        db = next(get_db())
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(
            User.telegram_id == settings.telegram_admin_id
        ).first()
        
        if not admin_user and settings.telegram_admin_id:
            # Create admin user
            admin_user = User(
                telegram_id=settings.telegram_admin_id,
                full_name="Admin User",
                username=settings.admin_username,
                is_admin=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Admin user created with Telegram ID: {settings.telegram_admin_id}")
        elif admin_user:
            logger.info("Admin user already exists")
        else:
            logger.warning("No Telegram Admin ID configured, skipping admin user creation")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise

def main():
    """
    Main initialization function
    """
    logger.info("Initializing Student Services Platform database...")
    
    try:
        # Initialize database tables
        logger.info("Creating database tables...")
        init_database()
        logger.info("Database tables created successfully")
        
        # Create admin user
        logger.info("Creating admin user...")
        create_admin_user()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()