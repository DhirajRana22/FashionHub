# Khalti Integration Test Guide

## Issues Fixed

### 1. Configuration Issues
- ✅ **Secret Key**: Updated from placeholder to test secret key
- ✅ **Base URL**: Fixed URL consistency between settings and implementation
- ✅ **Error Handling**: Added proper validation and error messages

### 2. Code Improvements
- ✅ **Input Validation**: Added validation for customer info and order amount
- ✅ **Dynamic URLs**: Fixed hardcoded URLs to use dynamic generation
- ✅ **Enhanced Logging**: Improved logging with formatters and proper file handling
- ✅ **API Payload**: Enhanced payload with additional required fields

## Test Credentials (Sandbox)

```
Secret Key: 05bf95cc57244045b8df5fad06748dab (Test)
Base URL: https://dev.khalti.com/api/v2
```

## Testing Steps

### 1. Basic Functionality Test
1. Navigate to the website: `http://127.0.0.1:8000/`
2. Add products to cart
3. Go to checkout page
4. Fill in shipping information
5. Select "Khalti" as payment method
6. Click "Place Order"

### 2. Expected Behavior
- ✅ No more "Payment initiation failed" error
- ✅ Should redirect to Khalti payment page
- ✅ Proper error messages for validation failures
- ✅ Logging entries in `logs/khalti.log`

### 3. Test Scenarios

#### Scenario A: Successful Payment Flow
1. Complete checkout with valid information
2. Should redirect to Khalti sandbox payment page
3. Complete payment on Khalti
4. Should return to success page

#### Scenario B: Missing Information
1. Try checkout with missing email/phone
2. Should show validation error message
3. Order should not be created

#### Scenario C: Invalid Amount
1. Try with zero or negative amount
2. Should show amount validation error

## Khalti Test Payment Details

For testing on Khalti sandbox, you can use:
- **Test Khalti ID**: Any of the provided test IDs (9800000000, 9800000001, etc.)
- **Test MPIN**: 1111
- **Test OTP**: 987654

## Log Monitoring

Check the log file for detailed information:
```bash
tail -f logs/khalti.log
```

Log entries will show:
- Payment initiation attempts
- API responses from Khalti
- Validation errors
- Success/failure status

## Troubleshooting

### Common Issues
1. **"Khalti secret key must be configured"**
   - Check if secret key is properly set in settings.py
   - Ensure it's not the placeholder value

2. **Network errors**
   - Check internet connectivity
   - Verify Khalti API endpoints are accessible

3. **Validation errors**
   - Ensure all required fields are filled
   - Check order amount is greater than 0

### Debug Mode
To enable more detailed logging, update settings.py:
```python
LOGGING['loggers']['store.khalti_payment']['level'] = 'DEBUG'
```

## Production Deployment Notes

When deploying to production:
1. Replace test secret key with production key
2. Update base URL to production endpoint
3. Use environment variables for sensitive data
4. Enable HTTPS for secure communication
5. Set up proper error monitoring

## API Documentation Reference

- Khalti Documentation: https://docs.khalti.com/
- Web Checkout Guide: https://docs.khalti.com/checkout/web/
- API Reference: https://docs.khalti.com/api/