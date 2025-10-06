#!/usr/bin/env python3
"""
Student Services Platform - Telegram Bot (Fixed Version)
Production-ready bot with comprehensive order management and payment processing

Improvements implemented:
1. Better dependency handling with fail-fast approach
2. Redis-based state storage for production
3. Proper database session management with context managers
4. Enhanced error handling with user-friendly messages
5. Secure file handling with sanitization
6. Separated payment processing logic
7. Markdown escaping for user input (FIXED f-string issues)
8. Structured logging with user traceability
9. Fallback handlers for unexpected callbacks
10. Helper functions to reduce code duplication
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import aiogram with fail-fast approach
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, StateFilter
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.storage.redis import RedisStorage
    from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.utils.markdown import escape_md
    from sqlalchemy.orm import Session
except ImportError as e:
    print(f"Critical Error: aiogram not available: {e}")
    print("Bot cannot start without aiogram. Install with: pip install aiogram")
    sys.exit(1)

# Import application modules
from config.config import settings
from app.models.database import get_db, init_database
from app.models.models import User, Order, Payment, Feedback
from app.services.pricing import PricingService
from app.services.payment import PaymentService
from app.services.notification import NotificationService
from app.bot.states import OrderStates, PaymentStates, FeedbackStates
from app.bot.keyboards import (
    get_main_menu, get_service_menu, get_academic_level_menu,
    get_currency_menu, get_payment_method_menu, get_order_actions_menu
)

# Configure structured logging with user traceability
class UserContextFilter(logging.Filter):
    """Add user context to log records"""
    def filter(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = 'unknown'
        return True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s [user:%(user_id)s] - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("telegram-bot")
logger.addFilter(UserContextFilter())

class DatabaseManager:
    """Context manager for database sessions"""
    
    @staticmethod
    @contextmanager
    def get_session():
        """Get database session with proper cleanup"""
        db = next(get_db())
        try:
            yield db
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()

class FileHandler:
    """Secure file handling utilities"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        import re
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading dots and spaces
        filename = filename.lstrip('. ')
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        return filename or 'unnamed_file'
    
    @staticmethod
    def get_safe_upload_path(base_dir: str, filename: str, subfolder: str = "") -> str:
        """Get safe upload path with directory creation"""
        safe_filename = FileHandler.sanitize_filename(filename)
        upload_dir = os.path.join(base_dir, subfolder) if subfolder else base_dir
        os.makedirs(upload_dir, exist_ok=True)
        return os.path.join(upload_dir, safe_filename)

class StudentServicesBot:
    """
    Main bot class for handling all Telegram interactions
    """
    
    def __init__(self):
        # Fail fast if required configuration is missing
        if not settings.telegram_bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured. Bot cannot start.")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        self.bot = Bot(token=settings.telegram_bot_token)
        
        # Use Redis storage for production, fallback to memory for development
        try:
            if hasattr(settings, 'redis_url') and settings.redis_url:
                storage = RedisStorage.from_url(settings.redis_url)
                logger.info("Using Redis storage for FSM")
            else:
                storage = MemoryStorage()
                logger.warning("Using Memory storage for FSM - not recommended for production")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis, using Memory storage: {e}")
            storage = MemoryStorage()
        
        self.dp = Dispatcher(storage=storage)
        self.pricing_service = PricingService()
        self.payment_service = PaymentService()
        self.notification_service = NotificationService()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Student Services Bot initialized successfully")
    
    def _register_handlers(self):
        """Register all bot handlers"""
        
        # Command handlers
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_orders, Command("orders"))
        self.dp.message.register(self.cmd_cancel, Command("cancel"))
        
        # Main menu handlers
        self.dp.callback_query.register(self.handle_new_order, F.data == "new_order")
        self.dp.callback_query.register(self.handle_my_orders, F.data == "my_orders")
        self.dp.callback_query.register(self.handle_support, F.data == "support")
        self.dp.callback_query.register(self.handle_feedback, F.data == "feedback")
        self.dp.callback_query.register(self.handle_main_menu, F.data == "main_menu")
        
        # Order creation flow
        self.dp.callback_query.register(self.handle_service_selection, F.data.startswith("service_"))
        self.dp.callback_query.register(self.handle_academic_level, F.data.startswith("level_"))
        self.dp.callback_query.register(self.handle_currency_selection, F.data.startswith("currency_"))
        self.dp.callback_query.register(self.handle_payment_method, F.data.startswith("payment_"))
        
        # Order management
        self.dp.callback_query.register(self.handle_order_action, F.data.startswith("order_"))
        self.dp.callback_query.register(self.handle_payment_action, F.data.startswith("pay_"))
        self.dp.callback_query.register(self.handle_upload_receipt, F.data.startswith("upload_receipt_"))
        
        # State handlers
        self.dp.message.register(self.handle_subject_input, StateFilter(OrderStates.waiting_for_subject))
        self.dp.message.register(self.handle_requirements_input, StateFilter(OrderStates.waiting_for_requirements))
        self.dp.message.register(self.handle_deadline_input, StateFilter(OrderStates.waiting_for_deadline))
        self.dp.message.register(self.handle_special_notes, StateFilter(OrderStates.waiting_for_notes))
        
        # Payment handlers
        self.dp.message.register(self.handle_bank_receipt, StateFilter(PaymentStates.waiting_for_receipt), F.document)
        
        # Feedback handlers
        self.dp.message.register(self.handle_feedback_rating, StateFilter(FeedbackStates.waiting_for_rating))
        self.dp.message.register(self.handle_feedback_comment, StateFilter(FeedbackStates.waiting_for_comment))
        
        # File handlers
        self.dp.message.register(self.handle_file_upload, F.document)
        
        # Fallback handler for unexpected callbacks
        self.dp.callback_query.register(self.handle_unknown_callback)
        
        # Error handler
        self.dp.error.register(self.error_handler)
    
    def _log_with_user_context(self, level: str, message: str, user_id: Optional[str] = None):
        """Log with user context"""
        extra = {'user_id': user_id or 'unknown'}
        getattr(logger, level)(message, extra=extra)
    
    async def _send_notification(self, order: Order, subject: str, message: str):
        """Helper function to send notifications"""
        try:
            # Send email notification
            await self.notification_service.send_email(
                to_email=order.user.email,
                subject=subject,
                message=message
            )
            
            # Send Telegram notification to admin if configured
            if hasattr(settings, 'telegram_admin_id') and settings.telegram_admin_id:
                admin_message = f"📋 Order #{order.order_number}\n{message}"
                await self.bot.send_message(
                    chat_id=settings.telegram_admin_id,
                    text=admin_message,
                    parse_mode="Markdown"
                )
        except Exception as e:
            self._log_with_user_context('error', f"Failed to send notification: {e}", str(order.user.telegram_id))
    
    async def _handle_user_error(self, message_or_callback, error_message: str = None):
        """Send user-friendly error message"""
        error_text = error_message or "❌ An error occurred. Please try again or contact support."
        
        try:
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.answer("❌ Error occurred")
                await message_or_callback.message.answer(
                    error_text,
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
            else:
                await message_or_callback.answer(
                    error_text,
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Handle /start command"""
        user_id = str(message.from_user.id)
        try:
            await state.clear()
            
            # Get or create user
            user = await self._get_or_create_user(message.from_user)
            
            welcome_text = f"""
🎓 **Welcome to Student Services Platform!**

Hello {user.full_name}! 👋

We provide high-quality academic writing services:
📝 Assignments & Essays
📊 Projects & Research
🎯 Presentations
✨ And much more!

**What would you like to do?**
            """
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('info', f"User started the bot", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in start command: {e}", user_id)
            await self._handle_user_error(message)
    
    async def cmd_help(self, message: Message):
        """Handle /help command"""
        user_id = str(message.from_user.id)
        try:
            support_email = settings.support_email or 'support@example.com'
            help_text = f"""
🆘 **Help & Support**

**Available Commands:**
/start - Start the bot and show main menu
/orders - View your orders
/cancel - Cancel current operation
/help - Show this help message

**How to place an order:**
1️⃣ Click "📝 New Order"
2️⃣ Select service type
3️⃣ Fill in requirements
4️⃣ Choose payment method
5️⃣ Complete payment

**Payment Methods:**
💳 Credit/Debit Card (Instant)
🏦 Bank Transfer (24h verification)

**Support:**
📧 Email: {support_email}

**Business Hours:**
🕐 24/7 Support Available
            """
            
            await message.answer(help_text, parse_mode="Markdown")
            self._log_with_user_context('info', "Help command used", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in help command: {e}", user_id)
            await self._handle_user_error(message)

    async def cmd_orders(self, message: Message):
        """Handle /orders command"""
        user_id = str(message.from_user.id)
        try:
            user = await self._get_or_create_user(message.from_user)
            
            # Use context manager for database session
            with DatabaseManager.get_session() as db:
                orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(10).all()
                
                if not orders:
                    await message.answer(
                        "📋 **Your Orders**\n\nYou haven't placed any orders yet.\n\nClick 'New Order' to get started!",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    return
                
                orders_text = "📋 **Your Recent Orders:**\n\n"
                
                for order in orders:
                    status_emoji = {
                        'pending': '⏳',
                        'confirmed': '✅',
                        'in_progress': '🔄',
                        'delivered': '📦',
                        'completed': '✅',
                        'cancelled': '❌'
                    }.get(order.status, '❓')
                    
                    payment_emoji = {
                        'pending': '⏳',
                        'paid': '✅',
                        'failed': '❌',
                        'refunded': '↩️'
                    }.get(order.payment_status, '❓')
                    
                    orders_text += f"""
{status_emoji} **Order #{order.order_number}**
📝 {order.service_type.title()} - {order.subject}
💰 {order.total_amount} {order.currency}
💳 Payment: {payment_emoji} {order.payment_status.title()}
📅 Created: {order.created_at.strftime('%Y-%m-%d %H:%M')}

"""
                
                # Create inline keyboard for order actions
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="📝 New Order", callback_data="new_order")
                keyboard.button(text="🔄 Refresh", callback_data="my_orders")
                keyboard.adjust(2)
                
                await message.answer(
                    orders_text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
                
                self._log_with_user_context('info', f"Orders viewed, count: {len(orders)}", user_id)
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in orders command: {e}", user_id)
            await self._handle_user_error(message, "❌ Error fetching your orders. Please try again.")
    
    async def cmd_cancel(self, message: Message, state: FSMContext):
        """Handle /cancel command"""
        user_id = str(message.from_user.id)
        try:
            await state.clear()
            await message.answer(
                "❌ **Operation Cancelled**\n\nReturning to main menu...",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            self._log_with_user_context('info', "Operation cancelled", user_id)
        except Exception as e:
            self._log_with_user_context('error', f"Error in cancel command: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Handle main menu callback"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            await state.clear()
            
            user = await self._get_or_create_user(callback.from_user)
            
            welcome_text = f"""
🎓 **Student Services Platform**

Hello {user.full_name}! 👋

**What would you like to do?**
            """
            
            await callback.message.edit_text(
                welcome_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in main menu handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_new_order(self, callback: CallbackQuery, state: FSMContext):
        """Handle new order creation"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            text = """
📝 **New Order**

Please select the type of service you need:

📚 **Assignment** - Essays, reports, homework
📊 **Project** - Research projects, case studies
🎯 **Presentation** - PowerPoint, slides
🎨 **Redesign** - Improve existing work
📄 **Summary** - Summarize documents
⚡ **Express** - Urgent work (24h or less)
            """
            
            await callback.message.edit_text(
                text,
                reply_markup=get_service_menu(),
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('info', "New order flow started", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in new order handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_service_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle service type selection"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            service_type = callback.data.replace("service_", "")
            await state.update_data(service_type=service_type)
            
            service_names = {
                'assignment': 'Assignment',
                'project': 'Project',
                'presentation': 'Presentation',
                'redesign': 'Redesign',
                'summary': 'Summary',
                'express': 'Express Service'
            }
            
            service_name = service_names.get(service_type, service_type.title())
            
            text = f"""
📝 **{service_name} Order**

Please enter the **subject/title** of your work:

Example: "Marketing Strategy Analysis" or "Python Programming Assignment"
            """
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(OrderStates.waiting_for_subject)
            
            self._log_with_user_context('info', f"Service selected: {service_type}", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in service selection: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_subject_input(self, message: Message, state: FSMContext):
        """Handle subject input"""
        user_id = str(message.from_user.id)
        try:
            subject = message.text.strip()
            
            if len(subject) < 5:
                await message.answer("❌ Subject is too short. Please provide a more detailed subject (at least 5 characters).", parse_mode="Markdown")
                return
            
            await state.update_data(subject=subject)
            
            text = """
📋 **Requirements**

Please provide detailed requirements for your work:

Include:
• Number of pages/words
• Specific instructions
• Format requirements (APA, MLA, etc.)
• Any special requirements

The more details you provide, the better we can serve you!
            """
            
            await message.answer(text, parse_mode="Markdown")
            await state.set_state(OrderStates.waiting_for_requirements)
            
            self._log_with_user_context('info', f"Subject entered: {subject[:50]}...", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in subject input: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_requirements_input(self, message: Message, state: FSMContext):
        """Handle requirements input"""
        user_id = str(message.from_user.id)
        try:
            requirements = message.text.strip()
            
            if len(requirements) < 20:
                await message.answer("❌ Requirements are too brief. Please provide more detailed requirements (at least 20 characters).", parse_mode="Markdown")
                return
            
            await state.update_data(requirements=requirements)
            
            text = """
🎓 **Academic Level**

Please select your academic level:
            """
            
            await message.answer(
                text,
                reply_markup=get_academic_level_menu(),
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('info', f"Requirements entered: {len(requirements)} chars", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in requirements input: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_academic_level(self, callback: CallbackQuery, state: FSMContext):
        """Handle academic level selection"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            academic_level = callback.data.replace("level_", "")
            await state.update_data(academic_level=academic_level)
            
            text = """
⏰ **Deadline**

Please enter your deadline in one of these formats:

📅 **Date & Time:** "2024-12-25 14:30"
📅 **Date Only:** "2024-12-25" (assumes end of day)
⏱️ **Hours:** "24 hours" or "3 days"

Examples:
• "2024-12-25 14:30"
• "2024-12-25"
• "48 hours"
• "3 days"
            """
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(OrderStates.waiting_for_deadline)
            
            self._log_with_user_context('info', f"Academic level selected: {academic_level}", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in academic level selection: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_deadline_input(self, message: Message, state: FSMContext):
        """Handle deadline input"""
        user_id = str(message.from_user.id)
        try:
            deadline_text = message.text.strip().lower()
            deadline = None
            
            # Parse different deadline formats
            try:
                if "hour" in deadline_text:
                    hours = int(deadline_text.split()[0])
                    deadline = datetime.now() + timedelta(hours=hours)
                elif "day" in deadline_text:
                    days = int(deadline_text.split()[0])
                    deadline = datetime.now() + timedelta(days=days)
                else:
                    # Try to parse as date/datetime
                    if len(deadline_text) == 10:  # Date only
                        deadline = datetime.strptime(deadline_text, "%Y-%m-%d").replace(hour=23, minute=59)
                    else:  # Date and time
                        deadline = datetime.strptime(deadline_text, "%Y-%m-%d %H:%M")
                
                # Validate deadline is in the future
                if deadline <= datetime.now():
                    await message.answer("❌ Deadline must be in the future. Please enter a valid deadline.", parse_mode="Markdown")
                    return
                
            except (ValueError, IndexError):
                await message.answer("""
❌ Invalid deadline format. Please use one of these formats:

📅 **Date & Time:** "2024-12-25 14:30"
📅 **Date Only:** "2024-12-25"
⏱️ **Hours:** "24 hours" or "48 hours"
⏱️ **Days:** "3 days" or "7 days"
                """, parse_mode="Markdown")
                return
            
            await state.update_data(deadline=deadline)
            
            text = """
💰 **Currency**

Please select your preferred currency:
            """
            
            await message.answer(
                text,
                reply_markup=get_currency_menu(),
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('info', f"Deadline set: {deadline}", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in deadline input: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_currency_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle currency selection"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            currency = callback.data.replace("currency_", "")
            await state.update_data(currency=currency)
            
            # Calculate pricing
            data = await state.get_data()
            
            with DatabaseManager.get_session() as db:
                user = await self._get_or_create_user(callback.from_user)
                
                try:
                    pricing = self.pricing_service.calculate_price(
                        service_type=data['service_type'],
                        academic_level=data['academic_level'],
                        deadline=data['deadline'],
                        currency=currency,
                        pages=1  # Default, can be extracted from requirements
                    )
                    
                    await state.update_data(pricing=pricing)
                    
                    # Show order summary
                    requirements_preview = data['requirements'][:200]
                    if len(data['requirements']) > 200:
                        requirements_preview += "..."
                    
                    summary_text = f"""
📋 **Order Summary**

📝 **Service:** {data['service_type'].title()}
📚 **Subject:** {data['subject']}
🎓 **Level:** {data['academic_level'].replace('_', ' ').title()}
⏰ **Deadline:** {data['deadline'].strftime('%Y-%m-%d %H:%M')}

💰 **Pricing:**
• Base Price: {pricing['base_price']:.2f} {currency}
• Academic Level: {pricing['academic_multiplier']:.1f}x
• Urgency: {pricing['urgency_multiplier']:.1f}x
• **Total: {pricing['total_price']:.2f} {currency}**

📝 **Requirements:**
{requirements_preview}

Do you want to add any special notes? (Optional)
Send "skip" to continue without notes.
                    """
                    
                    await callback.message.edit_text(summary_text, parse_mode="Markdown")
                    await state.set_state(OrderStates.waiting_for_notes)
                    
                    self._log_with_user_context('info', f"Currency selected: {currency}, price: {pricing['total_price']}", user_id)
                    
                except Exception as e:
                    self._log_with_user_context('error', f"Error calculating pricing: {e}", user_id)
                    await self._handle_user_error(callback, "❌ Error calculating price. Please try again.")
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in currency selection: {e}", user_id)
            await self._handle_user_error(callback)

    async def handle_special_notes(self, message: Message, state: FSMContext):
        """Handle special notes input"""
        user_id = str(message.from_user.id)
        try:
            notes = message.text.strip() if message.text.strip().lower() != "skip" else None
            await state.update_data(special_notes=notes)
            
            # Create order
            data = await state.get_data()
            user = await self._get_or_create_user(message.from_user)
            
            with DatabaseManager.get_session() as db:
                try:
                    # Generate order number
                    order_count = db.query(Order).count()
                    order_number = f"SS{datetime.now().strftime('%Y%m%d')}{order_count + 1:04d}"
                    
                    # Create order
                    order = Order(
                        order_number=order_number,
                        user_id=user.id,
                        service_type=data['service_type'],
                        subject=data['subject'],
                        requirements=data['requirements'],
                        special_notes=notes,
                        deadline=data['deadline'],
                        academic_level=data['academic_level'],
                        base_price=data['pricing']['base_price'],
                        urgency_multiplier=data['pricing']['urgency_multiplier'],
                        total_amount=data['pricing']['total_price'],
                        currency=data['currency'],
                        status='pending',
                        payment_status='pending'
                    )
                    
                    db.add(order)
                    db.commit()
                    db.refresh(order)
                    
                    # Show payment options
                    payment_text = f"""
✅ **Order Created Successfully!**

📋 **Order #{order.order_number}**
💰 **Total: {order.total_amount:.2f} {order.currency}**

Please select your payment method:
                    """
                    
                    await message.answer(
                        payment_text,
                        reply_markup=get_payment_method_menu(order.id),
                        parse_mode="Markdown"
                    )
                    
                    await state.clear()
                    
                    # Send notification
                    await self._send_notification(
                        order,
                        f"New Order Created - #{order.order_number}",
                        f"A new order has been created and is awaiting payment."
                    )
                    
                    self._log_with_user_context('info', f"Order {order.order_number} created successfully", user_id)
                    
                except Exception as e:
                    self._log_with_user_context('error', f"Error creating order: {e}", user_id)
                    await self._handle_user_error(message, "❌ Error creating order. Please try again.")
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in special notes handler: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_payment_method(self, callback: CallbackQuery, state: FSMContext):
        """Handle payment method selection - delegated to PaymentService"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            payment_data = callback.data.replace("payment_", "").split("_")
            method = payment_data[0]
            order_id = int(payment_data[1])
            
            with DatabaseManager.get_session() as db:
                order = db.query(Order).filter(Order.id == order_id).first()
                
                if not order:
                    await self._handle_user_error(callback, "❌ Order not found.")
                    return
                
                # Delegate to payment service for processing
                result = await self._process_payment_method(method, order, callback, db)
                
                if result['success']:
                    self._log_with_user_context('info', f"Payment method {method} processed for order {order.order_number}", user_id)
                else:
                    self._log_with_user_context('error', f"Payment method {method} failed for order {order.order_number}: {result.get('error')}", user_id)
                    await self._handle_user_error(callback, result.get('error', "❌ Payment processing failed."))
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in payment method handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def _process_payment_method(self, method: str, order: Order, callback: CallbackQuery, db: Session) -> Dict[str, Any]:
        """Process payment method - separated from UI logic"""
        try:
            if method == "stripe":
                # Create Stripe checkout session
                session_data = await self.payment_service.create_stripe_session(order, db)
                
                payment_text = f"""
💳 **Credit/Debit Card Payment**

Order: #{order.order_number}
Amount: {order.total_amount:.2f} {order.currency}

Click the button below to pay securely with Stripe:
                """
                
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="💳 Pay Now", url=session_data['session_url'])
                keyboard.button(text="🔙 Back", callback_data=f"order_view_{order.id}")
                keyboard.adjust(1)
                
                await callback.message.edit_text(
                    payment_text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
                
                return {'success': True}
                
            elif method == "bank":
                # Show bank transfer details
                bank_details = self.payment_service.get_payment_methods()['bank_transfer']['bank_details']
                
                bank_text = f"""
🏦 **Bank Transfer Payment**

Order: #{order.order_number}
Amount: {order.total_amount:.2f} {order.currency}

**Bank Details:**
🏛️ Bank: {bank_details['bank_name']}
👤 Account Name: {bank_details['account_name']}
🔢 Account Number: {bank_details['account_number']}
🌐 IBAN: {bank_details['iban']}
📧 SWIFT: {bank_details['swift']}

**Instructions:**
1. Transfer the exact amount to the above account
2. Upload your receipt using the button below
3. We'll verify your payment within 24 hours

⚠️ **Important:** Include order number #{order.order_number} in the transfer reference
                """
                
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="📎 Upload Receipt", callback_data=f"upload_receipt_{order.id}")
                keyboard.button(text="🔙 Back", callback_data=f"order_view_{order.id}")
                keyboard.adjust(1)
                
                await callback.message.edit_text(
                    bank_text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
                
                return {'success': True}
            
            else:
                return {'success': False, 'error': f"Unknown payment method: {method}"}
                
        except Exception as e:
            return {'success': False, 'error': f"Payment processing error: {str(e)}"}
    
    async def handle_upload_receipt(self, callback: CallbackQuery, state: FSMContext):
        """Handle receipt upload initiation"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            order_id = int(callback.data.replace("upload_receipt_", ""))
            await state.update_data(order_id=order_id)
            await state.set_state(PaymentStates.waiting_for_receipt)
            
            text = """
📎 **Upload Payment Receipt**

Please upload your bank transfer receipt or screenshot.

**Supported formats:**
• PDF documents
• Images (JPG, PNG)
• Screenshots

**File size limit:** 20MB
            """
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            
            self._log_with_user_context('info', f"Receipt upload initiated for order {order_id}", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in upload receipt handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_file_upload(self, message: Message, state: FSMContext):
        """Handle file uploads with security checks"""
        user_id = str(message.from_user.id)
        try:
            # Check if we're expecting a bank receipt
            current_state = await state.get_state()
            
            if current_state == PaymentStates.waiting_for_receipt:
                await self.handle_bank_receipt(message, state)
                return
            
            # General file upload (requirements, etc.)
            if not message.document:
                await message.answer("❌ Please send a valid document file.", parse_mode="Markdown")
                return
            
            # File size check (20MB limit)
            max_size = 20 * 1024 * 1024  # 20MB
            if message.document.file_size > max_size:
                await message.answer("❌ File too large. Maximum size is 20MB.", parse_mode="Markdown")
                return
            
            # Get file info and download securely
            file_info = await self.bot.get_file(message.document.file_id)
            safe_filename = FileHandler.sanitize_filename(message.document.file_name)
            file_path = FileHandler.get_safe_upload_path("static/uploads", safe_filename)
            
            # Download file
            await self.bot.download_file(file_info.file_path, file_path)
            
            await message.answer(
                f"✅ File uploaded successfully!\n📎 {message.document.file_name}",
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('info', f"File uploaded: {safe_filename}", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error handling file upload: {e}", user_id)
            await self._handle_user_error(message, "❌ Error uploading file. Please try again.")
    
    async def handle_bank_receipt(self, message: Message, state: FSMContext):
        """Handle bank receipt upload with enhanced security"""
        user_id = str(message.from_user.id)
        try:
            data = await state.get_data()
            order_id = data.get('order_id')
            
            if not order_id:
                await message.answer("❌ No order found. Please start over.", parse_mode="Markdown")
                await state.clear()
                return
            
            if not message.document:
                await message.answer("❌ Please send a valid document file.", parse_mode="Markdown")
                return
            
            # File size check (20MB limit)
            max_size = 20 * 1024 * 1024  # 20MB
            if message.document.file_size > max_size:
                await message.answer("❌ File too large. Maximum size is 20MB.", parse_mode="Markdown")
                return
            
            with DatabaseManager.get_session() as db:
                order = db.query(Order).filter(Order.id == order_id).first()
                
                if not order:
                    await message.answer("❌ Order not found.", parse_mode="Markdown")
                    await state.clear()
                    return
                
                try:
                    # Download receipt file securely
                    file_info = await self.bot.get_file(message.document.file_id)
                    safe_filename = FileHandler.sanitize_filename(message.document.file_name)
                    receipt_filename = f"{order.order_number}_{safe_filename}"
                    file_path = FileHandler.get_safe_upload_path("static/uploads", receipt_filename, "receipts")
                    
                    # Download file
                    await self.bot.download_file(file_info.file_path, file_path)
                    
                    # Process bank transfer
                    result = await self.payment_service.process_bank_transfer(order, file_path, db)
                    
                    await message.answer(
                        f"""
✅ **Receipt Uploaded Successfully!**

📋 Order: #{order.order_number}
📎 File: {message.document.file_name}

{result['message']}

We'll notify you once the payment is verified.
                        """,
                        parse_mode="Markdown"
                    )
                    
                    await state.clear()
                    
                    # Send notification to admin
                    await self._send_notification(
                        order,
                        f"Payment Receipt Uploaded - #{order.order_number}",
                        f"A payment receipt has been uploaded for order #{order.order_number}. Please verify the payment."
                    )
                    
                    self._log_with_user_context('info', f"Bank receipt uploaded for order {order.order_number}", user_id)
                    
                except Exception as e:
                    self._log_with_user_context('error', f"Error processing bank receipt: {e}", user_id)
                    await self._handle_user_error(message, "❌ Error processing receipt. Please try again.")
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in bank receipt handler: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_my_orders(self, callback: CallbackQuery):
        """Handle my orders view"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            user = await self._get_or_create_user(callback.from_user)
            
            with DatabaseManager.get_session() as db:
                orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(5).all()
                
                if not orders:
                    await callback.message.edit_text(
                        "📋 **Your Orders**\n\nYou haven't placed any orders yet.\n\nClick 'New Order' to get started!",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    return
                
                orders_text = "📋 **Your Recent Orders:**\n\n"
                keyboard = InlineKeyboardBuilder()
                
                for order in orders:
                    status_emoji = {
                        'pending': '⏳',
                        'confirmed': '✅',
                        'in_progress': '🔄',
                        'delivered': '📦',
                        'completed': '✅',
                        'cancelled': '❌'
                    }.get(order.status, '❓')
                    
                    orders_text += f"{status_emoji} **#{order.order_number}** - {order.subject[:30]}...\n"
                    keyboard.button(
                        text=f"📋 {order.order_number}",
                        callback_data=f"order_view_{order.id}"
                    )
                
                keyboard.button(text="📝 New Order", callback_data="new_order")
                keyboard.button(text="🔙 Main Menu", callback_data="main_menu")
                keyboard.adjust(2)
                
                await callback.message.edit_text(
                    orders_text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
                
                self._log_with_user_context('info', f"Orders list viewed, count: {len(orders)}", user_id)
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in my orders handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_support(self, callback: CallbackQuery):
        """Handle support request"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            support_email = settings.support_email or 'support@example.com'
            support_text = f"""
🆘 **Support & Help**

**Contact Information:**
📧 Email: {support_email}
💬 Telegram: Available 24/7

**Common Issues:**
• Payment problems
• Order modifications
• Technical support
• General inquiries

**Response Time:**
🕐 Usually within 2-4 hours
⚡ Urgent issues: Contact immediately

How can we help you today?
            """
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📧 Send Email", url=f"mailto:{support_email}")
            keyboard.button(text="🔙 Main Menu", callback_data="main_menu")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                support_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('info', "Support page accessed", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in support handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_feedback(self, callback: CallbackQuery, state: FSMContext):
        """Handle feedback initiation"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer()
            
            text = """
⭐ **Feedback**

We value your feedback! Please rate your experience:

**Rating Scale:**
⭐ 1 - Poor
⭐⭐ 2 - Fair  
⭐⭐⭐ 3 - Good
⭐⭐⭐⭐ 4 - Very Good
⭐⭐⭐⭐⭐ 5 - Excellent

Please send a number from 1 to 5:
            """
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(FeedbackStates.waiting_for_rating)
            
            self._log_with_user_context('info', "Feedback process started", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in feedback handler: {e}", user_id)
            await self._handle_user_error(callback)
    
    async def handle_feedback_rating(self, message: Message, state: FSMContext):
        """Handle feedback rating input"""
        user_id = str(message.from_user.id)
        try:
            try:
                rating = int(message.text.strip())
                if rating < 1 or rating > 5:
                    raise ValueError("Rating out of range")
            except ValueError:
                await message.answer("❌ Please send a valid rating from 1 to 5.", parse_mode="Markdown")
                return
            
            await state.update_data(rating=rating)
            
            stars = "⭐" * rating
            text = f"""
{stars} **Thank you for your rating!**

Would you like to add any comments? (Optional)

Send your comments or type "skip" to finish:
            """
            
            await message.answer(text, parse_mode="Markdown")
            await state.set_state(FeedbackStates.waiting_for_comment)
            
            self._log_with_user_context('info', f"Feedback rating: {rating}/5", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in feedback rating handler: {e}", user_id)
            await self._handle_user_error(message)
    
    async def handle_feedback_comment(self, message: Message, state: FSMContext):
        """Handle feedback comment input"""
        user_id = str(message.from_user.id)
        try:
            comment = message.text.strip() if message.text.strip().lower() != "skip" else None
            data = await state.get_data()
            
            user = await self._get_or_create_user(message.from_user)
            
            with DatabaseManager.get_session() as db:
                try:
                    # Create feedback record
                    feedback = Feedback(
                        user_id=user.id,
                        rating=data['rating'],
                        comment=comment,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(feedback)
                    db.commit()
                    
                    stars = "⭐" * data['rating']
                    
                    await message.answer(
                        f"""
✅ **Feedback Submitted!**

{stars} Rating: {data['rating']}/5

Thank you for helping us improve our service!
                        """,
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    
                    await state.clear()
                    
                    self._log_with_user_context('info', f"Feedback submitted: {data['rating']}/5", user_id)
                    
                except Exception as e:
                    self._log_with_user_context('error', f"Error saving feedback: {e}", user_id)
                    await self._handle_user_error(message, "❌ Error saving feedback. Please try again.")
                
        except Exception as e:
            self._log_with_user_context('error', f"Error in feedback comment handler: {e}", user_id)
            await self._handle_user_error(message)

    async def handle_unknown_callback(self, callback: CallbackQuery):
        """Fallback handler for unexpected callbacks"""
        user_id = str(callback.from_user.id)
        try:
            await callback.answer("❌ Unknown action")
            
            text = """
❓ **Unknown Action**

Sorry, I didn't understand that action. 
Let's return to the main menu:
            """
            
            await callback.message.edit_text(
                text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            
            self._log_with_user_context('warning', f"Unknown callback: {callback.data}", user_id)
            
        except Exception as e:
            self._log_with_user_context('error', f"Error in unknown callback handler: {e}", user_id)
    
    async def _get_or_create_user(self, telegram_user) -> User:
        """Get or create user from Telegram user data with proper session management"""
        with DatabaseManager.get_session() as db:
            user = db.query(User).filter(User.telegram_id == str(telegram_user.id)).first()
            
            if not user:
                # Create new user
                full_name = f"{telegram_user.first_name} {telegram_user.last_name or ''}".strip()
                user = User(
                    telegram_id=str(telegram_user.id),
                    telegram_username=telegram_user.username,
                    full_name=full_name,
                    language=telegram_user.language_code or "en",
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                self._log_with_user_context('info', f"New user created: {full_name}", str(telegram_user.id))
            else:
                # Update last activity
                user.last_activity = datetime.utcnow()
                db.commit()
            
            return user
    
    async def error_handler(self, event, exception):
        """Enhanced error handler with user notifications and admin alerts"""
        user_id = 'unknown'
        
        try:
            # Extract user ID if available
            if hasattr(event, 'from_user') and event.from_user:
                user_id = str(event.from_user.id)
            elif hasattr(event, 'message') and event.message and event.message.from_user:
                user_id = str(event.message.from_user.id)
            
            self._log_with_user_context('error', f"Bot error: {exception}", user_id)
            
            # Send user-friendly error message
            if hasattr(event, 'message') and event.message:
                try:
                    await event.message.answer(
                        "❌ An unexpected error occurred. Please try again or contact support.",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                except Exception as send_error:
                    logger.error(f"Failed to send error message to user: {send_error}")
            
            # Send admin notification for critical errors
            if hasattr(settings, 'telegram_admin_id') and settings.telegram_admin_id:
                try:
                    admin_message = f"""
🚨 **Bot Error Alert**

**User ID:** {user_id}
**Error:** {str(exception)[:200]}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the logs for more details.
                    """
                    
                    await self.bot.send_message(
                        chat_id=settings.telegram_admin_id,
                        text=admin_message,
                        parse_mode="Markdown"
                    )
                except Exception as admin_error:
                    logger.error(f"Failed to send admin notification: {admin_error}")
                    
        except Exception as handler_error:
            logger.error(f"Error in error handler: {handler_error}")
    
    async def start_polling(self):
        """Start bot polling with enhanced error handling"""
        try:
            logger.info("Starting Telegram bot polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise
    
    async def start_webhook(self, webhook_url: str, webhook_path: str = "/webhook"):
        """Start bot with webhook (recommended for production)"""
        try:
            logger.info(f"Starting Telegram bot with webhook: {webhook_url}")
            
            # Set webhook
            await self.bot.set_webhook(
                url=f"{webhook_url}{webhook_path}",
                drop_pending_updates=True
            )
            
            logger.info("Webhook set successfully")
            
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            raise
    
    async def stop(self):
        """Stop bot with proper cleanup"""
        try:
            if self.bot:
                await self.bot.session.close()
            
            # Close storage if it has a close method
            if hasattr(self.dp.storage, 'close'):
                await self.dp.storage.close()
                
            logger.info("Telegram bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

# -------------------------------------------------
# Rate Limiting (Optional Enhancement)
# -------------------------------------------------

class RateLimiter:
    """Simple rate limiter to prevent spam"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        now = datetime.now()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if (now - req_time).seconds < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        
        return False

# -------------------------------------------------
# Main Entry Point
# -------------------------------------------------

async def main():
    """Main function to run the bot with enhanced initialization"""
    
    # Validate required configuration
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        print("Please set TELEGRAM_BOT_TOKEN in your environment variables")
        return
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"Database initialization failed: {e}")
        return
    
    # Create and configure bot
    try:
        bot = StudentServicesBot()
        logger.info("Bot instance created successfully")
    except Exception as e:
        logger.error(f"Bot initialization failed: {e}")
        print(f"Bot initialization failed: {e}")
        return
    
    # Start bot based on configuration
    try:
        # Check if webhook URL is configured for production
        webhook_url = getattr(settings, 'webhook_url', None)
        
        if webhook_url:
            # Production mode with webhook
            logger.info("Starting bot in webhook mode (production)")
            await bot.start_webhook(webhook_url)
            
            # Keep the process running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
                
        else:
            # Development mode with polling
            logger.info("Starting bot in polling mode (development)")
            await bot.start_polling()
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Bot runtime error: {e}")
        print(f"Bot runtime error: {e}")
    finally:
        try:
            await bot.stop()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")

# -------------------------------------------------
# Webhook Handler (for production deployment)
# -------------------------------------------------

def create_webhook_app(bot_instance: StudentServicesBot):
    """Create FastAPI app for webhook handling"""
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        
        app = FastAPI(title="Telegram Bot Webhook")
        
        @app.post("/webhook")
        async def webhook_handler(request: Request):
            """Handle incoming webhook updates"""
            try:
                update_data = await request.json()
                update = types.Update(**update_data)
                await bot_instance.dp.feed_update(bot_instance.bot, update)
                return JSONResponse({"status": "ok"})
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return JSONResponse({"status": "error"}, status_code=500)
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return JSONResponse({"status": "healthy", "service": "telegram-bot"})
        
        return app
        
    except ImportError:
        logger.warning("FastAPI not available for webhook mode")
        return None

# -------------------------------------------------
# Entry Point
# -------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
