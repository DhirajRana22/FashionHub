from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
import csv
import json
from .models import Product, Category, Season, Order, OrderItem, User, UserProfile, UserMessage, OrderStatusHistory, Size, ProductSize
from .forms import ProductForm, CategoryForm, SeasonForm, ProductSizeFormSet, UserForm, UserProfileForm

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with statistics and overview"""
    # Get statistics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_users = User.objects.filter(is_staff=False).count()
    total_revenue = Order.objects.filter(
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Low stock products (stock < 10)
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')[:5]
    
    # Sales data for chart (last 7 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)
    
    sales_data = []
    sales_labels = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        daily_sales = Order.objects.filter(
            created_at__date=date,
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        sales_data.append(float(daily_sales))
        sales_labels.append(date.strftime('%b %d'))
    
    # Order status data for pie chart
    order_status_data = []
    order_status_labels = []
    order_status_breakdown = []
    
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    for status in status_counts:
        order_status_labels.append(status['status'].title())
        order_status_data.append(status['count'])
        order_status_breakdown.append((status['status'], status['count']))
    
    # Additional metrics for enhanced dashboard
    total_week_sales = sum(sales_data)
    avg_daily_sales = total_week_sales / 7 if total_week_sales > 0 else 0
    best_day_sales = max(sales_data) if sales_data else 0
    
    # Calculate sales growth (compare with previous week)
    prev_week_start = start_date - timedelta(days=7)
    prev_week_end = start_date - timedelta(days=1)
    prev_week_sales = Order.objects.filter(
        created_at__date__range=[prev_week_start, prev_week_end],
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    if prev_week_sales > 0:
        sales_growth = ((total_week_sales - float(prev_week_sales)) / float(prev_week_sales)) * 100
    else:
        sales_growth = 100 if total_week_sales > 0 else 0
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'sales_data': json.dumps(sales_data),
        'sales_labels': json.dumps(sales_labels),
        'order_status_data': json.dumps(order_status_data),
        'order_status_labels': json.dumps(order_status_labels),
        'order_status_breakdown': order_status_breakdown,
        'total_week_sales': total_week_sales,
        'avg_daily_sales': avg_daily_sales,
        'best_day_sales': best_day_sales,
        'sales_growth': sales_growth,
    }
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_products(request):
    """Product management page"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    season_filter = request.GET.get('season', '')
    
    products = Product.objects.select_related('category', 'season').all()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if season_filter:
        products = products.filter(season_id=season_filter)
    
    products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories and seasons for filters
    categories = Category.objects.all().order_by('name')
    seasons = Season.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'season_filter': season_filter,
        'categories': categories,
        'seasons': seasons,
    }
    
    return render(request, 'admin/products.html', context)

@staff_member_required
def admin_product_add(request):
    """Add new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        size_formset = ProductSizeFormSet(request.POST)
        
        if form.is_valid() and size_formset.is_valid():
            product = form.save()
            size_formset.instance = product
            size_formset.save()
            messages.success(request, 'Product added successfully!')
            return redirect('custom_admin:products')
    else:
        form = ProductForm()
        size_formset = ProductSizeFormSet()
    
    # Get all available sizes for the template
    available_sizes = Size.objects.all().order_by('sort_order', 'name')
    
    return render(request, 'admin/product_form.html', {
        'form': form,
        'size_formset': size_formset,
        'available_sizes': available_sizes,
        'title': 'Add New Product'
    })

@staff_member_required
def admin_product_edit(request, pk):
    """Edit existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        size_formset = ProductSizeFormSet(request.POST, instance=product)
        
        if form.is_valid() and size_formset.is_valid():
            form.save()
            size_formset.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('custom_admin:products')
    else:
        form = ProductForm(instance=product)
        size_formset = ProductSizeFormSet(instance=product)
    
    # Get all available sizes for the template
    available_sizes = Size.objects.all().order_by('sort_order', 'name')
    
    return render(request, 'admin/product_form.html', {
        'form': form,
        'size_formset': size_formset,
        'available_sizes': available_sizes,
        'product': product,
        'title': 'Edit Product'
    })

@staff_member_required
def admin_product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('custom_admin:products')
    
    return render(request, 'admin/confirm_delete.html', {
        'object': product,
        'object_type': 'Product'
    })

@staff_member_required
def admin_orders(request):
    """Order management page"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    orders = Order.objects.select_related('user').all()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    orders = orders.order_by('-created_at')
    
    # Calculate statistics from real data
    all_orders = Order.objects.all()
    total_orders = all_orders.count()
    pending_orders = all_orders.filter(status='pending').count()
    completed_orders = all_orders.filter(status='delivered').count()
    total_revenue = all_orders.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get order statuses for filter
    order_statuses = Order.objects.values_list('status', flat=True).distinct()
    
    context = {
        'orders': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'status_filter': status_filter,
        'search_query': search_query,
        'order_statuses': order_statuses,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'admin/orders.html', context)

@staff_member_required
def admin_order_detail(request, pk):
    """Order detail and management"""
    order = get_object_or_404(Order, pk=pk)
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    status_history = OrderStatusHistory.objects.filter(order=order).order_by('-created_at')
    
    if request.method == 'POST':
        # Handle payment status update for COD orders
        if 'payment_received' in request.POST:
            if order.payment_method == 'cash_on_delivery' and order.status == 'delivered' and not order.payment_status:
                order.payment_status = True
                order.save()
                
                # Create status history entry for payment received
                OrderStatusHistory.objects.create(
                    order=order,
                    status=order.status,
                    created_by=request.user,
                    notes='Payment received for COD order'
                )
                
                # Send notification to user
                if order.user:
                    UserMessage.objects.create(
                        user=order.user,
                        message=f'Payment for your order #{order.id} has been confirmed as received. Thank you!',
                        level=messages.SUCCESS
                    )
                
                messages.success(request, 'Payment marked as received successfully')
                return redirect('custom_admin:order_detail', pk=pk)
            else:
                messages.error(request, 'Payment can only be marked as received for delivered COD orders')
                return redirect('custom_admin:order_detail', pk=pk)
        
        new_status = request.POST.get('status')
        if new_status and new_status != order.status:
            # Define valid status transitions
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['processing', 'cancelled'],
                'processing': ['packed', 'cancelled'],
                'packed': ['shipped', 'cancelled'],
                'shipped': ['delivered', 'cancelled'],
                'delivered': [],  # Final status
                'cancelled': []   # Final status
            }
            
            # Check if the transition is valid
            if new_status in valid_transitions.get(order.status, []):
                old_status = order.status
                order.status = new_status
                order.save()
                
                # Create status history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status=new_status,
                    created_by=request.user,
                    notes=request.POST.get('notes', '')
                )
                
                # Send notification to user
                if order.user:
                    status_messages = {
                        'confirmed': f'Your order #{order.id} has been confirmed and will be processed soon.',
                        'processing': f'Your order #{order.id} is now being processed.',
                        'packed': f'Your order #{order.id} has been packed and is ready for shipment.',
                        'shipped': f'Your order #{order.id} has been shipped and is on its way to you.',
                        'delivered': f'Your order #{order.id} has been delivered. Thank you for shopping with us!',
                        'cancelled': f'Your order #{order.id} has been cancelled.'
                    }
                    
                    message_text = status_messages.get(new_status, f'Your order #{order.id} status has been updated to {order.get_status_display()}.')
                    
                    UserMessage.objects.create(
                        user=order.user,
                        message=message_text,
                        level=messages.INFO if new_status != 'cancelled' else messages.WARNING
                    )
                
                messages.success(request, f'Order status updated to {new_status.title()}')
                return redirect('custom_admin:order_detail', pk=pk)
            else:
                messages.error(request, f'Invalid status transition from {order.get_status_display()} to {dict(Order.STATUS_CHOICES).get(new_status, new_status)}')
                return redirect('custom_admin:order_detail', pk=pk)
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/order_detail.html', context)

@staff_member_required
def admin_users(request):
    """User management page"""
    search_query = request.GET.get('search', '')
    
    users = User.objects.filter(is_staff=False).select_related('userprofile')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    users = users.order_by('-date_joined')
    
    # Calculate statistics
    total_users = User.objects.filter(is_staff=False).count()
    active_users = User.objects.filter(is_staff=False, is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    
    # New users this month
    from datetime import datetime
    current_month = datetime.now().month
    current_year = datetime.now().year
    new_users_this_month = User.objects.filter(
        is_staff=False,
        date_joined__month=current_month,
        date_joined__year=current_year
    ).count()
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'new_users_this_month': new_users_this_month,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'admin/users.html', context)

@staff_member_required
def admin_user_add(request):
    """Add new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                state=request.POST.get('state', ''),
                postal_code=request.POST.get('postal_code', '')
            )
            
            messages.success(request, f'User {username} created successfully!')
            return redirect('custom_admin:users')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return redirect('custom_admin:users')
    
    return redirect('custom_admin:users')

@staff_member_required
def admin_user_detail(request, pk):
    """User detail view"""
    user = get_object_or_404(User, pk=pk)
    
    # Get user's orders
    orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Calculate user statistics
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(
        user=user,
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get user's cart items (Cart model doesn't have user field, so we'll skip this)
    cart_items = []
    
    # Get user's wishlist items
    try:
        from .models import Wishlist
        user_wishlist = Wishlist.objects.filter(user=user).first()
        if user_wishlist:
            wishlist_items = user_wishlist.products.all()[:5]
        else:
            wishlist_items = []
    except:
        wishlist_items = []
    
    context = {
        'user': user,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'cart_items': cart_items,
        'wishlist_items': wishlist_items,
    }
    
    return render(request, 'admin/user_detail.html', context)

@staff_member_required
def admin_categories(request):
    """Category management page"""
    categories = Category.objects.annotate(
        total_inventory=Sum('products__stock')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin/categories.html', context)

@staff_member_required
def admin_category_add(request):
    """Add new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('custom_admin:categories')
    else:
        form = CategoryForm()
    
    return render(request, 'admin/category_form.html', {
        'form': form,
        'title': 'Add New Category'
    })

@staff_member_required
def admin_category_edit(request, pk):
    """Edit existing category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('custom_admin:categories')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'admin/category_form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category'
    })

@staff_member_required
def admin_seasons(request):
    """Season management page"""
    seasons = Season.objects.all().order_by('name')
    
    # Calculate statistics
    total_seasons = seasons.count()
    active_seasons = seasons.filter(products__isnull=False).distinct().count()
    products_with_seasons = Product.objects.filter(season__isnull=False).count()
    
    # For current season, we'll use the season with most recent products
    # or you can define logic based on actual current season
    current_season_products = 0
    if seasons.exists():
        # Get the season with the most products as "current"
        current_season = seasons.annotate(
            product_count=Count('products')
        ).order_by('-product_count').first()
        if current_season:
            current_season_products = current_season.products.count()
    
    context = {
        'seasons': seasons,
        'total_seasons': total_seasons,
        'active_seasons': active_seasons,
        'products_with_seasons': products_with_seasons,
        'current_season_products': current_season_products,
    }
    
    return render(request, 'admin/seasons.html', context)

@staff_member_required
def admin_season_add(request):
    """Add new season"""
    if request.method == 'POST':
        form = SeasonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Season added successfully!')
            return redirect('custom_admin:seasons')
    else:
        form = SeasonForm()
    
    return render(request, 'admin/season_form.html', {
        'form': form,
        'title': 'Add New Season'
    })

@staff_member_required
def admin_season_edit(request, pk):
    """Edit existing season"""
    season = get_object_or_404(Season, pk=pk)
    
    if request.method == 'POST':
        form = SeasonForm(request.POST, instance=season)
        if form.is_valid():
            form.save()
            messages.success(request, f'Season "{season.name}" updated successfully!')
            return redirect('custom_admin:seasons')
    else:
        form = SeasonForm(instance=season)
    
    return render(request, 'admin/season_form.html', {
        'form': form,
        'title': f'Edit Season - {season.name}',
        'season': season
    })

@staff_member_required
def admin_season_delete(request, pk):
    """Delete existing season"""
    season = get_object_or_404(Season, pk=pk)
    
    if request.method == 'POST':
        season_name = season.name
        # Check if season has associated products
        product_count = season.products.count()
        if product_count > 0:
            messages.error(request, f'Cannot delete season "{season_name}" because it has {product_count} associated products. Please reassign or delete those products first.')
        else:
            season.delete()
            messages.success(request, f'Season "{season_name}" deleted successfully!')
        return redirect('custom_admin:seasons')
    
    # If GET request, redirect back to seasons page
    return redirect('custom_admin:seasons')

@staff_member_required
def admin_messages(request):
    """User messages management"""
    messages_list = UserMessage.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'admin/messages.html', context)

@staff_member_required
def admin_analytics(request):
    """Analytics and reports page"""
    # Monthly sales data
    monthly_sales = []
    monthly_labels = []
    
    for i in range(12):
        date = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        month_start = date.replace(day=1)
        if i == 0:
            month_end = timezone.now().date()
        else:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_total = Order.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end,
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_sales.insert(0, float(monthly_total))
        monthly_labels.insert(0, month_start.strftime('%b %Y'))
    
    # Top selling products
    top_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__isnull=False).order_by('-total_sold')[:10]
    
    # Category wise sales
    category_sales = Category.objects.annotate(
        total_sales=Sum('products__orderitem__order__total_amount')
    ).filter(total_sales__isnull=False).order_by('-total_sales')[:5]
    
    context = {
        'monthly_sales': json.dumps(monthly_sales),
        'monthly_labels': json.dumps(monthly_labels),
        'top_products': top_products,
        'category_sales': category_sales,
    }
    
    return render(request, 'admin/analytics.html', context)

@staff_member_required
def admin_send_order_email(request, pk):
    """Send order confirmation email to customer"""
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        
        try:
            # Prepare email context
            context = {
                'order': order,
                'order_items': order.orderitem_set.all(),
                'site_name': 'FashionHub',
            }
            
            # Render email template
            subject = f'Order Confirmation - #{order.id}'
            html_message = render_to_string('emails/order_confirmation.html', context)
            plain_message = f'Your order #{order.id} has been confirmed. Total: Rs.{order.total_amount}'
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return JsonResponse({'success': True, 'message': 'Email sent successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def admin_order_invoice(request, pk):
    """Generate and display order invoice"""
    order = get_object_or_404(Order, pk=pk)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'company_name': 'FashionHub',
        'company_address': 'Kathmandu, Nepal',
        'company_phone': '+977-1-4444444',
        'company_email': 'info@fashionhub.com',
    }
    
    return render(request, 'admin/invoice.html', context)

@staff_member_required
def admin_export_order(request, pk):
    """Export order data as CSV"""
    order = get_object_or_404(Order, pk=pk)
    order_items = order.orderitem_set.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="order_{order.id}_export.csv"'
    
    writer = csv.writer(response)
    
    # Write order header
    writer.writerow(['Order Export - FashionHub'])
    writer.writerow(['Order ID', order.id])
    writer.writerow(['Customer', order.full_name])
    writer.writerow(['Email', order.email])
    writer.writerow(['Phone', order.phone])
    writer.writerow(['Order Date', order.created_at.strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Status', order.get_status_display()])
    writer.writerow(['Total Amount', f'Rs.{order.total_amount}'])
    writer.writerow([])
    
    # Write shipping address
    writer.writerow(['Shipping Address'])
    writer.writerow(['Address', order.address])
    writer.writerow(['City', order.city])
    writer.writerow(['State', order.state])
    writer.writerow(['Postal Code', order.postal_code])
    writer.writerow([])
    
    # Write order items header
    writer.writerow(['Order Items'])
    writer.writerow(['Product Name', 'Category', 'Price', 'Quantity', 'Total'])
    
    # Write order items
    for item in order_items:
        writer.writerow([
            item.product.name,
            item.product.category.name,
            f'Rs.{item.price}',
            item.quantity,
            f'Rs.{item.get_total()}'
        ])
    
    return response



@staff_member_required
def admin_user_edit(request, pk):
    """Edit user account information"""
    user = get_object_or_404(User, pk=pk)
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'User {user.username} has been updated successfully!')
            return redirect('custom_admin:user_detail', pk=user.pk)
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_obj': user,  # Renamed to avoid conflict with request.user
        'user_form': user_form,
        'profile_form': profile_form,
        'title': f'Edit User - {user.username}'
    }
    
    return render(request, 'admin/user_edit.html', context)

@staff_member_required
def admin_profile(request):
    """Admin profile view and edit"""
    user = request.user
    
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('custom_admin:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)
    
    # Get user statistics
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(user=user, status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_user': user,
        'user_profile': user_profile,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'admin/profile.html', context)

@staff_member_required
def admin_logout(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('store:login')