# File: app/bot/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_language_keyboard():
    """Language selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton(text="عربي 🇸🇦", callback_data="lang_ar")]
    ])
    return keyboard

def get_country_keyboard():
    """Country selection keyboard for currency"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇯🇴 Jordan (JOD)", callback_data="country_JO")],
        [InlineKeyboardButton(text="🇦🇪 UAE (AED)", callback_data="country_AE")],
        [InlineKeyboardButton(text="🇸🇦 Saudi Arabia (SAR)", callback_data="country_SA")],
        [InlineKeyboardButton(text="🌍 Other (USD)", callback_data="country_OTHER")]
    ])
    return keyboard

def get_services_keyboard():
    """Main services menu keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Assignments", callback_data="service_assignment")],
        [InlineKeyboardButton(text="💻 IT Projects", callback_data="service_project")],
        [InlineKeyboardButton(text="📊 Presentations", callback_data="service_presentation")],
        [InlineKeyboardButton(text="🔄 Redesign Presentation", callback_data="service_redesign")],
        [InlineKeyboardButton(text="📚 Course Summary", callback_data="service_summary")],
        [InlineKeyboardButton(text="⚡ Express (24hr)", callback_data="service_express")]
    ])
    return keyboard

def get_academic_level_keyboard():
    """Academic level selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="High School", callback_data="level_high_school")],
        [InlineKeyboardButton(text="Bachelor", callback_data="level_bachelor")],
        [InlineKeyboardButton(text="Masters", callback_data="level_masters")],
        [InlineKeyboardButton(text="PhD", callback_data="level_phd")]
    ])
    return keyboard

def get_payment_keyboard():
    """Payment method selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Pay with Card (Stripe)", callback_data="pay_stripe")],
        [InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="pay_bank")]
    ])
    return keyboard

def get_skip_keyboard():
    """Skip button keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip ⏭️", callback_data="skip")]
    ])
    return keyboard

def get_deadline_keyboard():
    """Deadline selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="24 hours ⚡", callback_data="deadline_1")],
        [InlineKeyboardButton(text="2 days", callback_data="deadline_2")],
        [InlineKeyboardButton(text="3 days", callback_data="deadline_3")],
        [InlineKeyboardButton(text="5 days", callback_data="deadline_5")],
        [InlineKeyboardButton(text="7 days", callback_data="deadline_7")],
        [InlineKeyboardButton(text="Custom", callback_data="deadline_custom")]
    ])
    return keyboard

def get_confirmation_keyboard():
    """Yes/No confirmation keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ No", callback_data="confirm_no")
        ]
    ])
    return keyboard

def get_main_menu_keyboard():
    """Main menu keyboard for returning users"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 New Order", callback_data="new_order")],
        [InlineKeyboardButton(text="📋 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton(text="💬 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")]
    ])
    return keyboard

def get_cancel_keyboard():
    """Cancel operation keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Cancel", callback_data="cancel")]
    ])
    return keyboard
