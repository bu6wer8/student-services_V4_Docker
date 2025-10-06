#!/usr/bin/env python3
"""
Student Services Platform - Telegram Bot
Production-ready bot with comprehensive order management and payment processing
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, StateFilter
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from sqlalchemy.orm import Session
    
    AIOGRAM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: aiogram not available: {e}")
    print("Bot functionality will be disabled. Install aiogram to enable bot features.")
    AIOGRAM_AVAILABLE = False

# Import application modules
from config.config import settings
from app.models.database import get_db, init_database
from app.models.models import User, Order, Payment, Feedback
from app.services.pricing import PricingService
from app.services.payment import PaymentService
from app.services.notification import NotificationService

if AIOGRAM_AVAILABLE:
    from app.bot.states import OrderStates, PaymentStates, FeedbackStates
    from app.bot.keyboards import (
        get_main_menu, get_service_menu, get_academic_level_menu,
        get_currency_menu, get_payment_method_menu, get_order_actions_menu
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("telegram-bot")

class StudentServicesBot:
    """
    Main bot class for handling all Telegram interactions
    """
    
    def __init__(self):
        if not AIOGRAM_AVAILABLE:
            logger.error("aiogram not available. Bot cannot start.")
            return
            
        if not settings.telegram_bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured. Bot cannot start.")
            return
        
        self.bot = Bot(token=settings.telegram_bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.pricing_service = PricingService()
        self.payment_service = PaymentService()
        self.notification_service = NotificationService()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Student Services Bot initialized")
    
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
        
        # Order creation flow
        self.dp.callback_query.register(self.handle_service_selection, F.data.startswith("service_"))
        self.dp.callback_query.register(self.handle_academic_level, F.data.startswith("level_"))
        self.dp.callback_query.register(self.handle_currency_selection, F.data.startswith("currency_"))
        self.dp.callback_query.register(self.handle_payment_method, F.data.startswith("payment_"))
        
        # Order management
        self.dp.callback_query.register(self.handle_order_action, F.data.startswith("order_"))
        self.dp.callback_query.register(self.handle_payment_action, F.data.startswith("pay_"))
        
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
        
        # Error handler
        self.dp.error.register(self.error_handler)
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Handle /start command"""
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
            
            logger.info(f"User {user.telegram_id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.answer("❌ An error occurred. Please try again later.")
    
    async def cmd_help(self, message: Message):
        """Handle /help command"""
        help_text = """
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
📧 Email: {settings.support_email}
💬 Telegram: {settings.support_telegram}

**Business Hours:**
🕐 24/7 Support Available
        """
        
        await message.answer(help_text, parse_mode="Markdown")
    
    async def cmd_orders(self, message: Message):
        """Handle /orders command"""
        try:
            user = await self._get_or_create_user(message.from_user)
            
            # Get database session
            db = next(get_db())
            orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(10).all()
            db.close()
            
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
            
        except Exception as e:
            logger.error(f"Error in orders command: {e}")
            await message.answer("❌ An error occurred while fetching your orders.")
    
    async def cmd_cancel(self, message: Message, state: FSMContext):
        """Handle /cancel command"""
        await state.clear()
        await message.answer(
            "❌ **Operation Cancelled**\n\nReturning to main menu...",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_new_order(self, callback: CallbackQuery, state: FSMContext):
        """Handle new order creation"""
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
            
        except Exception as e:
            logger.error(f"Error in new order handler: {e}")
            await callback.answer("❌ An error occurred. Please try again.")
    
    async def handle_service_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle service type selection"""
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
            
            text = f"""
📝 **{service_names.get(service_type, service_type.title())} Order**

Please enter the **subject/title** of your work:

Example: "Marketing Strategy Analysis" or "Python Programming Assignment"
            """
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(OrderStates.waiting_for_subject)
            
        except Exception as e:
            logger.error(f"Error in service selection: {e}")
            await callback.answer("❌ An error occurred. Please try again.")
    
    async def handle_subject_input(self, message: Message, state: FSMContext):
        """Handle subject input"""
        try:
            subject = message.text.strip()
            
            if len(subject) < 5:
                await message.answer("❌ Subject is too short. Please provide a more detailed subject (at least 5 characters).")
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
            
        except Exception as e:
            logger.error(f"Error in subject input: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_requirements_input(self, message: Message, state: FSMContext):
        """Handle requirements input"""
        try:
            requirements = message.text.strip()
            
            if len(requirements) < 20:
                await message.answer("❌ Requirements are too brief. Please provide more detailed requirements (at least 20 characters).")
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
            
        except Exception as e:
            logger.error(f"Error in requirements input: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_academic_level(self, callback: CallbackQuery, state: FSMContext):
        """Handle academic level selection"""
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
            
        except Exception as e:
            logger.error(f"Error in academic level selection: {e}")
            await callback.answer("❌ An error occurred. Please try again.")
    
    async def handle_deadline_input(self, message: Message, state: FSMContext):
        """Handle deadline input"""
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
                    await message.answer("❌ Deadline must be in the future. Please enter a valid deadline.")
                    return
                
            except (ValueError, IndexError):
                await message.answer("""
❌ Invalid deadline format. Please use one of these formats:

📅 **Date & Time:** "2024-12-25 14:30"
📅 **Date Only:** "2024-12-25"
⏱️ **Hours:** "24 hours" or "48 hours"
⏱️ **Days:** "3 days" or "7 days"
                """)
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
            
        except Exception as e:
            logger.error(f"Error in deadline input: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_currency_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle currency selection"""
        try:
            await callback.answer()
            
            currency = callback.data.replace("currency_", "")
            await state.update_data(currency=currency)
            
            # Calculate pricing
            data = await state.get_data()
            
            # Get database session
            db = next(get_db())
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
{data['requirements'][:200]}{'...' if len(data['requirements']) > 200 else ''}

Do you want to add any special notes? (Optional)
Send "skip" to continue without notes.
                """
                
                await callback.message.edit_text(summary_text, parse_mode="Markdown")
                await state.set_state(OrderStates.waiting_for_notes)
                
            except Exception as e:
                logger.error(f"Error calculating pricing: {e}")
                await callback.answer("❌ Error calculating price. Please try again.")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in currency selection: {e}")
            await callback.answer("❌ An error occurred. Please try again.")
    
    async def handle_special_notes(self, message: Message, state: FSMContext):
        """Handle special notes input"""
        try:
            notes = message.text.strip() if message.text.strip().lower() != "skip" else None
            await state.update_data(special_notes=notes)
            
            # Create order
            data = await state.get_data()
            user = await self._get_or_create_user(message.from_user)
            
            # Get database session
            db = next(get_db())
            
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
                
                logger.info(f"Order {order.order_number} created for user {user.telegram_id}")
                
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                await message.answer("❌ Error creating order. Please try again.")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in special notes handler: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_payment_method(self, callback: CallbackQuery, state: FSMContext):
        """Handle payment method selection"""
        try:
            await callback.answer()
            
            payment_data = callback.data.replace("payment_", "").split("_")
            method = payment_data[0]
            order_id = int(payment_data[1])
            
            # Get database session
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                await callback.answer("❌ Order not found.")
                db.close()
                return
            
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
                
            except Exception as e:
                logger.error(f"Error processing payment method: {e}")
                await callback.answer("❌ Error processing payment. Please try again.")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in payment method handler: {e}")
            await callback.answer("❌ An error occurred. Please try again.")
    
    async def handle_my_orders(self, callback: CallbackQuery):
        """Handle my orders view"""
        try:
            await callback.answer()
            
            user = await self._get_or_create_user(callback.from_user)
            
            # Get database session
            db = next(get_db())
            orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(5).all()
            db.close()
            
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
            
        except Exception as e:
            logger.error(f"Error in my orders handler: {e}")
            await callback.answer("❌ An error occurred. Please try again.")
    
    async def handle_file_upload(self, message: Message, state: FSMContext):
        """Handle file uploads"""
        try:
            # Check if we're expecting a bank receipt
            current_state = await state.get_state()
            
            if current_state == PaymentStates.waiting_for_receipt:
                await self.handle_bank_receipt(message, state)
                return
            
            # General file upload (requirements, etc.)
            file_info = await self.bot.get_file(message.document.file_id)
            file_path = f"static/uploads/{message.document.file_name}"
            
            # Download file
            await self.bot.download_file(file_info.file_path, file_path)
            
            await message.answer(
                f"✅ File uploaded successfully!\n📎 {message.document.file_name}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            await message.answer("❌ Error uploading file. Please try again.")
    
    async def handle_bank_receipt(self, message: Message, state: FSMContext):
        """Handle bank receipt upload"""
        try:
            data = await state.get_data()
            order_id = data.get('order_id')
            
            if not order_id:
                await message.answer("❌ No order found. Please start over.")
                await state.clear()
                return
            
            # Get database session
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                await message.answer("❌ Order not found.")
                db.close()
                await state.clear()
                return
            
            try:
                # Download receipt file
                file_info = await self.bot.get_file(message.document.file_id)
                file_path = f"static/uploads/receipts/{order.order_number}_{message.document.file_name}"
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
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
                
                logger.info(f"Bank receipt uploaded for order {order.order_number}")
                
            except Exception as e:
                logger.error(f"Error processing bank receipt: {e}")
                await message.answer("❌ Error processing receipt. Please try again.")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in bank receipt handler: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def _get_or_create_user(self, telegram_user) -> User:
        """Get or create user from Telegram user data"""
        db = next(get_db())
        
        try:
            user = db.query(User).filter(User.telegram_id == str(telegram_user.id)).first()
            
            if not user:
                user = User(
                    telegram_id=str(telegram_user.id),
                    telegram_username=telegram_user.username,
                    full_name=f"{telegram_user.first_name} {telegram_user.last_name or ''}".strip(),
                    language=telegram_user.language_code or "en"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"New user created: {user.telegram_id}")
            else:
                # Update last activity
                user.last_activity = datetime.utcnow()
                db.commit()
            
            return user
            
        finally:
            db.close()
    
    async def error_handler(self, event, exception):
        """Handle bot errors"""
        logger.error(f"Bot error: {exception}")
        
        if hasattr(event, 'message') and event.message:
            try:
                await event.message.answer(
                    "❌ An unexpected error occurred. Please try again or contact support.",
                    reply_markup=get_main_menu()
                )
            except:
                pass
    
    async def start_polling(self):
        """Start bot polling"""
        if not AIOGRAM_AVAILABLE:
            logger.error("Cannot start bot: aiogram not available")
            return
        
        try:
            logger.info("Starting Telegram bot...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def stop(self):
        """Stop bot"""
        if AIOGRAM_AVAILABLE and self.bot:
            await self.bot.session.close()
            logger.info("Telegram bot stopped")

# -------------------------------------------------
# Main Entry Point
# -------------------------------------------------

async def main():
    """Main function to run the bot"""
    if not AIOGRAM_AVAILABLE:
        logger.error("aiogram not available. Please install it to run the bot.")
        print("To install aiogram, run: pip install aiogram")
        return
    
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        print("Please set TELEGRAM_BOT_TOKEN in your environment variables")
        return
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return
    
    # Create and start bot
    bot = StudentServicesBot()
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    if AIOGRAM_AVAILABLE:
        asyncio.run(main())
    else:
        print("aiogram not available. Bot cannot start.")
        print("Install aiogram with: pip install aiogram")
