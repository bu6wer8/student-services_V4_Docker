# File: app/services/notification.py
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Optional, Dict, Any
from aiogram import Bot
from config.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling customer notifications via email and Telegram"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.bot_token = settings.telegram_bot_token
        self.admin_id = settings.telegram_admin_id
        
    async def send_email(self, to_email: str, subject: str, message: str, html_message: Optional[str] = None) -> bool:
        """Send email notification to customer"""
        try:
            msg = MimeMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MimeText(message, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_message:
                html_part = MimeText(html_message, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_telegram_message(self, chat_id: str, message: str, parse_mode: str = "Markdown") -> bool:
        """Send Telegram message to customer"""
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode)
            logger.info(f"Telegram message sent to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
            return False
    
    async def notify_admin(self, message: str) -> bool:
        """Send notification to admin"""
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(chat_id=self.admin_id, text=message, parse_mode="Markdown")
            logger.info("Admin notification sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
            return False
    
    async def notify_order_status_change(self, order_data: Dict[str, Any], new_status: str) -> bool:
        """Notify customer about order status change"""
        customer_email = order_data.get('customer_email')
        customer_telegram_id = order_data.get('customer_telegram_id')
        order_number = order_data.get('order_number')
        customer_language = order_data.get('customer_language', 'en')
        
        # Prepare messages in customer's language
        if customer_language == 'ar':
            subject = f"تحديث حالة الطلب {order_number}"
            email_message = f"""
مرحباً،

تم تحديث حالة طلبك {order_number} إلى: {new_status}

شكراً لاختيارك خدماتنا الطلابية.

مع أطيب التحيات،
فريق الخدمات الطلابية
"""
            telegram_message = f"🔔 تم تحديث حالة طلبك {order_number} إلى: **{new_status}**"
        else:
            subject = f"Order Status Update - {order_number}"
            email_message = f"""
Hello,

Your order {order_number} status has been updated to: {new_status}

Thank you for choosing our student services.

Best regards,
Student Services Team
"""
            telegram_message = f"🔔 Your order {order_number} status has been updated to: **{new_status}**"
        
        # Send notifications
        success = True
        
        if customer_email:
            email_sent = await self.send_email(customer_email, subject, email_message)
            success = success and email_sent
        
        if customer_telegram_id:
            telegram_sent = await self.send_telegram_message(customer_telegram_id, telegram_message)
            success = success and telegram_sent
        
        return success
    
    async def notify_order_delivered(self, order_data: Dict[str, Any], files: list = None) -> bool:
        """Notify customer that order has been delivered"""
        customer_email = order_data.get('customer_email')
        customer_telegram_id = order_data.get('customer_telegram_id')
        order_number = order_data.get('order_number')
        customer_language = order_data.get('customer_language', 'en')
        
        files_text = ""
        if files:
            if customer_language == 'ar':
                files_text = f"\n\nالملفات المرفقة: {len(files)} ملف"
            else:
                files_text = f"\n\nAttached files: {len(files)} file(s)"
        
        # Prepare messages
        if customer_language == 'ar':
            subject = f"تم تسليم طلبك {order_number}"
            email_message = f"""
مرحباً،

تم تسليم طلبك {order_number} بنجاح!{files_text}

يمكنك تحميل الملفات من خلال التواصل معنا.

شكراً لاختيارك خدماتنا الطلابية.

مع أطيب التحيات،
فريق الخدمات الطلابية
"""
            telegram_message = f"✅ تم تسليم طلبك {order_number} بنجاح!{files_text}"
        else:
            subject = f"Order Delivered - {order_number}"
            email_message = f"""
Hello,

Your order {order_number} has been delivered successfully!{files_text}

You can download the files by contacting us.

Thank you for choosing our student services.

Best regards,
Student Services Team
"""
            telegram_message = f"✅ Your order {order_number} has been delivered successfully!{files_text}"
        
        # Send notifications
        success = True
        
        if customer_email:
            email_sent = await self.send_email(customer_email, subject, email_message)
            success = success and email_sent
        
        if customer_telegram_id:
            telegram_sent = await self.send_telegram_message(customer_telegram_id, telegram_message)
            success = success and telegram_sent
        
        return success
    
    async def send_custom_message(self, order_data: Dict[str, Any], message: str) -> bool:
        """Send custom message to customer"""
        customer_email = order_data.get('customer_email')
        customer_telegram_id = order_data.get('customer_telegram_id')
        order_number = order_data.get('order_number')
        customer_language = order_data.get('customer_language', 'en')
        
        # Prepare subject
        if customer_language == 'ar':
            subject = f"رسالة بخصوص طلبك {order_number}"
            email_header = f"مرحباً،\n\nبخصوص طلبك {order_number}:\n\n"
            email_footer = "\n\nمع أطيب التحيات،\nفريق الخدمات الطلابية"
        else:
            subject = f"Message regarding your order {order_number}"
            email_header = f"Hello,\n\nRegarding your order {order_number}:\n\n"
            email_footer = "\n\nBest regards,\nStudent Services Team"
        
        email_message = email_header + message + email_footer
        telegram_message = f"💬 **Message regarding order {order_number}:**\n\n{message}"
        
        # Send notifications
        success = True
        
        if customer_email:
            email_sent = await self.send_email(customer_email, subject, email_message)
            success = success and email_sent
        
        if customer_telegram_id:
            telegram_sent = await self.send_telegram_message(customer_telegram_id, telegram_message)
            success = success and telegram_sent
        
        return success
    
    async def notify_payment_confirmed(self, order_data: Dict[str, Any]) -> bool:
        """Notify customer that payment has been confirmed"""
        customer_email = order_data.get('customer_email')
        customer_telegram_id = order_data.get('customer_telegram_id')
        order_number = order_data.get('order_number')
        customer_language = order_data.get('customer_language', 'en')
        
        # Prepare messages
        if customer_language == 'ar':
            subject = f"تم تأكيد الدفع - {order_number}"
            email_message = f"""
مرحباً،

تم تأكيد دفعة طلبك {order_number} بنجاح!

سنبدأ العمل على طلبك قريباً وسنرسل لك تحديثات منتظمة.

شكراً لاختيارك خدماتنا الطلابية.

مع أطيب التحيات،
فريق الخدمات الطلابية
"""
            telegram_message = f"✅ تم تأكيد دفعة طلبك {order_number} بنجاح! سنبدأ العمل عليه قريباً."
        else:
            subject = f"Payment Confirmed - {order_number}"
            email_message = f"""
Hello,

Your payment for order {order_number} has been confirmed successfully!

We will start working on your order soon and will send you regular updates.

Thank you for choosing our student services.

Best regards,
Student Services Team
"""
            telegram_message = f"✅ Your payment for order {order_number} has been confirmed! We will start working on it soon."
        
        # Send notifications
        success = True
        
        if customer_email:
            email_sent = await self.send_email(customer_email, subject, email_message)
            success = success and email_sent
        
        if customer_telegram_id:
            telegram_sent = await self.send_telegram_message(customer_telegram_id, telegram_message)
            success = success and telegram_sent
        
        return success
