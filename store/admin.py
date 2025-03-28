from django.contrib import admin
from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Category, Season, Product, 
    UserProfile, Order, OrderItem, Wishlist, UserMessage, Cart, CartItem, OrderStatusHistory
)
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'price': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'})
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < Decimal('0.01'):
            raise forms.ValidationError("Price must be at least 0.01.")
        return price

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'subtotal')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'category', 'season', 'price', 'stock', 'featured', 'created_at')
    list_filter = ('category', 'season', 'featured')
    search_fields = ('name', 'description', 'tags')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'price', 'stock', 'image', 'tags', 'featured')
        }),
        ('Categories', {
            'fields': ('category', 'season')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Validate price is not negative"""
        if obj.price is not None and obj.price < Decimal('0.01'):
            obj.price = Decimal('0.01')
            messages.warning(request, "Price was set to the minimum value of 0.01")
        super().save_model(request, obj, form, change)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'parent', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('type', 'parent')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'type')
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': 'For regular categories, select a gender category as parent'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Season Information', {
            'fields': ('name', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_count', 'created_at')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('products',)
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'

@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'level', 'created_at', 'read')
    list_filter = ('level', 'read', 'created_at')
    search_fields = ('user__username', 'user__email', 'message')
    list_per_page = 20
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = "Mark selected messages as read"

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'order__full_name', 'created_by__username', 'notes')
    readonly_fields = ('order', 'status', 'created_by', 'created_at', 'notes')
    list_per_page = 20
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'user', 'total_amount', 'status_colored', 'payment_method', 
                  'payment_status', 'created_at', 'action_buttons')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'status_history_display')
    inlines = [OrderItemInline]
    actions = ['mark_as_processing', 'mark_as_packed', 'mark_as_shipped', 'mark_as_out_for_delivery', 'mark_as_delivered', 'mark_as_paid', 'mark_as_cancelled']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'full_name', 'email', 'phone')
        }),
        ('Shipping Information', {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        ('Receiver Information', {
            'fields': ('receiver_name', 'receiver_phone'),
            'classes': ('collapse',)
        }),
        ('Order Details', {
            'fields': ('total_amount', 'status', 'payment_method', 'payment_status', 
                     'order_notes', 'cancellation_reason')
        }),
        ('Status History', {
            'fields': ('status_history_display',),
        }),
        ('Receipt Status', {
            'fields': ('is_received', 'received_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/update-status/<str:status>/',
                 self.admin_site.admin_view(self.process_status_update),
                 name='store_order_status_update'),
            path('<path:object_id>/mark-as-paid/',
                 self.admin_site.admin_view(self.process_payment_update),
                 name='store_order_payment_update'),
        ]
        return custom_urls + urls
    
    def process_status_update(self, request, object_id, status):
        """Process a status update from the change form button"""
        order = get_object_or_404(Order, pk=object_id)
        
        # Map status to action function
        status_actions = {
            'processing': self.mark_as_processing,
            'packed': self.mark_as_packed,
            'shipped': self.mark_as_shipped,
            'out_for_delivery': self.mark_as_out_for_delivery,
            'delivered': self.mark_as_delivered,
            'cancelled': self.mark_as_cancelled
        }
        
        # Get the action function
        action_func = status_actions.get(status)
        if action_func:
            # Create a queryset with just this order
            queryset = Order.objects.filter(pk=object_id)
            # Call the action function
            action_func(request, queryset)
        
        return HttpResponseRedirect(
            reverse('admin:store_order_change', args=[object_id])
        )
    
    def process_payment_update(self, request, object_id):
        """Process a payment update from the change form button"""
        # Create a queryset with just this order
        queryset = Order.objects.filter(pk=object_id)
        # Call the mark_as_paid action
        self.mark_as_paid(request, queryset)
        
        return HttpResponseRedirect(
            reverse('admin:store_order_change', args=[object_id])
        )
    
    def status_colored(self, obj):
        """Display status with color coding"""
        status_colors = {
            'pending': 'gray',
            'processing': 'blue',
            'packed': 'purple',
            'shipped': 'orange',
            'out_for_delivery': 'teal',
            'delivered': 'green',
            'cancelled': 'red'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 5px; border-radius: 5px;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = "Status"
    status_colored.admin_order_field = 'status'
    
    def status_history_display(self, obj):
        """Display the status history in the admin panel"""
        if not obj.pk:
            return "Status history will be available after saving"
        
        history = obj.status_history.all()
        if not history:
            return "No status changes recorded"
        
        html = '<table style="width:100%; border-collapse: collapse;">'
        html += '<tr><th style="border:1px solid #ddd; padding:8px; text-align:left;">Date</th>'
        html += '<th style="border:1px solid #ddd; padding:8px; text-align:left;">Status</th>'
        html += '<th style="border:1px solid #ddd; padding:8px; text-align:left;">By</th>'
        html += '<th style="border:1px solid #ddd; padding:8px; text-align:left;">Notes</th></tr>'
        
        for entry in history:
            html += f'<tr>'
            html += f'<td style="border:1px solid #ddd; padding:8px;">{entry.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            html += f'<td style="border:1px solid #ddd; padding:8px;">{entry.get_status_display()}</td>'
            html += f'<td style="border:1px solid #ddd; padding:8px;">{entry.created_by.username if entry.created_by else "System"}</td>'
            html += f'<td style="border:1px solid #ddd; padding:8px;">{entry.notes}</td>'
            html += f'</tr>'
        
        html += '</table>'
        return format_html(html)
    status_history_display.short_description = "Status History"
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Create status history entry
                OrderStatusHistory.objects.create(
                    order=obj,
                    status=obj.status,
                    created_by=request.user,
                    notes=f"Status changed from {dict(Order.STATUS_CHOICES).get(old_obj.status)} to {dict(Order.STATUS_CHOICES).get(obj.status)}"
                )
                
                # Create user notification
                status_messages = {
                    'pending': 'Your order has been received and is pending processing.',
                    'processing': 'Great news! Your order #{} is now being processed. Our team is working on preparing your items.',
                    'packed': 'Your order #{} has been carefully packed and is ready for shipping! It will be handed over to our delivery partner soon.',
                    'shipped': 'Your order #{} has been shipped! Your package is on its way to you. You can track its journey in your account.',
                    'out_for_delivery': 'Exciting news! Your order #{} is out for delivery today. Please ensure someone is available to receive it.',
                    'delivered': 'Your order #{} has been delivered. We hope you love your purchase! Please confirm receipt in your account.',
                    'cancelled': 'Your order #{} has been cancelled as requested. If you have any questions, please contact our customer support.'
                }
                message_template = status_messages.get(obj.status, f'Your order #{obj.id} status has been updated to {obj.get_status_display()}.')
                message = message_template.format(obj.id)
                
                if obj.user:
                    UserMessage.objects.create(
                        user=obj.user,
                        message=message,
                        level=messages.INFO if obj.status in ['pending', 'processing', 'packed'] else 
                              messages.SUCCESS if obj.status in ['shipped', 'out_for_delivery', 'delivered'] else
                              messages.WARNING
                    )
        super().save_model(request, obj, form, change)
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='processing')
        for order in queryset.filter(status='processing'):
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='processing',
                created_by=request.user,
                notes="Status changed to Processing via admin action"
            )
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Great news! Your order #{order.id} is now being processed. Our team is working on preparing your items.',
                    level=messages.INFO
                )
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def mark_as_packed(self, request, queryset):
        updated = queryset.filter(status='processing').update(status='packed')
        for order in queryset.filter(status='packed'):
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='packed',
                created_by=request.user,
                notes="Status changed to Packed via admin action"
            )
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Your order #{order.id} has been carefully packed and is ready for shipping! It will be handed over to our delivery partner soon.',
                    level=messages.INFO
                )
        self.message_user(request, f'{updated} order(s) marked as packed.')
    mark_as_packed.short_description = "Mark selected orders as packed"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status__in=['processing', 'packed']).update(status='shipped')
        for order in queryset.filter(status='shipped'):
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='shipped',
                created_by=request.user,
                notes="Status changed to Shipped via admin action"
            )
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Your order #{order.id} has been shipped! Your package is on its way to you. You can track its journey in your account.',
                    level=messages.SUCCESS
                )
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_out_for_delivery(self, request, queryset):
        updated = queryset.filter(status='shipped').update(status='out_for_delivery')
        for order in queryset.filter(status='out_for_delivery'):
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='out_for_delivery',
                created_by=request.user,
                notes="Status changed to Out for Delivery via admin action"
            )
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Exciting news! Your order #{order.id} is out for delivery today. Please ensure someone is available to receive it.',
                    level=messages.SUCCESS
                )
        self.message_user(request, f'{updated} order(s) marked as out for delivery.')
    mark_as_out_for_delivery.short_description = "Mark selected orders as out for delivery"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.filter(status__in=['shipped', 'out_for_delivery']).update(status='delivered')
        for order in queryset.filter(status='delivered'):
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='delivered',
                created_by=request.user,
                notes="Status changed to Delivered via admin action"
            )
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Your order #{order.id} has been delivered. We hope you love your purchase! Please confirm receipt in your account.',
                    level=messages.SUCCESS
                )
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status=True)
        for order in queryset.filter(payment_status=True):
            # Create note in status history
            OrderStatusHistory.objects.create(
                order=order,
                status=order.status,
                created_by=request.user,
                notes="Payment marked as received via admin action"
            )
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Thank you! Payment for order #{order.id} has been received. Your purchase is confirmed!',
                    level=messages.SUCCESS
                )
        self.message_user(request, f'Payment status updated for {updated} order(s).')
    mark_as_paid.short_description = "Mark selected orders as paid"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark orders as cancelled"""
        updated = queryset.exclude(status__in=['delivered', 'cancelled']).update(status='cancelled')
        for order in queryset.filter(status='cancelled'):
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                created_by=request.user,
                notes="Status changed to Cancelled via admin action"
            )
            
            # Return items to inventory
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()
            
            # Notify user
            if order.user:
                UserMessage.objects.create(
                    user=order.user,
                    message=f'Your order #{order.id} has been cancelled. If you have any questions, please contact our customer support.',
                    level=messages.WARNING
                )
        self.message_user(request, f'{updated} order(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"

    def action_buttons(self, obj):
        """Display action buttons for status updates in the list view"""
        # Define available transitions based on current status
        status_transitions = {
            'pending': ['processing'],
            'processing': ['packed', 'cancelled'],
            'packed': ['shipped', 'cancelled'],
            'shipped': ['out_for_delivery', 'cancelled'],
            'out_for_delivery': ['delivered', 'cancelled'],
            'delivered': [],  # No transitions from delivered
            'cancelled': []   # No transitions from cancelled
        }
        
        available_transitions = status_transitions.get(obj.status, [])
        buttons = []
        
        for status in available_transitions:
            status_display = dict(Order.STATUS_CHOICES).get(status)
            status_colors = {
                'pending': 'gray',
                'processing': 'blue',
                'packed': 'purple',
                'shipped': 'orange',
                'out_for_delivery': 'teal',
                'delivered': 'green',
                'cancelled': 'red'
            }
            color = status_colors.get(status, 'black')
            
            url = reverse('admin:store_order_status_update', args=[obj.pk, status])
            buttons.append(
                f'<a href="{url}" '
                f'onclick="return confirm(\'Are you sure you want to change status to {status_display}?\');" '
                f'style="display: inline-block; margin: 2px; padding: 3px 8px; background-color: {color}; '
                f'color: white; text-decoration: none; border-radius: 3px; font-size: 0.8em;">'
                f'{status_display}</a>'
            )
        
        # Payment button
        if not obj.payment_status:
            url = reverse('admin:store_order_payment_update', args=[obj.pk])
            buttons.append(
                f'<a href="{url}" '
                f'onclick="return confirm(\'Are you sure you want to mark this order as paid?\');" '
                f'style="display: inline-block; margin: 2px; padding: 3px 8px; background-color: green; '
                f'color: white; text-decoration: none; border-radius: 3px; font-size: 0.8em;">'
                f'Mark Paid</a>'
            )
        
        if buttons:
            return format_html(''.join(buttons))
        return "No actions available"
    
    action_buttons.short_description = "Actions"
    action_buttons.allow_tags = True

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'subtotal')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
