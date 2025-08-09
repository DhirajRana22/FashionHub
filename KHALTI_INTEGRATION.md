 # Khalti Payment Gateway Integration

This document explains how to set up and use the Khalti payment gateway integration in FashionHub.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install requests
```

### 2. Configure Khalti Settings

Update `ecommerce/settings.py` with your Khalti credentials:

```python
# Khalti Payment Gateway Settings
KHALTI_SECRET_KEY = 'your_actual_khalti_secret_key'  # Replace with your secret key
KHALTI_BASE_URL = 'https://a.khalti.com/api/v2/epayment/'
```

### 3. Test Credentials (Sandbox)

For testing purposes, you can use Khalti's test credentials:
- Test Secret Key: Available in your Khalti merchant dashboard
- Test Public Key: Available in your Khalti merchant dashboard

## How It Works

### Payment Flow

1. **Checkout Process**: User selects Khalti as payment method on checkout page
2. **Payment Initiation**: System creates order and initiates Khalti payment
3. **Redirect to Khalti**: User is redirected to Khalti payment page
4. **Payment Processing**: User completes payment on Khalti
5. **Callback Handling**: Khalti redirects back to our callback URL
6. **Payment Verification**: System verifies payment with Khalti API
7. **Order Confirmation**: Order status is updated based on payment result

### Key Components

#### 1. KhaltiPayment Class (`store/khalti_payment.py`)
- Handles payment initiation and verification
- Communicates with Khalti API
- Logs all payment activities

#### 2. Checkout View (`store/views.py`)
- Modified to handle Khalti payment selection
- Creates order and initiates payment
- Stores session data for callback verification

#### 3. Callback View (`store/views.py`)
- Handles return from Khalti payment page
- Verifies payment status
- Updates order status accordingly
- Manages stock restoration on failed payments

### URL Configuration

- Checkout: `/store/checkout/`
- Khalti Callback: `/store/khalti-callback/`
- Order Success: `/store/order-success/<order_id>/`

## Testing

### Test Payment Flow

1. Add products to cart
2. Go to checkout page
3. Select "Khalti" as payment method
4. Fill in shipping details
5. Click "Place Order"
6. Complete payment on Khalti test environment
7. Verify order status in "My Orders"

### Test Scenarios

- **Successful Payment**: Complete payment flow
- **Failed Payment**: Cancel payment on Khalti page
- **Invalid Session**: Test with tampered session data
- **Amount Mismatch**: Verify amount validation

## Security Features

- Session-based payment tracking
- Payment amount verification
- PIDX validation
- Stock restoration on failed payments
- Comprehensive error handling
- Payment logging for audit trail

## Error Handling

- Invalid payment sessions
- Payment verification failures
- Network connectivity issues
- Amount mismatches
- Cancelled payments

## Logging

All Khalti payment activities are logged to `khalti_payments.log` for debugging and audit purposes.

## Production Deployment

### Important Notes

1. **Replace Test Credentials**: Use production Khalti credentials
2. **Update URLs**: Change return URLs to production domain
3. **SSL Certificate**: Ensure HTTPS is enabled
4. **Environment Variables**: Store sensitive keys in environment variables
5. **Error Monitoring**: Set up proper error monitoring and alerting

### Environment Variables (Recommended)

```python
import os

KHALTI_SECRET_KEY = os.environ.get('KHALTI_SECRET_KEY')
KHALTI_BASE_URL = os.environ.get('KHALTI_BASE_URL', 'https://a.khalti.com/api/v2/epayment/')
```

## Support

For Khalti-related issues:
- Khalti Documentation: https://docs.khalti.com/
- Khalti Support: support@khalti.com

For integration issues:
- Check logs in `khalti_payments.log`
- Verify API credentials
- Test network connectivity