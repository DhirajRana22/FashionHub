import requests
import json
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class KhaltiPayment:
    """
    Khalti Payment Gateway Integration
    Based on Khalti Web Checkout (KPG-2) documentation
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'KHALTI_BASE_URL', 'https://dev.khalti.com/api/v2')
        self.secret_key = getattr(settings, 'KHALTI_SECRET_KEY', '')
        
        if not self.secret_key or self.secret_key == 'your_khalti_secret_key_here':
            logger.error("Khalti secret key not properly configured in settings")
            raise ValueError("Khalti secret key must be configured")
    
    def initiate_payment(self, order, request):
        """
        Initiate payment with Khalti
        
        Args:
            order: Order instance
            request: Django request object
            
        Returns:
            dict: Response from Khalti API containing payment_url and pidx
        """
        
        # Validate required order data
        if not order.email or not order.phone or not order.full_name:
            logger.error(f"Missing required customer information for order {order.id}")
            return {
                'success': False,
                'error': 'Missing required customer information (name, email, phone)'
            }
        
        # Validate amount
        if order.total_amount <= 0:
            logger.error(f"Invalid order amount for order {order.id}: {order.total_amount}")
            return {
                'success': False,
                'error': 'Invalid order amount'
            }
        
        # Convert amount to paisa (multiply by 100)
        amount_in_paisa = int(order.total_amount * 100)
        
        # Build return URL
        return_url = request.build_absolute_uri(
            reverse('store:khalti_callback')
        )
        
        # Build website URL
        website_url = request.build_absolute_uri('/')
        
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount_in_paisa,
            "purchase_order_id": str(order.id),
            "purchase_order_name": f"FashionHub Order #{order.id}",
            "customer_info": {
                "name": order.full_name,
                "email": order.email,
                "phone": order.phone
            },
            "amount_breakdown": [
                {
                    "label": "Total Amount",
                    "amount": amount_in_paisa
                }
            ],
            "product_details": self._get_product_details(order),
            "merchant_username": "fashionhub",
            "merchant_extra": f"order_{order.id}"
        }
        
        headers = {
            "Authorization": f"Key {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/epayment/initiate/",
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Khalti payment initiated for order {order.id}: {data}")
                return {
                    'success': True,
                    'payment_url': data.get('payment_url'),
                    'pidx': data.get('pidx'),
                    'data': data
                }
            else:
                logger.error(f"Khalti payment initiation failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Payment initiation failed: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti API request failed: {str(e)}")
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
    
    def verify_payment(self, pidx):
        """
        Verify payment status with Khalti
        
        Args:
            pidx: Payment identifier from Khalti
            
        Returns:
            dict: Payment verification response
        """
        
        payload = {
            "pidx": pidx
        }
        
        headers = {
            "Authorization": f"Key {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/epayment/lookup/",
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Khalti payment verification response: {data}")
                return {
                    'success': True,
                    'data': data
                }
            else:
                logger.error(f"Khalti payment verification failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Payment verification failed: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti verification request failed: {str(e)}")
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
    
    def _get_product_details(self, order):
        """
        Get product details for Khalti payload
        
        Args:
            order: Order instance
            
        Returns:
            list: Product details for Khalti
        """
        product_details = []
        
        for item in order.items.all():
            product_details.append({
                "identity": str(item.product.id) if item.product else "deleted",
                "name": item.product_name,
                "total_price": int(item.subtotal * 100),  # Convert to paisa
                "quantity": item.quantity,
                "unit_price": int(item.price * 100)  # Convert to paisa
            })
        
        return product_details