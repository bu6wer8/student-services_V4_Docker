# File: app/utils/utils.py
"""
Utility functions to implement DRY (Don't Repeat Yourself) principles
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Order, User, Payment
from app.models.database import SessionLocal

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Database utility functions to avoid code repetition"""
    
    @staticmethod
    def get_db_session() -> Session:
        """Get database session with proper error handling"""
        return SessionLocal()
    
    @staticmethod
    def safe_db_operation(operation_func, *args, **kwargs):
        """Execute database operation with automatic session management"""
        db = DatabaseUtils.get_db_session()
        try:
            result = operation_func(db, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: str) -> Optional[User]:
        """Get user by telegram ID"""
        return db.query(User).filter(User.telegram_id == str(telegram_id)).first()
    
    @staticmethod
    def get_order_with_user(db: Session, order_id: int) -> Optional[Order]:
        """Get order with user relationship loaded"""
        from sqlalchemy.orm import joinedload
        return db.query(Order).options(joinedload(Order.user)).filter(Order.id == order_id).first()
    
    @staticmethod
    def get_user_orders(db: Session, user_id: int, limit: int = 10) -> List[Order]:
        """Get user's orders ordered by creation date"""
        return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(limit).all()

class OrderUtils:
    """Order-related utility functions"""
    
    @staticmethod
    def generate_order_number(user_id: int) -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"ORD-{timestamp}-{user_id}"
    
    @staticmethod
    def get_order_status_display(status: str, language: str = 'en') -> str:
        """Get localized order status display"""
        status_map = {
            'en': {
                'pending': 'Pending',
                'paid': 'Paid',
                'in_progress': 'In Progress',
                'delivered': 'Delivered',
                'completed': 'Completed',
                'archived': 'Archived'
            },
            'ar': {
                'pending': 'في الانتظار',
                'paid': 'مدفوع',
                'in_progress': 'قيد التنفيذ',
                'delivered': 'تم التسليم',
                'completed': 'مكتمل',
                'archived': 'مؤرشف'
            }
        }
        return status_map.get(language, status_map['en']).get(status, status)
    
    @staticmethod
    def get_payment_status_display(status: str, language: str = 'en') -> str:
        """Get localized payment status display"""
        status_map = {
            'en': {
                'waiting': 'Waiting',
                'confirmed': 'Confirmed',
                'failed': 'Failed'
            },
            'ar': {
                'waiting': 'في الانتظار',
                'confirmed': 'مؤكد',
                'failed': 'فشل'
            }
        }
        return status_map.get(language, status_map['en']).get(status, status)
    
    @staticmethod
    def calculate_order_urgency_days(deadline: datetime) -> int:
        """Calculate days until deadline"""
        now = datetime.now()
        delta = deadline - now
        return max(1, delta.days)
    
    @staticmethod
    def is_order_overdue(deadline: datetime) -> bool:
        """Check if order is overdue"""
        return datetime.now() > deadline
    
    @staticmethod
    def get_order_data_for_notification(order: Order) -> Dict[str, Any]:
        """Extract order data for notifications"""
        return {
            'order_number': order.order_number,
            'customer_email': order.user.email if order.user else None,
            'customer_telegram_id': order.user.telegram_id if order.user else None,
            'customer_language': order.user.language if order.user else 'en',
            'service_type': order.service_type,
            'total_price': order.total_price,
            'currency': order.currency,
            'status': order.status,
            'payment_status': order.payment_status
        }

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Basic phone validation"""
        import re
        # Remove spaces and special characters
        clean_phone = re.sub(r'[^\d+]', '', phone)
        # Check if it's a valid international format
        return len(clean_phone) >= 10 and len(clean_phone) <= 15
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize and truncate text input"""
        if not text:
            return ""
        # Remove potentially harmful characters
        import re
        sanitized = re.sub(r'[<>"\']', '', text.strip())
        return sanitized[:max_length]
    
    @staticmethod
    def validate_currency(currency: str) -> bool:
        """Validate currency code"""
        valid_currencies = ['USD', 'JOD', 'AED', 'SAR', 'EUR', 'GBP']
        return currency.upper() in valid_currencies
    
    @staticmethod
    def validate_order_status(status: str) -> bool:
        """Validate order status"""
        valid_statuses = ['pending', 'paid', 'in_progress', 'delivered', 'completed', 'archived']
        return status.lower() in valid_statuses

class FormattingUtils:
    """Text formatting utilities"""
    
    @staticmethod
    def format_currency(amount: float, currency: str) -> str:
        """Format currency amount"""
        currency_symbols = {
            'USD': '$',
            'JOD': 'JD',
            'AED': 'AED',
            'SAR': 'SAR',
            'EUR': '€',
            'GBP': '£'
        }
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{amount:.2f}"
    
    @staticmethod
    def format_datetime(dt: datetime, language: str = 'en') -> str:
        """Format datetime for display"""
        if language == 'ar':
            # Arabic date format
            return dt.strftime('%Y/%m/%d %H:%M')
        else:
            # English date format
            return dt.strftime('%B %d, %Y at %I:%M %p')
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text with suffix"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

class FileUtils:
    """File handling utilities"""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        import os
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def is_allowed_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
        """Check if file type is allowed"""
        if allowed_extensions is None:
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.zip', '.rar']
        
        extension = FileUtils.get_file_extension(filename)
        return extension in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def generate_safe_filename(original_filename: str, order_id: int) -> str:
        """Generate safe filename for storage"""
        import re
        import os
        
        # Remove unsafe characters
        safe_name = re.sub(r'[^\w\-_\.]', '_', original_filename)
        name, ext = os.path.splitext(safe_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{order_id}_{timestamp}_{name}{ext}"

class SecurityUtils:
    """Security-related utilities"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate secure random token"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class CacheUtils:
    """Caching utilities for performance optimization"""
    
    _cache = {}
    
    @staticmethod
    def get_cached(key: str, default=None):
        """Get value from cache"""
        return CacheUtils._cache.get(key, default)
    
    @staticmethod
    def set_cached(key: str, value, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        CacheUtils._cache[key] = {'value': value, 'expiry': expiry}
    
    @staticmethod
    def clear_expired():
        """Clear expired cache entries"""
        now = datetime.now()
        expired_keys = [k for k, v in CacheUtils._cache.items() if v['expiry'] < now]
        for key in expired_keys:
            del CacheUtils._cache[key]
    
    @staticmethod
    def clear_cache():
        """Clear all cache"""
        CacheUtils._cache.clear()

class ErrorUtils:
    """Error handling utilities"""
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Log error with context"""
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)
    
    @staticmethod
    def create_error_response(message: str, code: str = "GENERAL_ERROR") -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error': {
                'code': code,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Create standardized success response"""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if data is not None:
            response['data'] = data
        return response

# Decorator for common functionality
def with_db_session(func):
    """Decorator to automatically handle database sessions"""
    def wrapper(*args, **kwargs):
        db = DatabaseUtils.get_db_session()
        try:
            result = func(db, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            ErrorUtils.log_error(e, func.__name__)
            raise
        finally:
            db.close()
    return wrapper

def log_execution_time(func):
    """Decorator to log function execution time"""
    import time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper
