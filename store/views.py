from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Season, Product, Cart, CartItem, Wishlist, Order, OrderItem, UserProfile, UserMessage
from django.db.models import Q, Count, Prefetch
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.http import condition

def get_or_create_cart(request):
    if 'cart_id' not in request.session:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
    else:
        cart = get_object_or_404(Cart, id=request.session['cart_id'])
    return cart

def cart_context_processor(request):
    cart = get_or_create_cart(request)
    
    # Get wishlist products for logged in user
    wishlist_products = []
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist_products = wishlist.products.all()
    
    return {
        'cart': cart,
        'wishlist_products': wishlist_products
    }

def home(request):
    categories = Category.objects.all()
    seasons = Season.objects.all()
    # Only get products that are marked as featured
    featured_products = Product.objects.filter(featured=True)[:8]
    cart = get_or_create_cart(request)
    
    # Get all gender categories (type='gender')
    gender_categories = Category.objects.filter(type='gender')
    
    # Get specific gender categories for the links
    men_category = Category.objects.filter(type='gender', name__icontains='men').first()
    women_category = Category.objects.filter(type='gender', name__icontains='women').first()
    
    # Get all regular categories with their parent gender category
    regular_categories = Category.objects.filter(type='regular').select_related('parent')
    
    return render(request, 'store/home.html', {
        'categories': categories,
        'gender_categories': gender_categories,
        'regular_categories': regular_categories,
        'seasons': seasons,
        'featured_products': featured_products,
        'cart': cart,
        'men_category': men_category,
        'women_category': women_category,
    })

def product_list(request):
    # Get filter parameters
    parent_category_id = request.GET.get('parent_category')
    gender = request.GET.get('gender')
    category_id = request.GET.get('category')
    season_id = request.GET.get('season')
    query = request.GET.get('q')
    tags = request.GET.get('tags')
    
    # Build base query with select_related for better performance
    products = Product.objects.select_related('category', 'season')
    
    # Apply filters
    filters = {}
    
    # Handle gender/parent category filtering
    if parent_category_id:
        # Direct filter by category ID
        filters['category_id'] = parent_category_id
    elif gender:
        # Use exact category filtering based on gender
        if gender.lower() == 'men':
            # Find men's category (ID 23)
            filters['category_id'] = 23
        elif gender.lower() == 'women':
            # Find women's category (ID 24)
            filters['category_id'] = 24
    
    # Filter by specific category (this will override parent category filter if both are provided)
    if category_id:
        filters['category_id'] = category_id
    
    if season_id:
        filters['season_id'] = season_id
    
    # Apply all filters at once
    if filters:
        products = products.filter(**filters)
    
    # Apply search query if provided
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Apply tag filtering
    if tags:
        tag_terms = [term.strip() for term in tags.split(',')]
        tag_q = Q()
        for tag in tag_terms:
            tag_q |= Q(tags__icontains=tag)
        products = products.filter(tag_q)
    
    # Get all gender categories for the dropdown
    # In your case, these are actually the top level categories
    men_category = Category.objects.get(id=23)  # Men's Cloths
    women_category = Category.objects.get(id=24)  # Women's Cloths
    gender_categories = [men_category, women_category]
    
    # Get all categories
    categories = Category.objects.all()
    
    # Get seasons
    seasons = Season.objects.all()
    
    # Get cart
    cart = get_or_create_cart(request)
    
    return render(request, 'store/product_list.html', {
        'products': products,
        'gender_categories': gender_categories,
        'categories': categories,
        'seasons': seasons,
        'cart': cart,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        Q(category=product.category) | Q(season=product.season)
    ).exclude(pk=pk)[:4]
    cart = get_or_create_cart(request)
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'cart': cart,
    })

def cart_view(request):
    cart = get_or_create_cart(request)
    
    # Check if the form was submitted (proceed to checkout button)
    if request.method == 'POST' and 'checkout' in request.POST:
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to complete your purchase.')
            # Store the next URL in session to redirect after login
            request.session['next'] = 'store:checkout'
            return redirect('store:login')
        else:
            return redirect('store:checkout')
            
    return render(request, 'store/cart.html', {'cart': cart})

def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        
        # Check if product already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, f'{product.name} added to cart.')
        return redirect('store:product_detail', pk=product_id)
    
    return redirect('store:home')

def buy_now(request, product_id):
    """Add product to cart and redirect to checkout directly"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        
        # Clear the cart first (we only want this product)
        cart.items.all().delete()
        
        # Add the product to cart
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        
        messages.success(request, f'{product.name} is ready for checkout.')
        
        # Check if user is logged in before redirecting to checkout
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to complete your purchase.')
            return redirect('store:login')
            
        return redirect('store:checkout')
    
    return redirect('store:product_detail', pk=product_id)

@login_required
def toggle_wishlist(request, product_id):
    """Add or remove product from wishlist"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Check if product is already in wishlist
        if product in wishlist.products.all():
            # Remove from wishlist
            wishlist.products.remove(product)
            messages.success(request, f'{product.name} removed from wishlist.')
        else:
            # Add to wishlist
            wishlist.products.add(product)
            messages.success(request, f'{product.name} added to wishlist.')
            
        return redirect('store:product_detail', pk=product_id)
    
    return redirect('store:home')

@login_required
def wishlist_view(request):
    """View user's wishlist"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.all()
    
    return render(request, 'store/wishlist.html', {
        'wishlist': wishlist,
        'products': products,
    })

@login_required
def checkout(request):
    """Checkout page"""
    cart = get_or_create_cart(request)
    
    # Only proceed if cart has items
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')
    
    if request.method == 'POST':
        # Process the order
        try:
            # Create order
            order = Order.objects.create(
                user=request.user,
                full_name=request.POST.get('full_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                postal_code=request.POST.get('postal_code'),
                receiver_name=request.POST.get('receiver_name', ''),
                receiver_phone=request.POST.get('receiver_phone', ''),
                total_amount=cart.total_price,
                payment_method=request.POST.get('payment_method'),
                order_notes=request.POST.get('order_notes', '')
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
                
                # Reduce stock
                product = cart_item.product
                product.stock -= cart_item.quantity
                if product.stock < 0:
                    product.stock = 0
                product.save()
            
            # Clear the cart
            cart.items.all().delete()
            
            messages.success(request, f'Your order (#{order.id}) has been placed successfully!')
            return redirect('store:order_success', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'There was an error processing your order: {str(e)}')
    
    return render(request, 'store/checkout.html', {'cart': cart})

@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))  # Ensure minimum quantity is 1
            cart_item.quantity = quantity
            cart_item.save()
        except ValueError:
            messages.error(request, 'Invalid quantity value.')
            return redirect('store:cart')
            
        return redirect('store:cart')
    
    return redirect('store:home')

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
        return redirect('store:cart')
    
    return redirect('store:home')

# Authentication Views
def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Check for next URL in POST first, then session, then default to home
            next_url = request.POST.get('next', None)
            if not next_url and 'next' in request.session:
                next_url = request.session.pop('next')
            
            if next_url:
                return redirect(next_url)
            return redirect('store:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    next_url = request.GET.get('next', '')
    return render(request, 'store/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('store:home')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
        
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validate form data
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('store:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('store:register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('store:register')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create user profile with just phone number
            UserProfile.objects.create(
                user=user,
                phone=phone,
                # Address fields will remain blank
            )
            
            # Login user
            login(request, user)
            messages.success(request, 'Your account has been created successfully.')
            return redirect('store:home')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'store/register.html')

@login_required
def my_orders(request):
    """Display all orders for the current user"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

@login_required
def cancel_order(request, order_id):
    """Cancel an order if it's within 30 minutes of creation"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        if order.can_cancel:
            order.status = 'cancelled'
            order.cancellation_reason = 'Cancelled by user'
            order.save()
            
            # Return items to inventory
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()
            
            messages.success(request, f'Order #{order.id} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled. Orders can only be cancelled within 30 minutes of placement.')
    
    return redirect('store:my_orders')

@login_required
def confirm_order_receipt(request, order_id):
    """Allow users to confirm that they've received an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        if order.status == 'delivered' and not order.is_received:
            order.is_received = True
            order.received_at = timezone.now()
            order.save()
            
            # Create a notification for the admin user
            for admin_user in User.objects.filter(is_superuser=True):
                UserMessage.objects.create(
                    user=admin_user,
                    message=f"Customer {request.user.username} has confirmed receipt of Order #{order.id}.",
                    level=messages.SUCCESS
                )
            
            messages.success(request, f"Thank you for confirming receipt of your order #{order.id}!")
        else:
            messages.error(request, "This order cannot be marked as received.")
    
    return redirect('store:my_orders')
