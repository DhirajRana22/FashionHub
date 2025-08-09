from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Main app URLs
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    
    # Checkout and Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('khalti-callback/', views.khalti_callback, name='khalti_callback'),
    
    # User Account Management
    path('my-account/', views.my_account, name='my_account'),
    
    # User Order Management
    path('my-orders/', views.my_orders, name='my_orders'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('confirm-receipt/<int:order_id>/', views.confirm_order_receipt, name='confirm_receipt'),
    path('rate-product/<int:product_id>/', views.rate_product, name='rate_product'),
    path('product-ratings/<int:product_id>/', views.product_ratings, name='product_ratings'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    # API endpoint for chatbot product search
    path('api/products/', views.api_product_search, name='api_product_search'),
    
    # Contact page
    path('contact/', views.contact_view, name='contact'),
]