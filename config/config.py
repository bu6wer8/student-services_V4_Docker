"""
Student Services Platform - Configuration
Production-ready configuration for Docker deployment
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Environment Configuration
    env: str = "production"
    debug: bool = False
    app_url: str = "http://localhost"
    
    # Database Configuration
    database_url: str = "postgresql://student_services:password@postgres:5432/student_services"
    redis_url: str = "redis://redis:6379"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    
    # Admin Authentication
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # Telegram Bot Configuration
    telegram_bot_token: str = ""
    telegram_admin_id: str = ""
    
    # Payment Configuration - Stripe
    stripe_public_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    
    # File Storage Configuration
    upload_dir: str = "./static/uploads"
    download_dir: str = "./static/downloads"
    max_file_size: int = 10485760  # 10MB
    
    # Bank Transfer Details
    bank_name: str = "Your Bank"
    bank_account_name: str = "Your Company"
    bank_account_number: str = ""
    bank_iban: str = ""
    bank_swift: str = ""
    
    # Pricing Configuration
    base_price_assignment: float = 20.0
    base_price_project: float = 50.0
    base_price_presentation: float = 30.0
    base_price_redesign: float = 25.0
    base_price_summary: float = 15.0
    base_price_express: float = 50.0
    
    # Urgency Multipliers
    urgency_multiplier_24h: float = 2.0
    urgency_multiplier_48h: float = 1.5
    urgency_multiplier_72h: float = 1.3
    
    # Academic Level Multipliers
    academic_multiplier_high_school: float = 1.0
    academic_multiplier_bachelor: float = 1.2
    academic_multiplier_masters: float = 1.5
    academic_multiplier_phd: float = 2.0
    
    # Currency Exchange Rates (to USD)
    rate_usd_to_jod: float = 0.71
    rate_usd_to_aed: float = 3.67
    rate_usd_to_sar: float = 3.75
    
    # Business Settings
    business_name: str = "Student Services Platform"
    support_email: str = "support@yourdomain.com"
    support_telegram: str = "@your_support"
    
    # Feature Flags
    enable_registration: bool = True
    enable_bank_transfer: bool = True
    enable_stripe: bool = True
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    
    # JWT Configuration
    access_token_expire_minutes: int = 30
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Cache Configuration
    cache_ttl: int = 3600
    cache_prefix: str = "student_services"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_payment_methods(self):
        """
        Get available payment methods based on configuration
        """
        methods = {}
        
        if self.enable_stripe and self.stripe_public_key and self.stripe_secret_key:
            methods["stripe"] = {
                "name": "Credit/Debit Card",
                "enabled": True,
                "public_key": self.stripe_public_key
            }
        
        if self.enable_bank_transfer:
            methods["bank_transfer"] = {
                "name": "Bank Transfer",
                "enabled": True,
                "details": {
                    "bank_name": self.bank_name,
                    "account_name": self.bank_account_name,
                    "account_number": self.bank_account_number,
                    "iban": self.bank_iban,
                    "swift": self.bank_swift
                }
            }
        
        return methods
    
    def get_database_config(self):
        """
        Get database configuration for connection
        """
        return {
            "url": self.database_url,
            "echo": self.debug,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600
        }
    
    def get_redis_config(self):
        """
        Get Redis configuration
        """
        return {
            "url": self.redis_url,
            "decode_responses": True,
            "health_check_interval": 30
        }
    
    def is_production(self) -> bool:
        """
        Check if running in production environment
        """
        return self.env.lower() == "production"
    
    def is_development(self) -> bool:
        """
        Check if running in development environment
        """
        return self.env.lower() == "development"

# Create global settings instance
settings = Settings()
