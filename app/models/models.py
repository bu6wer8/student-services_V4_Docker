#!/usr/bin/env python3
"""
Student Services Platform - Database Models
Enhanced SQLAlchemy models with validation and relationships
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.database import Base

# -------------------------------------------------
# User Model
# -------------------------------------------------

class User(Base):
    """
    User model for customers and admins
    """
    __tablename__ = "users"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, index=True, nullable=False)
    telegram_username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    
    # Contact information
    student_id = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Preferences
    language = Column(String(5), default="en", nullable=False)
    country = Column(String(3), default="OTHER", nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    registration_ip = Column(String(45), nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_telegram', 'telegram_id'),
        Index('idx_user_email', 'email'),
        Index('idx_user_active', 'is_active'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code"""
        valid_currencies = ['USD', 'JOD', 'AED', 'SAR', 'EUR', 'GBP']
        if currency not in valid_currencies:
            raise ValueError(f"Invalid currency. Must be one of: {valid_currencies}")
        return currency
    
    @hybrid_property
    def display_name(self):
        """Get display name for user"""
        return self.full_name or self.telegram_username or f"User {self.id}"
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name={self.full_name})>"

# -------------------------------------------------
# Order Model
# -------------------------------------------------

class Order(Base):
    """
    Order model for service requests
    """
    __tablename__ = "orders"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Service details
    service_type = Column(String(50), nullable=False)
    subject = Column(String(200), nullable=False)
    requirements = Column(Text, nullable=False)
    special_notes = Column(Text, nullable=True)
    
    # Academic details
    academic_level = Column(String(20), nullable=False)
    pages_count = Column(Integer, default=1)
    word_count = Column(Integer, nullable=True)
    citation_style = Column(String(20), default="APA")
    
    # Timing
    deadline = Column(DateTime, nullable=False)
    urgency_hours = Column(Integer, nullable=True)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    urgency_multiplier = Column(Float, default=1.0)
    academic_multiplier = Column(Float, default=1.0)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment
    payment_method = Column(String(20), nullable=True)  # stripe, bank_transfer
    payment_status = Column(String(20), default="pending")  # pending, paid, failed, refunded
    stripe_session_id = Column(String(200), nullable=True)
    stripe_payment_intent_id = Column(String(200), nullable=True)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, confirmed, in_progress, delivered, completed, cancelled
    admin_notes = Column(Text, nullable=True)
    
    # Files
    requirement_files = Column(JSON, nullable=True)  # List of uploaded requirement files
    delivered_files = Column(JSON, nullable=True)    # List of delivered work files
    work_file_path = Column(String(500), nullable=True)  # Main delivered file
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="order", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_number', 'order_number'),
        Index('idx_order_user', 'user_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_payment_status', 'payment_status'),
        Index('idx_order_created', 'created_at'),
        Index('idx_order_deadline', 'deadline'),
    )
    
    @validates('service_type')
    def validate_service_type(self, key, service_type):
        """Validate service type"""
        valid_types = ['assignment', 'project', 'presentation', 'redesign', 'summary', 'express']
        if service_type not in valid_types:
            raise ValueError(f"Invalid service type. Must be one of: {valid_types}")
        return service_type
    
    @validates('academic_level')
    def validate_academic_level(self, key, academic_level):
        """Validate academic level"""
        valid_levels = ['high_school', 'bachelor', 'masters', 'phd']
        if academic_level not in valid_levels:
            raise ValueError(f"Invalid academic level. Must be one of: {valid_levels}")
        return academic_level
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate order status"""
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'delivered', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return status
    
    @validates('payment_status')
    def validate_payment_status(self, key, payment_status):
        """Validate payment status"""
        valid_statuses = ['pending', 'paid', 'failed', 'refunded']
        if payment_status not in valid_statuses:
            raise ValueError(f"Invalid payment status. Must be one of: {valid_statuses}")
        return payment_status
    
    @hybrid_property
    def is_overdue(self):
        """Check if order is overdue"""
        return self.deadline < datetime.utcnow() and self.status not in ['completed', 'cancelled']
    
    @hybrid_property
    def time_remaining(self):
        """Get time remaining until deadline"""
        if self.status in ['completed', 'cancelled']:
            return None
        return self.deadline - datetime.utcnow()
    
    @hybrid_property
    def is_paid(self):
        """Check if order is paid"""
        return self.payment_status == 'paid'
    
    def __repr__(self):
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status})>"

# -------------------------------------------------
# Payment Model
# -------------------------------------------------

class Payment(Base):
    """
    Payment model for tracking transactions
    """
    __tablename__ = "payments"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Payment details
    payment_id = Column(String(200), unique=True, nullable=False)  # Stripe payment ID or bank transaction ID
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    method = Column(String(20), nullable=False)  # stripe, bank_transfer
    
    # Status and metadata
    status = Column(String(20), default="pending")  # pending, succeeded, failed, cancelled, refunded
    failure_reason = Column(String(500), nullable=True)
    
    # Stripe specific
    stripe_session_id = Column(String(200), nullable=True)
    stripe_payment_intent_id = Column(String(200), nullable=True)
    receipt_url = Column(String(500), nullable=True)
    
    # Bank transfer specific
    bank_receipt_path = Column(String(500), nullable=True)
    bank_reference = Column(String(100), nullable=True)
    bank_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    succeeded_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_id', 'payment_id'),
        Index('idx_payment_order', 'order_id'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_method', 'method'),
        Index('idx_payment_created', 'created_at'),
    )
    
    @validates('method')
    def validate_method(self, key, method):
        """Validate payment method"""
        valid_methods = ['stripe', 'bank_transfer']
        if method not in valid_methods:
            raise ValueError(f"Invalid payment method. Must be one of: {valid_methods}")
        return method
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate payment status"""
        valid_statuses = ['pending', 'succeeded', 'failed', 'cancelled', 'refunded']
        if status not in valid_statuses:
            raise ValueError(f"Invalid payment status. Must be one of: {valid_statuses}")
        return status
    
    @hybrid_property
    def is_successful(self):
        """Check if payment is successful"""
        return self.status == 'succeeded'
    
    def __repr__(self):
        return f"<Payment(id={self.id}, payment_id={self.payment_id}, status={self.status})>"

# -------------------------------------------------
# Feedback Model
# -------------------------------------------------

class Feedback(Base):
    """
    Feedback model for order reviews
    """
    __tablename__ = "feedbacks"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Feedback details
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    
    # Categories (optional detailed feedback)
    quality_rating = Column(Integer, nullable=True)      # 1-5
    timeliness_rating = Column(Integer, nullable=True)   # 1-5
    communication_rating = Column(Integer, nullable=True) # 1-5
    
    # Metadata
    is_public = Column(Boolean, default=True)  # Whether to show publicly
    admin_response = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="feedback")
    
    # Indexes
    __table_args__ = (
        Index('idx_feedback_order', 'order_id'),
        Index('idx_feedback_rating', 'rating'),
        Index('idx_feedback_public', 'is_public'),
        Index('idx_feedback_created', 'created_at'),
    )
    
    @validates('rating')
    def validate_rating(self, key, rating):
        """Validate rating value"""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating
    
    @validates('quality_rating', 'timeliness_rating', 'communication_rating')
    def validate_sub_rating(self, key, rating):
        """Validate sub-rating values"""
        if rating is not None and not 1 <= rating <= 5:
            raise ValueError(f"{key} must be between 1 and 5")
        return rating
    
    @hybrid_property
    def average_rating(self):
        """Calculate average of all ratings"""
        ratings = [r for r in [self.rating, self.quality_rating, self.timeliness_rating, self.communication_rating] if r is not None]
        return sum(ratings) / len(ratings) if ratings else self.rating
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, order_id={self.order_id}, rating={self.rating})>"

# -------------------------------------------------
# Admin Log Model (for audit trail)
# -------------------------------------------------

class AdminLog(Base):
    """
    Admin log model for tracking admin actions
    """
    __tablename__ = "admin_logs"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Action details
    action = Column(String(50), nullable=False)  # create, update, delete, view
    resource_type = Column(String(50), nullable=False)  # order, user, payment, etc.
    resource_id = Column(Integer, nullable=True)
    
    # Details
    description = Column(Text, nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_admin_log_user', 'admin_user_id'),
        Index('idx_admin_log_action', 'action'),
        Index('idx_admin_log_resource', 'resource_type', 'resource_id'),
        Index('idx_admin_log_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AdminLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
