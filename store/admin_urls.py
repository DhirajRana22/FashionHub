from django.urls import path
from . import admin_views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('', admin_views.admin_dashboard, name='dashboard'),
    
    # Products
    path('products/', admin_views.admin_products, name='products'),
    path('products/add/', admin_views.admin_product_add, name='product_add'),
    path('products/<int:pk>/edit/', admin_views.admin_product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', admin_views.admin_product_delete, name='product_delete'),
    
    # Categories
    path('categories/', admin_views.admin_categories, name='categories'),
    path('categories/add/', admin_views.admin_category_add, name='category_add'),
    path('categories/<int:pk>/edit/', admin_views.admin_category_edit, name='category_edit'),
    
    # Seasons
    path('seasons/', admin_views.admin_seasons, name='seasons'),
    path('seasons/add/', admin_views.admin_season_add, name='season_add'),
    path('seasons/<int:pk>/edit/', admin_views.admin_season_edit, name='season_edit'),
    path('seasons/<int:pk>/delete/', admin_views.admin_season_delete, name='season_delete'),
    
    # Orders
    path('orders/', admin_views.admin_orders, name='orders'),
    path('orders/<int:pk>/', admin_views.admin_order_detail, name='order_detail'),
    path('orders/<int:pk>/send-email/', admin_views.admin_send_order_email, name='send_order_email'),
    path('orders/<int:pk>/invoice/', admin_views.admin_order_invoice, name='order_invoice'),
    path('orders/<int:pk>/export/', admin_views.admin_export_order, name='export_order'),

    
    # Users
    path('users/', admin_views.admin_users, name='users'),
    path('users/add/', admin_views.admin_user_add, name='add_user'),
    path('users/<int:pk>/', admin_views.admin_user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', admin_views.admin_user_edit, name='user_edit'),
    
    # Admin Profile
    path('profile/', admin_views.admin_profile, name='profile'),
    
    # Messages
    path('messages/', admin_views.admin_messages, name='messages'),
    
    # Analytics
    path('analytics/', admin_views.admin_analytics, name='analytics'),
    
    # Logout
    path('logout/', admin_views.admin_logout, name='logout'),
]