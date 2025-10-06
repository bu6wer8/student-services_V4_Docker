# File: app/bot/states.py
from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """States for new user registration"""
    language = State()
    country = State()
    full_name = State()
    student_id = State()
    email = State()
    phone = State()

class OrderStates(StatesGroup):
    """States for order creation process"""
    service_selection = State()
    subject = State()
    requirements = State()
    upload_files = State()
    special_notes = State()
    deadline = State()
    academic_level = State()
    review_order = State()
    payment_method = State()
    payment_confirmation = State()

class FeedbackStates(StatesGroup):
    """States for feedback collection"""
    rating = State()
    comment = State()

class SupportStates(StatesGroup):
    """States for support conversation"""
    issue_description = State()
    waiting_response = State()