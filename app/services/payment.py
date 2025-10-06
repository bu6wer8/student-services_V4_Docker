# File: app/services/payment.py
import stripe
from config.config import settings
import logging
from typing import Optional, Dict
from app.models.database import SessionLocal
from app.models.models import Order

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key

class PaymentService:
    def __init__(self):
        self.stripe_key = settings.stripe_secret_key
        stripe.api_key = self.stripe_key
    
    def create_payment_link(
        self, 
        order_id: int, 
        amount: float, 
        currency: str, 
        description: str,
        customer_email: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """Create a Stripe checkout session"""
        try:
            currency_code = currency.lower()
            
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price_data': {
                        'currency': currency_code,
                        'product_data': {
                            'name': description,
                            'description': f'Order #{order_id}',
                        },
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': f'https://t.me/{settings.telegram_bot_token.split(":")[0]}?start=payment_success_{order_id}',
                'cancel_url': f'https://t.me/{settings.telegram_bot_token.split(":")[0]}?start=payment_cancel_{order_id}',
                'metadata': {
                    'order_id': str(order_id),
                    'type': 'student_service_order'
                }
            }
            
            if customer_email:
                session_params['customer_email'] = customer_email
            
            session = stripe.checkout.Session.create(**session_params)
            logger.info(f"Created payment session {session.id} for order {order_id}")

            # Save session ID to the order in database
            db = SessionLocal()
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.stripe_session_id = session.id
                db.commit()
            db.close()

            return {'id': session.id, 'url': session.url}
            
        except Exception as e:
            logger.error(f"Error creating payment link: {e}")
            return None
    
    def verify_payment(self, session_id: str) -> Dict:
        """Verify payment status"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'paid': session.payment_status == 'paid',
                'amount': session.amount_total / 100 if session.amount_total else 0,
                'currency': session.currency,
                'payment_intent': session.payment_intent
            }
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return {'paid': False}
    
    def create_refund(self, payment_intent_id: str, amount: Optional[float] = None) -> Dict:
        """Create a refund for a payment"""
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount:
                refund_params['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount / 100
            }
        except Exception as e:
            logger.error(f"Error creating refund: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_bank_transfer_details(self, order_number: str, amount: float, currency: str) -> str:
        """Get bank transfer details formatted message"""
        bank_details = f"""
🏦 **Bank Transfer Details:**

**Bank Name:** {settings.bank_name}
**Account Name:** {settings.bank_account_name}
**Account Number:** {settings.bank_account_number}
**IBAN:** {settings.bank_iban}
**Swift Code:** {settings.bank_swift}

**Amount:** {amount} {currency}
**Reference:** {order_number}

⚠️ **Important:**
1. Use order number as reference
2. Send transfer receipt after payment
3. Processing takes 1-2 hours after receipt

Please upload your transfer receipt using the button below.
"""
        return bank_details

    def check_payment_status_by_order(self, order_id: int) -> str:
        """
        Check payment status for an order.
        Returns: 'pending', 'succeeded', 'failed', or 'error'
        """
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return "Order not found"

            if order.payment_method != "stripe":
                return "Not a Stripe order"

            session_id = getattr(order, "stripe_session_id", None)
            if not session_id:
                return "No session ID found"

            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                # Update order in DB
                order.payment_status = "confirmed"
                order.status = "paid"
                db.commit()
                return "succeeded"
            elif session.payment_status == "unpaid":
                return "pending"
            else:
                return "failed"
        except Exception as e:
            logger.error(f"Error checking payment status for order {order_id}: {e}")
            return "error"
        finally:
            db.close()
