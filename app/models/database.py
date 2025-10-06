#!/usr/bin/env python3
"""
Student Services Platform - Database Configuration
Production-ready database setup with connection pooling and error handling
"""

import logging
import sys
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config import settings

# Configure logging
logger = logging.getLogger("database")

# Database configuration
DATABASE_URL = settings.database_url

# Create engine with connection pooling
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    # PostgreSQL/MySQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# -------------------------------------------------
# Database Connection Management
# -------------------------------------------------

def get_db():
    """
    Database dependency for FastAPI
    Provides database session with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """
    Initialize database and create all tables
    """
    try:
        # Import all models to ensure they are registered
        from app.models.models import Order, User, Payment, Feedback
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        logger.info(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'SQLite'}")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def check_database_connection():
    """
    Check if database connection is working
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

def get_database_info():
    """
    Get database information for health checks
    """
    try:
        db = SessionLocal()
        
        # Get database version and info
        if DATABASE_URL.startswith("postgresql"):
            result = db.execute("SELECT version()").fetchone()
            db_info = {"type": "PostgreSQL", "version": result[0] if result else "Unknown"}
        elif DATABASE_URL.startswith("mysql"):
            result = db.execute("SELECT VERSION()").fetchone()
            db_info = {"type": "MySQL", "version": result[0] if result else "Unknown"}
        else:
            result = db.execute("SELECT sqlite_version()").fetchone()
            db_info = {"type": "SQLite", "version": result[0] if result else "Unknown"}
        
        db.close()
        return db_info
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"type": "Unknown", "version": "Unknown", "error": str(e)}

# -------------------------------------------------
# Database Event Listeners
# -------------------------------------------------

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Set SQLite pragmas for better performance and integrity
    """
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    Log database connection checkout (for debugging)
    """
    if settings.debug:
        logger.debug("Database connection checked out")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """
    Log database connection checkin (for debugging)
    """
    if settings.debug:
        logger.debug("Database connection checked in")

# -------------------------------------------------
# Database Utilities
# -------------------------------------------------

class DatabaseManager:
    """
    Database management utilities
    """
    
    @staticmethod
    def backup_database(backup_path: str = None):
        """
        Create database backup (SQLite only)
        """
        if not DATABASE_URL.startswith("sqlite"):
            raise NotImplementedError("Backup only supported for SQLite")
        
        import shutil
        from datetime import datetime
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/database_backup_{timestamp}.db"
        
        # Extract database file path from URL
        db_file = DATABASE_URL.replace("sqlite:///", "")
        
        # Create backup directory
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Copy database file
        shutil.copy2(db_file, backup_path)
        
        logger.info(f"Database backup created: {backup_path}")
        return backup_path
    
    @staticmethod
    def restore_database(backup_path: str):
        """
        Restore database from backup (SQLite only)
        """
        if not DATABASE_URL.startswith("sqlite"):
            raise NotImplementedError("Restore only supported for SQLite")
        
        import shutil
        
        # Extract database file path from URL
        db_file = DATABASE_URL.replace("sqlite:///", "")
        
        # Restore database file
        shutil.copy2(backup_path, db_file)
        
        logger.info(f"Database restored from: {backup_path}")
    
    @staticmethod
    def get_table_stats():
        """
        Get statistics for all tables
        """
        try:
            db = SessionLocal()
            
            from app.models.models import Order, User, Payment, Feedback
            
            stats = {
                "orders": db.query(Order).count(),
                "users": db.query(User).count(),
                "payments": db.query(Payment).count(),
                "feedback": db.query(Feedback).count()
            }
            
            db.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {}

# Initialize database manager
db_manager = DatabaseManager()
