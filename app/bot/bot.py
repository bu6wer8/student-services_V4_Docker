#!/usr/bin/env python3
"""
Student Services Platform - Telegram Bot (Arabic Support + Enhanced UX)
Multi-language bot with Arabic support and improved user journey
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import aiogram
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, StateFilter
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from sqlalchemy.orm import Session
except ImportError as e:
    print(f"Error: aiogram not available: {e}")
    sys.exit(1)

# Import application modules
from config.config import settings
from app.models.database import get_db, init_database
from app.models.models import User, Order, Payment, Feedback
from app.services.pricing import PricingService
from app.services.payment import PaymentService

# Import existing states
from app.bot.states import OrderStates, FeedbackStates, SupportStates, RegistrationStates

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("telegram-bot")

# -------------------------------------------------
# Multi-language Support
# -------------------------------------------------

MESSAGES = {
    'en': {
        'welcome_title': '🎓 **Welcome to Student Services Platform!**',
        'language_prompt': 'Please select your preferred language:',
        'welcome_message': '''Hello {name}! 👋

We provide high-quality academic writing services:
📝 Assignments & Essays
📊 Projects & Research  
🎯 Presentations
✨ And much more!

**What would you like to do?**''',
        'main_menu': {
            'new_order': '📝 New Order',
            'my_orders': '📋 My Orders', 
            'support': '💬 Contact Support',
            'help': 'ℹ️ Help'
        },
        'services': {
            'assignment': '📝 Assignments',
            'project': '💻 IT Projects',
            'presentation': '📊 Presentations', 
            'redesign': '🔄 Redesign Presentation',
            'summary': '📚 Course Summary',
            'express': '⚡ Express (24hr)'
        },
        'academic_levels': {
            'high_school': 'High School',
            'bachelor': 'Bachelor',
            'masters': 'Masters', 
            'phd': 'PhD'
        },
        'currencies': {
            'AED': '🇦🇪 UAE Dirham (AED)',
            'USD': '🇺🇸 US Dollar (USD)',
            'JOD': '🇯🇴 Jordanian Dinar (JOD)'
        },
        'payment_methods': {
            'stripe': '💳 Pay with Card (Stripe)',
            'bank': '🏦 Bank Transfer'
        },
        'order_flow': {
            'service_selection': '📝 **New Order**\n\nPlease select the type of service you need:',
            'subject_prompt': '📝 **{service} Order**\n\nPlease enter the **subject/title** of your work:\n\nExample: "Marketing Strategy Analysis" or "Python Programming Assignment"',
            'requirements_prompt': '''📋 **Requirements**

Please provide detailed requirements for your work:

Include:
• Number of pages/words
• Specific instructions  
• Format requirements (APA, MLA, etc.)
• Any special requirements

The more details you provide, the better we can serve you!''',
            'academic_level_prompt': '🎓 **Academic Level**\n\nPlease select your academic level:',
            'deadline_prompt': '''⏰ **Deadline**

Please enter your deadline in one of these formats:

📅 **Date & Time:** "2024-12-25 14:30"
📅 **Date Only:** "2024-12-25"
⏱️ **Hours:** "24 hours" or "3 days"

Examples:
• "2024-12-25 14:30"
• "2024-12-25"  
• "48 hours"
• "3 days"''',
            'currency_prompt': '💰 **Currency**\n\nPlease select your preferred currency:',
            'notes_prompt': '''📋 **Order Summary**

📝 **Service:** {service}
📚 **Subject:** {subject}
🎓 **Level:** {level}
⏰ **Deadline:** {deadline}

💰 **Pricing:**
• Base Price: {base_price:.2f} {currency}
• Academic Level: {academic_multiplier:.1f}x
• Urgency: {urgency_multiplier:.1f}x
• **Total: {total_price:.2f} {currency}**

Do you want to add any special notes? (Optional)
Send "skip" to continue without notes.''',
            'order_created': '''✅ **Order Created Successfully!**

📋 **Order #{order_number}**
💰 **Total: {total:.2f} {currency}**

Please select your payment method:'''
        },
        'errors': {
            'general': '❌ An error occurred. Please try again.',
            'subject_short': '❌ Subject is too short. Please provide a more detailed subject (at least 5 characters).',
            'requirements_short': '❌ Requirements are too brief. Please provide more detailed requirements (at least 20 characters).',
            'deadline_future': '❌ Deadline must be in the future. Please enter a valid deadline.',
            'deadline_format': '''❌ Invalid deadline format. Please use one of these formats:

📅 **Date & Time:** "2024-12-25 14:30"
📅 **Date Only:** "2024-12-25"
⏱️ **Hours:** "24 hours" or "48 hours"
⏱️ **Days:** "3 days" or "7 days"'''
        }
    },
    'ar': {
        'welcome_title': '🎓 **مرحباً بك في منصة الخدمات الطلابية!**',
        'language_prompt': 'يرجى اختيار لغتك المفضلة:',
        'welcome_message': '''مرحباً {name}! 👋

نحن نقدم خدمات كتابة أكاديمية عالية الجودة:
📝 الواجبات والمقالات
📊 المشاريع والأبحاث
🎯 العروض التقديمية
✨ والمزيد!

**ماذا تريد أن تفعل؟**''',
        'main_menu': {
            'new_order': '📝 طلب جديد',
            'my_orders': '📋 طلباتي',
            'support': '💬 اتصل بالدعم',
            'help': 'ℹ️ مساعدة'
        },
        'services': {
            'assignment': '📝 الواجبات',
            'project': '💻 مشاريع تقنية',
            'presentation': '📊 عروض تقديمية',
            'redesign': '🔄 إعادة تصميم العرض',
            'summary': '📚 ملخص المقرر',
            'express': '⚡ خدمة سريعة (24 ساعة)'
        },
        'academic_levels': {
            'high_school': 'المرحلة الثانوية',
            'bachelor': 'البكالوريوس',
            'masters': 'الماجستير',
            'phd': 'الدكتوراه'
        },
        'currencies': {
            'AED': '🇦🇪 درهم إماراتي (AED)',
            'USD': '🇺🇸 دولار أمريكي (USD)', 
            'JOD': '🇯🇴 دينار أردني (JOD)'
        },
        'payment_methods': {
            'stripe': '💳 الدفع بالبطاقة (Stripe)',
            'bank': '🏦 تحويل بنكي'
        },
        'order_flow': {
            'service_selection': '📝 **طلب جديد**\n\nيرجى اختيار نوع الخدمة التي تحتاجها:',
            'subject_prompt': '📝 **طلب {service}**\n\nيرجى إدخال **موضوع/عنوان** عملك:\n\nمثال: "تحليل استراتيجية التسويق" أو "واجب برمجة Python"',
            'requirements_prompt': '''📋 **المتطلبات**

يرجى تقديم متطلبات مفصلة لعملك:

تشمل:
• عدد الصفحات/الكلمات
• تعليمات محددة
• متطلبات التنسيق (APA، MLA، إلخ)
• أي متطلبات خاصة

كلما قدمت تفاصيل أكثر، كلما تمكنا من خدمتك بشكل أفضل!''',
            'academic_level_prompt': '🎓 **المستوى الأكاديمي**\n\nيرجى اختيار مستواك الأكاديمي:',
            'deadline_prompt': '''⏰ **الموعد النهائي**

يرجى إدخال موعدك النهائي بأحد هذه التنسيقات:

📅 **التاريخ والوقت:** "2024-12-25 14:30"
📅 **التاريخ فقط:** "2024-12-25"
⏱️ **الساعات:** "24 hours" أو "3 days"

أمثلة:
• "2024-12-25 14:30"
• "2024-12-25"
• "48 hours"
• "3 days"''',
            'currency_prompt': '💰 **العملة**\n\nيرجى اختيار عملتك المفضلة:',
            'notes_prompt': '''📋 **ملخص الطلب**

📝 **الخدمة:** {service}
📚 **الموضوع:** {subject}
🎓 **المستوى:** {level}
⏰ **الموعد النهائي:** {deadline}

💰 **التسعير:**
• السعر الأساسي: {base_price:.2f} {currency}
• المستوى الأكاديمي: {academic_multiplier:.1f}x
• الاستعجال: {urgency_multiplier:.1f}x
• **المجموع: {total_price:.2f} {currency}**

هل تريد إضافة أي ملاحظات خاصة؟ (اختياري)
أرسل "skip" للمتابعة بدون ملاحظات.''',
            'order_created': '''✅ **تم إنشاء الطلب بنجاح!**

📋 **الطلب رقم #{order_number}**
💰 **المجموع: {total:.2f} {currency}**

يرجى اختيار طريقة الدفع:'''
        },
        'errors': {
            'general': '❌ حدث خطأ. يرجى المحاولة مرة أخرى.',
            'subject_short': '❌ الموضوع قصير جداً. يرجى تقديم موضوع أكثر تفصيلاً (5 أحرف على الأقل).',
            'requirements_short': '❌ المتطلبات مختصرة جداً. يرجى تقديم متطلبات أكثر تفصيلاً (20 حرف على الأقل).',
            'deadline_future': '❌ يجب أن يكون الموعد النهائي في المستقبل. يرجى إدخال موعد صحيح.',
            'deadline_format': '''❌ تنسيق الموعد النهائي غير صحيح. يرجى استخدام أحد هذه التنسيقات:

📅 **التاريخ والوقت:** "2024-12-25 14:30"
📅 **التاريخ فقط:** "2024-12-25"
⏱️ **الساعات:** "24 hours" أو "48 hours"
⏱️ **الأيام:** "3 days" أو "7 days"'''
        }
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """Get localized text with formatting"""
    keys = key.split('.')
    text = MESSAGES.get(lang, MESSAGES['en'])
    
    for k in keys:
        text = text.get(k, key)
    
    if isinstance(text, str) and kwargs:
        return text.format(**kwargs)
    return text

# -------------------------------------------------
# Keyboard Builders
# -------------------------------------------------

def get_language_keyboard():
    """Language selection keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="English 🇬🇧", callback_data="lang_en")
    keyboard.button(text="العربية 🇸🇦", callback_data="lang_ar")
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_main_menu_keyboard(lang: str = 'en'):
    """Main menu keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=get_text(lang, 'main_menu.new_order'), callback_data="new_order")
    keyboard.button(text=get_text(lang, 'main_menu.my_orders'), callback_data="my_orders")
    keyboard.button(text=get_text(lang, 'main_menu.support'), callback_data="contact_support")
    keyboard.button(text=get_text(lang, 'main_menu.help'), callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_services_keyboard(lang: str = 'en'):
    """Services selection keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=get_text(lang, 'services.assignment'), callback_data="service_assignment")
    keyboard.button(text=get_text(lang, 'services.project'), callback_data="service_project")
    keyboard.button(text=get_text(lang, 'services.presentation'), callback_data="service_presentation")
    keyboard.button(text=get_text(lang, 'services.redesign'), callback_data="service_redesign")
    keyboard.button(text=get_text(lang, 'services.summary'), callback_data="service_summary")
    keyboard.button(text=get_text(lang, 'services.express'), callback_data="service_express")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_academic_level_keyboard(lang: str = 'en'):
    """Academic level selection keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=get_text(lang, 'academic_levels.high_school'), callback_data="level_high_school")
    keyboard.button(text=get_text(lang, 'academic_levels.bachelor'), callback_data="level_bachelor")
    keyboard.button(text=get_text(lang, 'academic_levels.masters'), callback_data="level_masters")
    keyboard.button(text=get_text(lang, 'academic_levels.phd'), callback_data="level_phd")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_currency_keyboard(lang: str = 'en'):
    """Currency selection keyboard - AED as main currency"""
    keyboard = InlineKeyboardBuilder()
    # AED first as main currency
    keyboard.button(text=get_text(lang, 'currencies.AED'), callback_data="currency_AED")
    keyboard.button(text=get_text(lang, 'currencies.USD'), callback_data="currency_USD")
    keyboard.button(text=get_text(lang, 'currencies.JOD'), callback_data="currency_JOD")
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_payment_keyboard(lang: str = 'en'):
    """Payment method selection keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=get_text(lang, 'payment_methods.stripe'), callback_data="pay_stripe")
    keyboard.button(text=get_text(lang, 'payment_methods.bank'), callback_data="pay_bank")
    keyboard.adjust(1)
    return keyboard.as_markup()

# -------------------------------------------------
# Database Manager
# -------------------------------------------------

class DatabaseManager:
    """Simple database session manager"""
    
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

# -------------------------------------------------
# Main Bot Class
# -------------------------------------------------

class StudentServicesBot:
    """
    Multi-language bot with Arabic support and enhanced UX
    """
    
    def __init__(self):
        if not settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        self.bot = Bot(token=settings.telegram_bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.pricing_service = PricingService()
        self.payment_service = PaymentService()
        
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
        
        # Language selection
        self.dp.callback_query.register(self.handle_language_selection, F.data.startswith("lang_"))
        
        # Main menu handlers
        self.dp.callback_query.register(self.handle_new_order, F.data == "new_order")
        self.dp.callback_query.register(self.handle_my_orders, F.data == "my_orders")
        self.dp.callback_query.register(self.handle_contact_support, F.data == "contact_support")
        self.dp.callback_query.register(self.handle_help, F.data == "help")
        
        # Service selection
        self.dp.callback_query.register(self.handle_service_selection, F.data.startswith("service_"))
        
        # Academic level selection
        self.dp.callback_query.register(self.handle_academic_level, F.data.startswith("level_"))
        
        # Currency selection
        self.dp.callback_query.register(self.handle_currency_selection, F.data.startswith("currency_"))
        
        # Payment method selection
        self.dp.callback_query.register(self.handle_payment_method, F.data.startswith("pay_"))
        
        # State handlers
        self.dp.message.register(self.handle_subject_input, StateFilter(OrderStates.subject))
        self.dp.message.register(self.handle_requirements_input, StateFilter(OrderStates.requirements))
        self.dp.message.register(self.handle_deadline_input, StateFilter(OrderStates.deadline))
        self.dp.message.register(self.handle_special_notes, StateFilter(OrderStates.special_notes))
        
        # Feedback handlers
        self.dp.message.register(self.handle_feedback_rating, StateFilter(FeedbackStates.rating))
        self.dp.message.register(self.handle_feedback_comment, StateFilter(FeedbackStates.comment))
        
        # File handlers
        self.dp.message.register(self.handle_file_upload, F.document)
        
        # Error handler
        self.dp.error.register(self.error_handler)
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Handle /start command - Language selection first"""
        try:
            await state.clear()
            
            # Check if user exists and has language preference
            user = await self._get_user_if_exists(message.from_user)
            
            if user and user.get('language'):
                # User exists with language preference, show main menu
                await self._show_main_menu(message, user['language'], user['full_name'])
            else:
                # New user or no language set, show language selection
                welcome_text = """🎓 **Welcome to Student Services Platform!**
مرحباً بك في منصة الخدمات الطلابية!

Please select your preferred language:
يرجى اختيار لغتك المفضلة:"""
                
                await message.answer(
                    welcome_text,
                    reply_markup=get_language_keyboard(),
                    parse_mode="Markdown"
                )
            
            logger.info(f"User {message.from_user.id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.answer("❌ An error occurred. Please try again.\n❌ حدث خطأ. يرجى المحاولة مرة أخرى.")
    
    async def handle_language_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle language selection"""
        try:
            await callback.answer()
            
            language = callback.data.replace("lang_", "")
            
            # Create or update user with language preference
            user = await self._get_or_create_user(callback.from_user, language)
            
            # Show main menu in selected language
            await self._show_main_menu_callback(callback, language, user['full_name'])
            
            logger.info(f"User {callback.from_user.id} selected language: {language}")
            
        except Exception as e:
            logger.error(f"Error in language selection: {e}")
            await callback.answer("❌ Error occurred")
    
    async def _show_main_menu(self, message: Message, lang: str, name: str):
        """Show main menu message"""
        welcome_text = get_text(lang, 'welcome_title') + '\n\n' + get_text(lang, 'welcome_message', name=name)
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    
    async def _show_main_menu_callback(self, callback: CallbackQuery, lang: str, name: str):
        """Show main menu via callback"""
        welcome_text = get_text(lang, 'welcome_title') + '\n\n' + get_text(lang, 'welcome_message', name=name)
        
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    
    async def handle_new_order(self, callback: CallbackQuery, state: FSMContext):
        """Handle new order creation"""
        try:
            await callback.answer()
            
            user = await self._get_user_data(callback.from_user)
            lang = user.get('language', 'en')
            
            text = get_text(lang, 'order_flow.service_selection')
            
            await callback.message.edit_text(
                text,
                reply_markup=get_services_keyboard(lang),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in new order handler: {e}")
            await callback.answer("❌ Error occurred")
    
    async def handle_service_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle service type selection"""
        try:
            await callback.answer()
            
            user = await self._get_user_data(callback.from_user)
            lang = user.get('language', 'en')
            
            service_type = callback.data.replace("service_", "")
            await state.update_data(service_type=service_type, language=lang)
            
            service_name = get_text(lang, f'services.{service_type}')
            text = get_text(lang, 'order_flow.subject_prompt', service=service_name)
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(OrderStates.subject)
            
        except Exception as e:
            logger.error(f"Error in service selection: {e}")
            await callback.answer("❌ Error occurred")
    
    async def handle_subject_input(self, message: Message, state: FSMContext):
        """Handle subject input"""
        try:
            data = await state.get_data()
            lang = data.get('language', 'en')
            
            subject = message.text.strip()
            
            if len(subject) < 5:
                await message.answer(get_text(lang, 'errors.subject_short'))
                return
            
            await state.update_data(subject=subject)
            
            text = get_text(lang, 'order_flow.requirements_prompt')
            await message.answer(text, parse_mode="Markdown")
            await state.set_state(OrderStates.requirements)
            
        except Exception as e:
            logger.error(f"Error in subject input: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_requirements_input(self, message: Message, state: FSMContext):
        """Handle requirements input"""
        try:
            data = await state.get_data()
            lang = data.get('language', 'en')
            
            requirements = message.text.strip()
            
            if len(requirements) < 20:
                await message.answer(get_text(lang, 'errors.requirements_short'))
                return
            
            await state.update_data(requirements=requirements)
            
            text = get_text(lang, 'order_flow.academic_level_prompt')
            await message.answer(
                text,
                reply_markup=get_academic_level_keyboard(lang),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in requirements input: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_academic_level(self, callback: CallbackQuery, state: FSMContext):
        """Handle academic level selection"""
        try:
            await callback.answer()
            
            data = await state.get_data()
            lang = data.get('language', 'en')
            
            academic_level = callback.data.replace("level_", "")
            await state.update_data(academic_level=academic_level)
            
            text = get_text(lang, 'order_flow.deadline_prompt')
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(OrderStates.deadline)
            
        except Exception as e:
            logger.error(f"Error in academic level selection: {e}")
            await callback.answer("❌ Error occurred")
    
    async def handle_deadline_input(self, message: Message, state: FSMContext):
        """Handle deadline input"""
        try:
            data = await state.get_data()
            lang = data.get('language', 'en')
            
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
                    await message.answer(get_text(lang, 'errors.deadline_future'))
                    return
                
            except (ValueError, IndexError):
                await message.answer(get_text(lang, 'errors.deadline_format'))
                return
            
            await state.update_data(deadline=deadline)
            
            text = get_text(lang, 'order_flow.currency_prompt')
            await message.answer(
                text,
                reply_markup=get_currency_keyboard(lang),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in deadline input: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_currency_selection(self, callback: CallbackQuery, state: FSMContext):
        """Handle currency selection"""
        try:
            await callback.answer()
            
            data = await state.get_data()
            lang = data.get('language', 'en')
            
            currency = callback.data.replace("currency_", "")
            await state.update_data(currency=currency)
            
            # Calculate pricing
            try:
                # Calculate days until deadline
                days_until_deadline = max(1, (data['deadline'] - datetime.now()).days)
                
                pricing = self.pricing_service.calculate_price(
                    service_type=data['service_type'],
                    academic_level=data['academic_level'],
                    days_until_deadline=days_until_deadline,
                    currency=currency
                )
                
                await state.update_data(pricing=pricing)
                
                # Show order summary
                service_name = get_text(lang, f"services.{data['service_type']}")
                level_name = get_text(lang, f"academic_levels.{data['academic_level']}")
                
                summary_text = get_text(lang, 'order_flow.notes_prompt',
                    service=service_name,
                    subject=data['subject'],
                    level=level_name,
                    deadline=data['deadline'].strftime('%Y-%m-%d %H:%M'),
                    base_price=pricing['base_price'],
                    currency=currency,
                    academic_multiplier=pricing['academic_multiplier'],
                    urgency_multiplier=pricing['urgency_multiplier'],
                    total_price=pricing['total_price']
                )
                
                await callback.message.edit_text(summary_text, parse_mode="Markdown")
                await state.set_state(OrderStates.special_notes)
                
            except Exception as e:
                logger.error(f"Error calculating pricing: {e}")
                await callback.answer("❌ Error calculating price. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in currency selection: {e}")
            await callback.answer("❌ Error occurred")

    async def handle_special_notes(self, message: Message, state: FSMContext):
        """Handle special notes input"""
        try:
            data = await state.get_data()
            lang = data.get('language', 'en')
            
            notes = message.text.strip() if message.text.strip().lower() != "skip" else None
            await state.update_data(special_notes=notes)
            
            # Create order
            user = await self._get_user_data(message.from_user)
            
            with DatabaseManager.get_session() as db:
                try:
                    # Generate order number
                    order_count = db.query(Order).count()
                    order_number = f"SS{datetime.now().strftime('%Y%m%d')}{order_count + 1:04d}"
                    
                    # Create order
                    order = Order(
                        order_number=order_number,
                        user_id=user['id'],
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
                    payment_text = get_text(lang, 'order_flow.order_created',
                        order_number=order.order_number,
                        total=order.total_amount,
                        currency=order.currency
                    )
                    
                    await message.answer(
                        payment_text,
                        reply_markup=get_payment_keyboard(lang),
                        parse_mode="Markdown"
                    )
                    
                    await state.clear()
                    
                    logger.info(f"Order {order.order_number} created successfully")
                    
                except Exception as e:
                    logger.error(f"Error creating order: {e}")
                    await message.answer(get_text(lang, 'errors.general'))
                
        except Exception as e:
            logger.error(f"Error in special notes handler: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_payment_method(self, callback: CallbackQuery):
        """Handle payment method selection"""
        try:
            await callback.answer()
            
            user = await self._get_user_data(callback.from_user)
            lang = user.get('language', 'en')
            
            method = callback.data.replace("pay_", "")
            
            if method == "stripe":
                if lang == 'ar':
                    text = """💳 **الدفع بالبطاقة الائتمانية**

سيتم توجيهك إلى صفحة الدفع الآمنة عبر Stripe.

هذه الميزة قيد الإعداد حالياً. يرجى التواصل مع الدعم للمساعدة في الدفع."""
                else:
                    text = """💳 **Credit/Debit Card Payment**

You will be redirected to our secure Stripe payment page.

This feature is currently being set up. Please contact support for payment assistance."""
                    
            elif method == "bank":
                if lang == 'ar':
                    text = """🏦 **الدفع عبر التحويل البنكي**

**تفاصيل البنك:**
🏛️ البنك: بنك الإمارات دبي الوطني
👤 اسم الحساب: Student Services
🔢 رقم الحساب: 1234567890
🌐 IBAN: AE07 0331 2345 6789 0123 456
📧 SWIFT: EBILAEAD

**التعليمات:**
1. حول المبلغ الدقيق إلى الحساب أعلاه
2. أرسل لنا إيصال التحويل عبر الدعم
3. سنتحقق من دفعتك خلال 24 ساعة

⚠️ **مهم:** اذكر رقم طلبك في مرجع التحويل"""
                else:
                    text = """🏦 **Bank Transfer Payment**

**Bank Details:**
🏛️ Bank: Emirates NBD
👤 Account Name: Student Services
🔢 Account Number: 1234567890
🌐 IBAN: AE07 0331 2345 6789 0123 456
📧 SWIFT: EBILAEAD

**Instructions:**
1. Transfer the exact amount to the above account
2. Send us the receipt via support
3. We'll verify your payment within 24 hours

⚠️ **Important:** Include your order number in the transfer reference"""
            else:
                text = "❌ Unknown payment method selected."
            
            await callback.message.edit_text(
                text,
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in payment method handler: {e}")
            await callback.answer("❌ Error occurred")
    
    async def handle_my_orders(self, callback: CallbackQuery):
        """Handle my orders view"""
        try:
            await callback.answer()
            
            user = await self._get_user_data(callback.from_user)
            lang = user.get('language', 'en')
            
            with DatabaseManager.get_session() as db:
                orders = db.query(Order).filter(Order.user_id == user['id']).order_by(Order.created_at.desc()).limit(5).all()
                
                if not orders:
                    if lang == 'ar':
                        text = "📋 **طلباتك**\n\nلم تقم بوضع أي طلبات بعد.\n\nانقر على 'طلب جديد' للبدء!"
                    else:
                        text = "📋 **Your Orders**\n\nYou haven't placed any orders yet.\n\nClick 'New Order' to get started!"
                        
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_main_menu_keyboard(lang),
                        parse_mode="Markdown"
                    )
                    return
                
                if lang == 'ar':
                    orders_text = "📋 **طلباتك الأخيرة:**\n\n"
                else:
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
                    
                    orders_text += f"{status_emoji} **#{order.order_number}** - {order.subject[:30]}...\n"
                
                await callback.message.edit_text(
                    orders_text,
                    reply_markup=get_main_menu_keyboard(lang),
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error in my orders handler: {e}")
            await callback.answer("❌ Error occurred")
    
    async def handle_contact_support(self, callback: CallbackQuery):
        """Handle support request"""
        try:
            await callback.answer()
            
            user = await self._get_user_data(callback.from_user)
            lang = user.get('language', 'en')
            
            if lang == 'ar':
                support_text = """🆘 **الدعم والمساعدة**

**معلومات التواصل:**
📧 البريد الإلكتروني: support@studentservices.com
💬 تليجرام: متاح 24/7

**المشاكل الشائعة:**
• مشاكل الدفع
• تعديل الطلبات
• الدعم التقني
• استفسارات عامة

**وقت الاستجابة:**
🕐 عادة خلال 2-4 ساعات
⚡ المشاكل العاجلة: تواصل فوراً

كيف يمكننا مساعدتك اليوم؟"""
            else:
                support_text = """🆘 **Support & Help**

**Contact Information:**
📧 Email: support@studentservices.com
💬 Telegram: Available 24/7

**Common Issues:**
• Payment problems
• Order modifications
• Technical support
• General inquiries

**Response Time:**
🕐 Usually within 2-4 hours
⚡ Urgent issues: Contact immediately

How can we help you today?"""
            
            await callback.message.edit_text(
                support_text,
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in support handler: {e}")
            await callback.answer("❌ Error occurred")
    
    async def handle_help(self, callback: CallbackQuery):
        """Handle help request"""
        try:
            await callback.answer()
            
            user = await self._get_user_data(callback.from_user)
            lang = user.get('language', 'en')
            
            if lang == 'ar':
                help_text = """ℹ️ **المساعدة والمعلومات**

**كيفية وضع طلب:**
1️⃣ انقر على "📝 طلب جديد"
2️⃣ اختر نوع الخدمة
3️⃣ املأ المتطلبات
4️⃣ اختر طريقة الدفع
5️⃣ أكمل الدفع

**الخدمات المتاحة:**
📝 الواجبات والمقالات
💻 المشاريع التقنية
📊 العروض التقديمية
🔄 خدمات إعادة التصميم
📚 ملخصات المقررات
⚡ الخدمات السريعة (24 ساعة)

**طرق الدفع:**
💳 البطاقة الائتمانية (Stripe)
🏦 التحويل البنكي

تحتاج مساعدة أكثر؟ تواصل مع فريق الدعم!"""
            else:
                help_text = """ℹ️ **Help & Information**

**How to place an order:**
1️⃣ Click "📝 New Order"
2️⃣ Select service type
3️⃣ Fill in requirements
4️⃣ Choose payment method
5️⃣ Complete payment

**Available Services:**
📝 Assignments & Essays
💻 IT Projects
📊 Presentations
🔄 Redesign Services
📚 Course Summaries
⚡ Express Services (24h)

**Payment Methods:**
💳 Credit/Debit Card (Stripe)
🏦 Bank Transfer

Need more help? Contact our support team!"""
            
            await callback.message.edit_text(
                help_text,
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in help handler: {e}")
            await callback.answer("❌ Error occurred")
    
    async def cmd_help(self, message: Message):
        """Handle /help command"""
        try:
            user = await self._get_user_data(message.from_user)
            lang = user.get('language', 'en') if user else 'en'
            
            if lang == 'ar':
                help_text = """🆘 **المساعدة والدعم**

**الأوامر المتاحة:**
/start - بدء البوت وعرض القائمة الرئيسية
/orders - عرض طلباتك
/cancel - إلغاء العملية الحالية
/help - عرض رسالة المساعدة هذه

**كيفية وضع طلب:**
1️⃣ انقر على "📝 طلب جديد"
2️⃣ اختر نوع الخدمة
3️⃣ املأ المتطلبات
4️⃣ اختر طريقة الدفع
5️⃣ أكمل الدفع

**طرق الدفع:**
💳 البطاقة الائتمانية (فوري)
🏦 التحويل البنكي (تحقق خلال 24 ساعة)

**الدعم:**
📧 البريد الإلكتروني: support@studentservices.com

**ساعات العمل:**
🕐 دعم متاح 24/7"""
            else:
                help_text = """🆘 **Help & Support**

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
📧 Email: support@studentservices.com

**Business Hours:**
🕐 24/7 Support Available"""
            
            await message.answer(help_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await message.answer("❌ An error occurred. Please try again.")

    async def cmd_orders(self, message: Message):
        """Handle /orders command"""
        try:
            user = await self._get_user_data(message.from_user)
            
            if not user:
                await message.answer("Please start the bot first with /start")
                return
                
            lang = user.get('language', 'en')
            
            with DatabaseManager.get_session() as db:
                orders = db.query(Order).filter(Order.user_id == user['id']).order_by(Order.created_at.desc()).limit(10).all()
                
                if not orders:
                    if lang == 'ar':
                        text = "📋 **طلباتك**\n\nلم تقم بوضع أي طلبات بعد.\n\nانقر على 'طلب جديد' للبدء!"
                    else:
                        text = "📋 **Your Orders**\n\nYou haven't placed any orders yet.\n\nClick 'New Order' to get started!"
                        
                    await message.answer(
                        text,
                        reply_markup=get_main_menu_keyboard(lang),
                        parse_mode="Markdown"
                    )
                    return
                
                if lang == 'ar':
                    orders_text = "📋 **طلباتك الأخيرة:**\n\n"
                else:
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
                    
                    orders_text += f"""
{status_emoji} **Order #{order.order_number}**
📝 {order.service_type.title()} - {order.subject}
💰 {order.total_amount} {order.currency}
📅 Created: {order.created_at.strftime('%Y-%m-%d %H:%M')}

"""
                
                await message.answer(
                    orders_text,
                    reply_markup=get_main_menu_keyboard(lang),
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error in orders command: {e}")
            await message.answer("❌ Error fetching your orders. Please try again.")
    
    async def cmd_cancel(self, message: Message, state: FSMContext):
        """Handle /cancel command"""
        try:
            user = await self._get_user_data(message.from_user)
            lang = user.get('language', 'en') if user else 'en'
            
            await state.clear()
            
            if lang == 'ar':
                text = "❌ **تم إلغاء العملية**\n\nالعودة إلى القائمة الرئيسية..."
            else:
                text = "❌ **Operation Cancelled**\n\nReturning to main menu..."
                
            await message.answer(
                text,
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in cancel command: {e}")
            await message.answer("❌ An error occurred.")
    
    async def handle_feedback_rating(self, message: Message, state: FSMContext):
        """Handle feedback rating input"""
        try:
            user = await self._get_user_data(message.from_user)
            lang = user.get('language', 'en')
            
            try:
                rating = int(message.text.strip())
                if rating < 1 or rating > 5:
                    raise ValueError("Rating out of range")
            except ValueError:
                if lang == 'ar':
                    await message.answer("❌ يرجى إرسال تقييم صحيح من 1 إلى 5.")
                else:
                    await message.answer("❌ Please send a valid rating from 1 to 5.")
                return
            
            await state.update_data(rating=rating)
            
            stars = "⭐" * rating
            
            if lang == 'ar':
                text = f"""
{stars} **شكراً لك على تقييمك!**

هل تريد إضافة أي تعليقات؟ (اختياري)

أرسل تعليقاتك أو اكتب "skip" للانتهاء:
                """
            else:
                text = f"""
{stars} **Thank you for your rating!**

Would you like to add any comments? (Optional)

Send your comments or type "skip" to finish:
                """
            
            await message.answer(text, parse_mode="Markdown")
            await state.set_state(FeedbackStates.comment)
            
        except Exception as e:
            logger.error(f"Error in feedback rating handler: {e}")
            await message.answer("❌ An error occurred. Please try again.")
    
    async def handle_feedback_comment(self, message: Message, state: FSMContext):
        """Handle feedback comment input"""
        try:
            user = await self._get_user_data(message.from_user)
            lang = user.get('language', 'en')
            
            comment = message.text.strip() if message.text.strip().lower() != "skip" else None
            data = await state.get_data()
            
            with DatabaseManager.get_session() as db:
                try:
                    # Create feedback record
                    feedback = Feedback(
                        user_id=user['id'],
                        rating=data['rating'],
                        comment=comment,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(feedback)
                    db.commit()
                    
                    stars = "⭐" * data['rating']
                    
                    if lang == 'ar':
                        text = f"""
✅ **تم إرسال التقييم!**

{stars} التقييم: {data['rating']}/5

شكراً لك لمساعدتنا في تحسين خدمتنا!
                        """
                    else:
                        text = f"""
✅ **Feedback Submitted!**

{stars} Rating: {data['rating']}/5

Thank you for helping us improve our service!
                        """
                    
                    await message.answer(
                        text,
                        reply_markup=get_main_menu_keyboard(lang),
                        parse_mode="Markdown"
                    )
                    
                    await state.clear()
                    
                except Exception as e:
                    logger.error(f"Error saving feedback: {e}")
                    await message.answer(get_text(lang, 'errors.general'))
                
        except Exception as e:
            logger.error(f"Error in feedback comment handler: {e}")
            await message.answer("❌ An error occurred. Please try again.")

    async def handle_file_upload(self, message: Message):
        """Handle file uploads"""
        try:
            user = await self._get_user_data(message.from_user)
            lang = user.get('language', 'en') if user else 'en'
            
            if not message.document:
                if lang == 'ar':
                    await message.answer("❌ يرجى إرسال ملف صحيح.")
                else:
                    await message.answer("❌ Please send a valid document file.")
                return
            
            # File size check (20MB limit)
            max_size = 20 * 1024 * 1024  # 20MB
            if message.document.file_size > max_size:
                if lang == 'ar':
                    await message.answer("❌ الملف كبير جداً. الحد الأقصى 20 ميجابايت.")
                else:
                    await message.answer("❌ File too large. Maximum size is 20MB.")
                return
            
            if lang == 'ar':
                text = f"✅ تم استلام الملف: {message.document.file_name}\n\nمعالجة رفع الملفات قيد الإعداد. يرجى التواصل مع الدعم لإرسال الملفات."
            else:
                text = f"✅ File received: {message.document.file_name}\n\nFile upload processing is being set up. Please contact support for file submissions."
            
            await message.answer(text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            await message.answer("❌ Error processing file. Please try again.")
    
    async def _get_user_if_exists(self, telegram_user) -> Optional[Dict[str, Any]]:
        """Check if user exists and return user data"""
        try:
            with DatabaseManager.get_session() as db:
                user = db.query(User).filter(User.telegram_id == str(telegram_user.id)).first()
                
                if user:
                    return {
                        'id': user.id,
                        'telegram_id': user.telegram_id,
                        'full_name': user.full_name,
                        'telegram_username': user.telegram_username,
                        'language': user.language
                    }
                return None
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return None
    
    async def _get_user_data(self, telegram_user) -> Dict[str, Any]:
        """Get existing user data"""
        with DatabaseManager.get_session() as db:
            user = db.query(User).filter(User.telegram_id == str(telegram_user.id)).first()
            
            if user:
                return {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'full_name': user.full_name,
                    'telegram_username': user.telegram_username,
                    'language': user.language
                }
            else:
                # Create user with default language if not exists
                return await self._get_or_create_user(telegram_user, 'en')
    
    async def _get_or_create_user(self, telegram_user, language: str = 'en') -> Dict[str, Any]:
        """Get or create user from Telegram user data"""
        with DatabaseManager.get_session() as db:
            user = db.query(User).filter(User.telegram_id == str(telegram_user.id)).first()
            
            if not user:
                # Create new user
                full_name = f"{telegram_user.first_name} {telegram_user.last_name or ''}".strip()
                
                # Map currency based on language/region
                currency_map = {
                    'ar': 'AED',  # Arabic users default to AED
                    'en': 'AED'   # AED as main currency for all
                }
                
                user = User(
                    telegram_id=str(telegram_user.id),
                    telegram_username=telegram_user.username,
                    full_name=full_name,
                    language=language,
                    country="UAE" if language == 'ar' else "OTH",  # 3-character limit fix
                    currency=currency_map.get(language, 'AED'),
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"New user created: {full_name} (Language: {language})")
            else:
                # Update language and last activity
                user.language = language
                user.last_activity = datetime.utcnow()
                db.commit()
            
            # Return user data as dict to avoid session issues
            return {
                'id': user.id,
                'telegram_id': user.telegram_id,
                'full_name': user.full_name,
                'telegram_username': user.telegram_username,
                'language': user.language
            }
    
    async def error_handler(self, event, exception):
        """Simple error handler"""
        logger.error(f"Bot error: {exception}")
        
        # Try to send user-friendly error message
        try:
            if hasattr(event, 'message') and event.message:
                await event.message.answer(
                    "❌ An unexpected error occurred. Please try again or contact support.\n❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى أو التواصل مع الدعم."
                )
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
    
    async def start_polling(self):
        """Start bot polling"""
        try:
            logger.info("Starting Telegram bot polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise
    
    async def stop(self):
        """Stop bot"""
        try:
            if self.bot:
                await self.bot.session.close()
            logger.info("Telegram bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

# -------------------------------------------------
# Main Entry Point
# -------------------------------------------------

async def main():
    """Main function to run the bot"""
    
    # Validate configuration
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
    
    # Create and start bot
    try:
        bot = StudentServicesBot()
        logger.info("Bot instance created successfully")
        
        # Start polling
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

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
