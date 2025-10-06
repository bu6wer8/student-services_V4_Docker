#!/usr/bin/env python3
"""
Student Services Platform - Simplified Authentication Service
Basic admin authentication with session management
"""

import hashlib
import secrets
import time
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Response
from passlib.context import CryptContext

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config import settings

# Configure logging
logger = logging.getLogger("auth")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """
    Simplified authentication service for admin panel
    """
    
    def __init__(self):
        self.sessions = {}  # In production, use Redis
        self.session_cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash password
        """
        return pwd_context.hash(password)
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        """
        Authenticate admin user with simple username/password check
        """
        # Check against configured admin credentials
        if username == settings.admin_username:
            # Simple password comparison
            return password == settings.admin_password
        
        return False
    
    def create_session(self, username: str, ip_address: str) -> str:
        """
        Create admin session
        """
        session_id = secrets.token_urlsafe(32)
        
        self.sessions[session_id] = {
            'username': username,
            'ip_address': ip_address,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=8)
        }
        
        logger.info(f"Created session {session_id[:8]}... for user {username}")
        return session_id
    
    def verify_session(self, session_id: str, ip_address: str = None) -> Optional[Dict[str, Any]]:
        """
        Verify admin session
        """
        if session_id not in self.sessions:
            return None
        
        session_data = self.sessions[session_id]
        
        # Check expiration
        if datetime.utcnow() > session_data['expires_at']:
            del self.sessions[session_id]
            return None
        
        # Update last activity
        session_data['last_activity'] = datetime.utcnow()
        
        return session_data
    
    def invalidate_session(self, session_id: str):
        """
        Invalidate admin session
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Invalidated session {session_id[:8]}...")
    
    def cleanup_expired_sessions(self):
        """
        Clean up expired sessions periodically
        """
        current_time = time.time()
        
        # Only cleanup every hour
        if current_time - self.last_cleanup < self.session_cleanup_interval:
            return
        
        current_datetime = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, data in self.sessions.items()
            if current_datetime > data['expires_at']
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        self.last_cleanup = current_time
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        """
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

# Global auth service instance
auth_service = AuthService()

# Dependency for protected routes
def get_current_admin(request: Request):
    """
    Dependency to get current authenticated admin
    """
    session_id = request.cookies.get("admin_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    ip_address = auth_service.get_client_ip(request)
    session_data = auth_service.verify_session(session_id, ip_address)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return session_data

def require_admin_auth(request: Request):
    """
    Decorator for admin-only routes
    """
    return get_current_admin(request)
