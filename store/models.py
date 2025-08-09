from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.messages import constants as message_constants
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib import messages
from django.db.models import Avg

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=10, 
        choices=[
            ('gender', 'Gender Category'),
            ('regular', 'Regular Category')
        ],
        default='regular',
        help_text="Whether this is a gender category (Men, Women, Kids, Unisex) or a regular category"
    )
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_categories',
                              help_text="Parent category (only for regular categories)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name
        
    def clean(self):
        # Ensure gender categories don't have parents
        if self.type == 'gender' and self.parent:
            raise ValidationError({'parent': 'Gender categories cannot have parent categories.'})
        
        # Ensure regular categories have parent gender categories
        if self.type == 'regular' and (not self.parent or self.parent.type != 'gender'):
            raise ValidationError({'parent': 'Regular categories must have a gender category as parent.'})

class Season(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    def __str__(self):
        return self.name

class Size(models.Model):
    """Model to represent clothing sizes"""
    SIZE_CHOICES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
        ('XXXL', 'Triple Extra Large'),
    ]
    
    name = models.CharField(max_length=10, choices=SIZE_CHOICES, unique=True)
    description = models.CharField(max_length=50, blank=True, help_text="Optional description for the size")
    sort_order = models.PositiveIntegerField(default=0, help_text="Order in which sizes should be displayed")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Size'
        verbose_name_plural = 'Sizes'
    
    def __str__(self):
        return self.get_name_display()

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price must be greater than or equal to 0.01"
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='products')
    sizes = models.ManyToManyField(Size, through='ProductSize', blank=True, help_text="Available sizes for this product")
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags for improved search (e.g. t-shirt,cotton,summer)")
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def tag_list(self):
        """Return tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]
    
    @property
    def available_sizes(self):
        """Return available sizes with stock information"""
        return self.product_sizes.filter(stock__gt=0).select_related('size')
    
    @property
    def total_stock(self):
        """Return total stock across all sizes"""
        return sum(ps.stock for ps in self.product_sizes.all())
    
    @property
    def average_rating(self):
        """Return average rating for this product"""
        avg = self.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return round(avg, 1) if avg else 0.0
    
    @property
    def rating_count(self):
        """Return total number of ratings for this product"""
        return self.ratings.count()
    
    @property
    def rating_distribution(self):
        """Return distribution of ratings (1-5 stars)"""
        distribution = {i: 0 for i in range(1, 6)}
        for rating in self.ratings.all():
            distribution[rating.rating] += 1
        return distribution
        
    def clean(self):
        # Ensure price is not negative
        if self.price is not None and self.price < Decimal('0.01'):
            raise ValidationError({'price': 'Price must be at least 0.01.'})
            
    def save(self, *args, **kwargs):
        # Ensure price is not negative
        if self.price is not None and self.price < Decimal('0.01'):
            self.price = Decimal('0.01')
        super().save(*args, **kwargs)

class ProductSize(models.Model):
    """Intermediate model to handle product sizes with individual stock"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_sizes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='product_sizes')
    stock = models.PositiveIntegerField(default=0, help_text="Stock available for this size")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'size']
        ordering = ['size__sort_order', 'size__name']
        verbose_name = 'Product Size'
        verbose_name_plural = 'Product Sizes'
    
    def __str__(self):
        return f"{self.product.name} - {self.size.name} (Stock: {self.stock})"

class Rating(models.Model):
    """Model to handle product ratings and reviews"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Rating from 1 to 5 stars")
    review = models.TextField(blank=True, help_text="Optional review text")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'product']  # One rating per user per product
        ordering = ['-created_at']
        verbose_name = 'Product Rating'
        verbose_name_plural = 'Product Ratings'
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('khalti', 'Khalti'),
        ('esewa', 'eSewa'),
        ('bank_transfer', 'Bank Transfer')
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # Shipping Information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    
    # Receiver Information (if different from shipping)
    receiver_name = models.CharField(max_length=100, blank=True, null=True)
    receiver_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Order Details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash_on_delivery')
    payment_status = models.BooleanField(default=False)
    order_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    is_received = models.BooleanField(default=False, help_text="Indicates if the customer has confirmed receipt of the order")
    received_at = models.DateTimeField(null=True, blank=True, help_text="When the customer confirmed receipt of the order")

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"

    class Meta:
        ordering = ['-created_at']
        
    def get_status_display(self):
        """Return the human-readable status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
        
    def get_payment_method_display(self):
        """Return the human-readable payment method"""
        return dict(self.PAYMENT_CHOICES).get(self.payment_method, self.payment_method)
        
    @property
    def can_cancel(self):
        """Check if the order can be cancelled by the user (within 30 minutes of creation)"""
        if self.status in ['cancelled', 'shipped', 'delivered']:
            return False
        time_elapsed = timezone.now() - self.created_at
        return time_elapsed <= timedelta(minutes=30)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # Store the name in case product is deleted
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True)
    size_name = models.CharField(max_length=10, blank=True)  # Store size name in case size is deleted
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        size_info = f" ({self.size_name})" if self.size_name else ""
        return f"{self.quantity}x {self.product_name}{size_info} in Order #{self.order.id}"

    @property
    def subtotal(self):
        return self.price * self.quantity

class OrderStatusHistory(models.Model):
    """Track history of order status changes"""
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order status history"
    
    def __str__(self):
        return f"Order #{self.order.id} changed to {self.get_status_display()}"
    
    def get_status_display(self):
        """Return the human-readable status"""
        return dict(Order.STATUS_CHOICES).get(self.status, self.status)

# We'll keep Cart and CartItem models for the shopping cart functionality,
# but they won't be exposed in the admin interface
class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id}"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'size']  # Prevent duplicate items with same product and size

    def __str__(self):
        size_info = f" ({self.size.name})" if self.size else ""
        return f"{self.quantity}x {self.product.name}{size_info}"

    @property
    def subtotal(self):
        return self.quantity * self.product.price

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist"

    class Meta:
        unique_together = ['user']

class UserMessage(models.Model):
    """Store messages for users that will be shown on their next login"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    level = models.IntegerField(choices=[
        (messages.DEBUG, 'DEBUG'),
        (messages.INFO, 'INFO'),
        (messages.SUCCESS, 'SUCCESS'),
        (messages.WARNING, 'WARNING'),
        (messages.ERROR, 'ERROR'),
    ], default=messages.INFO)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message for {self.user.username} ({self.get_level_display()})"

@receiver(pre_delete, sender=Order)
def notify_user_on_order_delete(sender, instance, **kwargs):
    """Notify user when their order is deleted by admin"""
    if instance.user and instance.status != 'cancelled':
        UserMessage.objects.create(
            user=instance.user,
            message=f"Your order #{instance.id} has been cancelled by the store. Please contact customer support for more information.",
            level=messages.WARNING
        )
        
        # Return items to inventory if order was deleted and not already cancelled
        if instance.status != 'cancelled':
            for item in instance.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()


class ContactMessage(models.Model):
    """Model for storing contact messages from anonymous users"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_replied = models.BooleanField(default=False)
    admin_reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_replies')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


class UserMessageReply(models.Model):
    """Model for admin replies to user messages"""
    original_message = models.ForeignKey(UserMessage, on_delete=models.CASCADE, related_name='replies')
    reply_message = models.TextField()
    replied_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Message Reply'
        verbose_name_plural = 'Message Replies'
    
    def __str__(self):
        return f"Reply to {self.original_message.user.username} by {self.replied_by.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Create a new UserMessage for the user to see the reply
        UserMessage.objects.create(
            user=self.original_message.user,
            message=f"Reply to your message: {self.original_message.message[:50]}...\n\nAdmin Reply:\n{self.reply_message}",
            level=messages.INFO
        )
