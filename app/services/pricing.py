# File: app/services/pricing.py
from config.config import settings
from typing import Dict

class PricingService:
    def __init__(self):
        self.base_prices = {
            'assignment': settings.base_price_assignment,
            'project': settings.base_price_project,
            'presentation': settings.base_price_presentation,
            'redesign': 25,
            'summary': 15,
            'express': 50
        }
        
        self.academic_multipliers = {
            'high_school': 1.0,
            'bachelor': 1.2,
            'masters': 1.5,
            'phd': 2.0
        }
        
        self.currency_rates = {
            'USD': 1.0,
            'JOD': 0.71,
            'AED': 3.67,
            'SAR': 3.75
        }
    
    def calculate_price(
        self, 
        service_type: str, 
        academic_level: str, 
        days_until_deadline: int, 
        currency: str = 'USD'
    ) -> Dict:
        """Calculate price based on various factors"""
        
        # Get base price
        base_price = self.base_prices.get(service_type, 30)
        
        # Calculate urgency multiplier
        if days_until_deadline <= 1:
            urgency_multiplier = settings.urgency_multiplier_24h
        elif days_until_deadline <= 2:
            urgency_multiplier = 1.5
        elif days_until_deadline <= 3:
            urgency_multiplier = 1.3
        elif days_until_deadline <= 5:
            urgency_multiplier = 1.1
        else:
            urgency_multiplier = 1.0
        
        # Get academic level multiplier
        academic_multiplier = self.academic_multipliers.get(academic_level, 1.0)
        
        # Calculate total in USD
        total_price_usd = base_price * urgency_multiplier * academic_multiplier
        
        # Convert to requested currency
        if currency != 'USD':
            currency_rate = self.currency_rates.get(currency, 1.0)
            total_price = total_price_usd * currency_rate
        else:
            total_price = total_price_usd
        
        return {
            'base_price': round(base_price, 2),
            'urgency_multiplier': urgency_multiplier,
            'academic_multiplier': academic_multiplier,
            'total_price': round(total_price, 2),
            'total_price_usd': round(total_price_usd, 2),
            'currency': currency
        }
    
    def format_price_breakdown(self, price_details: Dict) -> str:
        """Format price breakdown for display"""
        breakdown = f"""
💰 **Price Breakdown:**
Base Price: {price_details['base_price']} USD
Urgency: x{price_details['urgency_multiplier']}
Academic Level: x{price_details['academic_multiplier']}
─────────────────
**Total: {price_details['total_price']} {price_details['currency']}**
"""
        if price_details['currency'] != 'USD':
            breakdown += f"(${price_details['total_price_usd']} USD)"
        
        return breakdown