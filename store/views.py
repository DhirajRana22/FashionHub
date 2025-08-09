from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Season, Product, Cart, CartItem, Wishlist, Order, OrderItem, UserProfile, UserMessage, Size, ProductSize, ContactMessage, Rating
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
from django.views.decorators.csrf import csrf_exempt
from .khalti_payment import KhaltiPayment
from .forms import UserRegistrationForm, UserProfileForm, ContactForm, LoginForm, GeneralContactForm, UserForm
from .utils.sorting import quick_sort_products, hybrid_sort_products

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
    men_category = Category.objects.filter(name__icontains='men').first()
    women_category = Category.objects.filter(name__icontains='women').first()
    kids_category = Category.objects.filter(name__icontains='kid').first()
    unisex_category = Category.objects.filter(name__icontains='unisex').first()
    
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
        'kids_category': kids_category,
        'unisex_category': unisex_category,
    })

def product_list(request):
    # Get filter parameters
    parent_category_id = request.GET.get('parent_category')
    gender = request.GET.get('gender')
    category_id = request.GET.get('category')
    season_param = request.GET.get('season')
    query = request.GET.get('q')
    tags = request.GET.get('tags')
    
    # Build base query with select_related for better performance
    products = Product.objects.select_related('category', 'season')
    
    # Apply filters
    filters = {}
    
    # Handle gender filtering - filter by gender category or its children
    if gender:
        if gender.lower() == 'men':
            # Get men's category and all its child categories
            men_category = Category.objects.get(id=23)
            child_categories = men_category.child_categories.all()
            category_ids = [men_category.id] + list(child_categories.values_list('id', flat=True))
            products = products.filter(category_id__in=category_ids)
        elif gender.lower() == 'women':
            # Get women's category and all its child categories
            women_category = Category.objects.get(id=24)
            child_categories = women_category.child_categories.all()
            category_ids = [women_category.id] + list(child_categories.values_list('id', flat=True))
            products = products.filter(category_id__in=category_ids)
    
    # Handle parent category filtering
    if parent_category_id:
        filters['category_id'] = parent_category_id
    
    # Filter by specific category (this will override parent category filter if both are provided)
    if category_id:
        filters['category_id'] = category_id
    
    # Handle season filtering
    if season_param:
        try:
            # Convert season parameter to season name
            season_mapping = {
                '1': 'Spring',
                '2': 'Summer', 
                '3': 'Fall',
                '4': 'Winter'
            }
            season_name = season_mapping.get(season_param)
            if season_name:
                season_obj = Season.objects.filter(name__iexact=season_name).first()
                if season_obj:
                    filters['season_id'] = season_obj.id
        except (ValueError, Season.DoesNotExist):
            pass  # Invalid season parameter, ignore it
    
    # Apply all filters at once
    if filters:
        products = products.filter(**filters)
    
    # Apply search query if provided
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
    
    # Apply tag filtering
    if tags:
        tag_terms = [term.strip() for term in tags.split(',')]
        tag_q = Q()
        for tag in tag_terms:
            tag_q |= Q(tags__icontains=tag)
        products = products.filter(tag_q)
    
    # Get sorting parameters
    sort_by = request.GET.get('sort_by', 'name')  # Default sort by name
    order = request.GET.get('order', 'asc')  # Default ascending order
    
    # Apply Quick Sort if sorting by price or rating
    if sort_by in ['price', 'rating']:
        # Convert QuerySet to list for Quick Sort
        products_list = list(products)
        
        # Apply Quick Sort algorithm
        if sort_by == 'price':
            sorted_products = quick_sort_products(products_list, sort_by='price', order=order)
        elif sort_by == 'rating':
            sorted_products = quick_sort_products(products_list, sort_by='rating', order=order)
        
        products = sorted_products
    else:
        # Use Django's default ordering for other fields
        if sort_by == 'name':
            if order == 'desc':
                products = products.order_by('-name')
            else:
                products = products.order_by('name')
        elif sort_by == 'created_at':
            if order == 'desc':
                products = products.order_by('-created_at')
            else:
                products = products.order_by('created_at')
    
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
    
    # Prepare sorting options for template
    sort_options = [
        {'value': 'name', 'label': 'Name'},
        {'value': 'price', 'label': 'Price'},
        {'value': 'rating', 'label': 'Rating'},
        {'value': 'created_at', 'label': 'Newest'},
    ]
    
    return render(request, 'store/product_list.html', {
        'products': products,
        'gender_categories': gender_categories,
        'categories': categories,
        'seasons': seasons,
        'cart': cart,
        'sort_options': sort_options,
        'current_sort': sort_by,
        'current_order': order,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        Q(category=product.category) | Q(season=product.season)
    ).exclude(pk=pk)[:4]
    cart = get_or_create_cart(request)
    
    # Get available sizes for this product
    available_sizes = ProductSize.objects.filter(product=product, stock__gt=0).select_related('size')
    
    # Check if user can rate this product (has purchased and received it)
    can_rate = False
    user_rating = None
    if request.user.is_authenticated:
        can_rate = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()
        user_rating = Rating.objects.filter(user=request.user, product=product).first()
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'cart': cart,
        'available_sizes': available_sizes,
        'can_rate': can_rate,
        'user_rating': user_rating,
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
        
        # Get quantity from form (default to 1)
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except (ValueError, TypeError):
            quantity = 1
        
        # Get size if provided
        size_id = request.POST.get('size_id')
        size = None
        available_stock = product.total_stock
        
        if size_id:
            size = get_object_or_404(Size, id=size_id)
            # Check if this size is available for this product
            product_size = ProductSize.objects.filter(product=product, size=size).first()
            if not product_size or product_size.stock <= 0:
                messages.error(request, f'Size {size.name} is not available for {product.name}.')
                return redirect('store:product_detail', pk=product_id)
            available_stock = product_size.stock
        elif product.sizes.exists():
            # Product has sizes but none selected
            messages.error(request, 'Please select a size.')
            return redirect('store:product_detail', pk=product_id)
        
        # Check if requested quantity is available
        if quantity > available_stock:
            size_text = f' in size {size.name}' if size else ''
            messages.error(request, f'Only {available_stock} items available{size_text}.')
            return redirect('store:product_detail', pk=product_id)
        
        # Check if product with same size already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Check stock availability before updating quantity
            new_quantity = cart_item.quantity + quantity
            if new_quantity > available_stock:
                size_text = f' in size {size.name}' if size else ''
                messages.error(request, f'Cannot add {quantity} more items. Only {available_stock} items available{size_text} and you already have {cart_item.quantity} in cart.')
                return redirect('store:product_detail', pk=product_id)
            
            cart_item.quantity = new_quantity
            cart_item.save()
        
        size_text = f' (Size: {size.name})' if size else ''
        quantity_text = f'{quantity}x ' if quantity > 1 else ''
        messages.success(request, f'{quantity_text}{product.name}{size_text} added to cart.')
        return redirect('store:product_detail', pk=product_id)
    
    return redirect('store:home')

def buy_now(request, product_id):
    """Create a temporary cart for immediate checkout without affecting the main cart"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Get quantity from form (default to 1)
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except (ValueError, TypeError):
            quantity = 1
        
        # Get size if provided
        size_id = request.POST.get('size_id')
        size = None
        available_stock = product.total_stock
        
        if size_id:
            size = get_object_or_404(Size, id=size_id)
            # Check if this size is available for this product
            product_size = ProductSize.objects.filter(product=product, size=size).first()
            if not product_size or product_size.stock <= 0:
                messages.error(request, f'Size {size.name} is not available for {product.name}.')
                return redirect('store:product_detail', pk=product_id)
            available_stock = product_size.stock
        elif product.sizes.exists():
            # Product has sizes but none selected
            messages.error(request, 'Please select a size.')
            return redirect('store:product_detail', pk=product_id)
        
        # Check if requested quantity is available
        if quantity > available_stock:
            size_text = f' in size {size.name}' if size else ''
            messages.error(request, f'Only {available_stock} items available{size_text}.')
            return redirect('store:product_detail', pk=product_id)
        
        # Check if user is logged in before proceeding
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to complete your purchase.')
            return redirect('store:login')
        
        # Store buy now product details in session instead of using cart
        request.session['buy_now_product'] = {
            'product_id': product.id,
            'size_id': size.id if size else None,
            'quantity': quantity
        }
        
        size_text = f' (Size: {size.name})' if size else ''
        quantity_text = f'{quantity}x ' if quantity > 1 else ''
        messages.success(request, f'{quantity_text}{product.name}{size_text} is ready for checkout.')
            
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
    buy_now_product = request.session.get('buy_now_product')
    
    # Check if we have either cart items or buy_now product
    if not cart.items.exists() and not buy_now_product:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')
    
    # If buy_now_product exists, use it instead of cart items
    if buy_now_product:
        # Get the product and size for buy_now
        product = get_object_or_404(Product, id=buy_now_product['product_id'])
        size = None
        if buy_now_product['size_id']:
            size = get_object_or_404(Size, id=buy_now_product['size_id'])
        
        # Create a temporary cart item object for display purposes
        class TempCartItem:
            def __init__(self, product, size, quantity):
                self.product = product
                self.size = size
                self.quantity = quantity
                self.subtotal = product.price * quantity
        
        temp_cart_items = [TempCartItem(product, size, buy_now_product['quantity'])]
        total_price = product.price * buy_now_product['quantity']
    else:
        # Use regular cart items
        temp_cart_items = cart.items.all()
        total_price = cart.total_price
    
    if request.method == 'POST':
        # Process the order
        try:
            payment_method = request.POST.get('payment_method')
            
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
                total_amount=total_price,
                payment_method=payment_method,
                order_notes=request.POST.get('order_notes', ''),
                payment_status=False  # Will be updated after payment verification
            )
            
            # Create order items based on source (buy_now or cart)
            if buy_now_product:
                # Handle buy_now product
                product = get_object_or_404(Product, id=buy_now_product['product_id'])
                size = None
                if buy_now_product['size_id']:
                    size = get_object_or_404(Size, id=buy_now_product['size_id'])
                
                size_name = size.name if size else None
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    price=product.price,
                    quantity=buy_now_product['quantity'],
                    size=size,
                    size_name=size_name
                )
                
                # Reduce stock (size-specific if applicable)
                if size:
                    # Reduce size-specific stock
                    product_size = ProductSize.objects.get(product=product, size=size)
                    product_size.stock -= buy_now_product['quantity']
                    if product_size.stock < 0:
                        product_size.stock = 0
                    product_size.save()
                else:
                    # Reduce general product stock
                    product.stock -= buy_now_product['quantity']
                    if product.stock < 0:
                        product.stock = 0
                    product.save()
                
                # Clear buy_now session data
                del request.session['buy_now_product']
            else:
                # Handle regular cart items
                for cart_item in cart.items.all():
                    # Handle size information
                    size_name = cart_item.size.name if cart_item.size else None
                    
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        product_name=cart_item.product.name,
                        price=cart_item.product.price,
                        quantity=cart_item.quantity,
                        size=cart_item.size,
                        size_name=size_name
                    )
                    
                    # Reduce stock (size-specific if applicable)
                    if cart_item.size:
                        # Reduce size-specific stock
                        product_size = ProductSize.objects.get(product=cart_item.product, size=cart_item.size)
                        product_size.stock -= cart_item.quantity
                        if product_size.stock < 0:
                            product_size.stock = 0
                        product_size.save()
                    else:
                        # Reduce general product stock
                        product = cart_item.product
                        product.stock -= cart_item.quantity
                        if product.stock < 0:
                            product.stock = 0
                        product.save()
                
                # Clear the cart only if not buy_now
                cart.items.all().delete()
            
            # Handle payment method
            if payment_method == 'khalti':
                # Initiate Khalti payment
                khalti = KhaltiPayment()
                payment_response = khalti.initiate_payment(order, request)
                
                if payment_response['success']:
                    # Store pidx in session for verification
                    request.session['khalti_pidx'] = payment_response['pidx']
                    request.session['order_id'] = order.id
                    
                    # Redirect to Khalti payment page
                    return redirect(payment_response['payment_url'])
                else:
                    # Payment initiation failed
                    messages.error(request, f'Payment initiation failed: {payment_response["error"]}')
                    # Restore cart items and stock
                    for item in order.items.all():
                        if item.product:
                            item.product.stock += item.quantity
                            item.product.save()
                            CartItem.objects.create(
                                cart=cart,
                                product=item.product,
                                quantity=item.quantity
                            )
                    order.delete()
                    # Create context with proper cart data for template
                    context = {
                        'cart': cart,
                        'cart_items': temp_cart_items,
                        'total_price': total_price,
                        'is_buy_now': bool(buy_now_product)
                    }
                    return render(request, 'store/checkout.html', context)
            else:
                # Cash on Delivery - keep payment status as unpaid (will be paid on delivery)
                order.payment_status = False
                order.save()
                messages.success(request, f'Your order (#{order.id}) has been placed successfully! Payment will be collected on delivery.')
                return redirect('store:order_success', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'There was an error processing your order: {str(e)}')
    
    # Create context with proper cart data for template
    context = {
        'cart': cart,
        'cart_items': temp_cart_items,
        'total_price': total_price,
        'is_buy_now': bool(buy_now_product)
    }
    return render(request, 'store/checkout.html', context)

@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

@login_required
def khalti_callback(request):
    """Handle Khalti payment callback"""
    pidx = request.GET.get('pidx')
    status = request.GET.get('status')
    
    # Get stored data from session
    session_pidx = request.session.get('khalti_pidx')
    order_id = request.session.get('order_id')
    
    if not pidx or not session_pidx or pidx != session_pidx:
        messages.error(request, 'Invalid payment session. Please try again.')
        return redirect('store:cart')
    
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        if status == 'Completed':
            # Verify payment with Khalti
            khalti = KhaltiPayment()
            verification_response = khalti.verify_payment(pidx)
            
            if verification_response['success']:
                payment_data = verification_response['data']
                
                # Check if payment is successful and amount matches
                if (payment_data.get('status') == 'Completed' and 
                    int(payment_data.get('total_amount', 0)) == int(order.total_amount * 100)):
                    
                    # Mark order as paid
                    order.payment_status = True
                    order.status = 'processing'
                    order.save()
                    
                    # Clear session data
                    request.session.pop('khalti_pidx', None)
                    request.session.pop('order_id', None)
                    
                    messages.success(request, f'Payment successful! Your order (#{order.id}) has been confirmed.')
                    return redirect('store:order_success', order_id=order.id)
                else:
                    # Payment verification failed
                    messages.error(request, 'Payment verification failed. Please contact support.')
                    order.status = 'cancelled'
                    order.cancellation_reason = 'Payment verification failed'
                    order.save()
                    
                    # Restore stock
                    for item in order.items.all():
                        if item.product:
                            item.product.stock += item.quantity
                            item.product.save()
            else:
                messages.error(request, f'Payment verification error: {verification_response["error"]}')
                order.status = 'cancelled'
                order.cancellation_reason = 'Payment verification error'
                order.save()
        else:
            # Payment was cancelled or failed
            messages.error(request, 'Payment was cancelled or failed.')
            order.status = 'cancelled'
            order.cancellation_reason = 'Payment cancelled by user'
            order.save()
            
            # Restore stock
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save()
        
        # Clear session data
        request.session.pop('khalti_pidx', None)
        request.session.pop('order_id', None)
        
    except Exception as e:
        messages.error(request, f'Error processing payment callback: {str(e)}')
    
    return redirect('store:my_orders')

def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))  # Ensure minimum quantity is 1
            
            # Check stock availability
            if cart_item.size:
                # Product has size, check size-specific stock
                product_size = ProductSize.objects.filter(
                    product=cart_item.product, 
                    size=cart_item.size
                ).first()
                if not product_size:
                    messages.error(request, f'Size {cart_item.size.name} is no longer available.')
                    return redirect('store:cart')
                available_stock = product_size.stock
                size_text = f' in size {cart_item.size.name}'
            else:
                # Product without size, check total stock
                available_stock = cart_item.product.total_stock
                size_text = ''
            
            # Validate quantity against available stock
            if quantity > available_stock:
                messages.error(request, f'Only {available_stock} items available{size_text}. Quantity updated to maximum available.')
                quantity = available_stock
            
            cart_item.quantity = quantity
            cart_item.save()
            
            if quantity < int(request.POST.get('quantity', 1)):
                messages.warning(request, f'Quantity adjusted to {quantity} due to stock limitations.')
            else:
                messages.success(request, 'Cart updated successfully.')
                
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
            
            # Role-based redirection: Staff users go to admin panel, regular users to home
            if user.is_staff:
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}! You have been logged into the admin panel.')
                return redirect('/admin/')  # Custom admin panel
            else:
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

@login_required
def rate_product(request, product_id):
    """Allow users to rate a product they have purchased"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__status='delivered'
    ).exists()
    
    if not has_purchased:
        messages.error(request, 'You can only rate products you have purchased and received.')
        return redirect('store:product_detail', pk=product_id)
    
    # Get existing rating if any
    existing_rating = Rating.objects.filter(user=request.user, product=product).first()
    
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        review_text = request.POST.get('review', '').strip()
        
        if rating_value and 1 <= int(rating_value) <= 5:
            if existing_rating:
                # Update existing rating
                existing_rating.rating = int(rating_value)
                existing_rating.review = review_text
                existing_rating.save()
                messages.success(request, 'Your rating has been updated successfully!')
            else:
                # Create new rating
                Rating.objects.create(
                    user=request.user,
                    product=product,
                    rating=int(rating_value),
                    review=review_text
                )
                messages.success(request, 'Thank you for rating this product!')
        else:
            messages.error(request, 'Please provide a valid rating (1-5 stars).')
        
        return redirect('store:product_detail', pk=product_id)
    
    context = {
        'product': product,
        'existing_rating': existing_rating,
        'has_purchased': has_purchased,
    }
    return render(request, 'store/rate_product.html', context)

@login_required
def product_ratings(request, product_id):
    """Display all ratings for a specific product"""
    product = get_object_or_404(Product, id=product_id)
    ratings = Rating.objects.filter(product=product).order_by('-created_at')
    
    context = {
        'product': product,
        'ratings': ratings,
        'average_rating': product.average_rating,
        'rating_count': product.rating_count,
        'rating_distribution': product.rating_distribution,
    }
    return render(request, 'store/product_ratings.html', context)

@csrf_exempt
def api_product_search(request):
    """
    API endpoint for chatbot to search products by name, price, size, etc.
    Accepts GET parameters:
      - product: product name or keyword
      - price: max price
      - size: (optional, if you have size info)
    Returns a JSON list of matching products (name, price, stock, etc.).
    """
    product_query = request.GET.get('product', '')
    price_query = request.GET.get('price', None)
    # You can add more filters as needed (e.g., size)

    products = Product.objects.all()
    if product_query:
        products = products.filter(name__icontains=product_query)
    if price_query:
        try:
            price_val = float(price_query)
            products = products.filter(price__lte=price_val)
        except ValueError:
            pass
    # Only show products in stock
    products = products.filter(stock__gt=0)

    # Prepare response data
    data = [
        {
            'name': p.name,
            'price': float(p.price),
            'stock': p.stock,
            'category': p.category.name,
            'season': p.season.name,
            'tags': p.tag_list,
            'image': p.image.url if p.image else None,
        }
        for p in products[:10]  # Limit to 10 results
    ]
    return JsonResponse({'products': data})

@login_required
def my_account(request):
    """
    Display and handle user account information updates
    """
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your account information has been updated successfully!')
            return redirect('store:my_account')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    # Get user's recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'recent_orders': recent_orders,
        'user_profile': user_profile,
    }
    return render(request, 'store/my_account.html', context)


def contact_view(request):
    """Contact page for users to send messages to admin"""
    if request.method == 'POST':
        if request.user.is_authenticated:
            # For logged-in users, save to UserMessage model
            form = ContactForm(request.POST)
            if form.is_valid():
                user_message = form.save(commit=False)
                user_message.user = request.user
                user_message.level = messages.INFO  # Default level for user queries
                user_message.save()
                messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
                return redirect('store:contact')
        else:
            # For anonymous users, use GeneralContactForm and save to ContactMessage model
            form = GeneralContactForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']
                
                # Save to ContactMessage model
                ContactMessage.objects.create(
                    name=name,
                    email=email,
                    subject=subject,
                    message=message
                )
                
                messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
                return redirect('store:contact')
    else:
        if request.user.is_authenticated:
            form = ContactForm()
        else:
            form = GeneralContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'store/contact.html', context)
