import os
import django
import random
from decimal import Decimal

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category, Season, Product

def create_sample_data():
    # Clear existing data
    Product.objects.all().delete()
    Category.objects.all().delete()
    Season.objects.all().delete()
    
    print("Creating seasons...")
    seasons = [
        Season(name="Spring"),
        Season(name="Summer"),
        Season(name="Fall"),
        Season(name="Winter")
    ]
    Season.objects.bulk_create(seasons)
    
    print("Creating categories...")
    # Men's categories
    men_categories = [
        Category(name="T-Shirts", gender="Men"),
        Category(name="Shirts", gender="Men"),
        Category(name="Jeans", gender="Men"),
        Category(name="Hoodies", gender="Men"),
        Category(name="Jackets", gender="Men"),
        Category(name="Shorts", gender="Men"),
        Category(name="Sweaters", gender="Men"),
    ]
    Category.objects.bulk_create(men_categories)
    
    # Women's categories
    women_categories = [
        Category(name="Dresses", gender="Women"),
        Category(name="Tops", gender="Women"),
        Category(name="Jeans", gender="Women"),
        Category(name="Skirts", gender="Women"),
        Category(name="Jackets", gender="Women"),
        Category(name="Sweaters", gender="Women"),
        Category(name="Shorts", gender="Women"),
    ]
    Category.objects.bulk_create(women_categories)
    
    # Unisex categories
    unisex_categories = [
        Category(name="Hats", gender="Unisex"),
        Category(name="Scarves", gender="Unisex"),
        Category(name="Gloves", gender="Unisex"),
    ]
    Category.objects.bulk_create(unisex_categories)
    
    print("Creating products...")
    # Get all categories and seasons
    all_categories = list(Category.objects.all())
    all_seasons = list(Season.objects.all())
    spring = Season.objects.get(name="Spring")
    summer = Season.objects.get(name="Summer")
    fall = Season.objects.get(name="Fall")
    winter = Season.objects.get(name="Winter")
    
    # Example products for Men
    men_products = [
        # Spring
        {
            "name": "Lightweight Cotton T-Shirt",
            "description": "A comfortable and breathable cotton t-shirt perfect for spring weather. Available in various colors.",
            "price": Decimal("24.99"),
            "category": Category.objects.get(name="T-Shirts", gender="Men"),
            "season": spring,
        },
        {
            "name": "Button-Down Oxford Shirt",
            "description": "A classic Oxford shirt that's perfect for casual or semi-formal spring occasions. Made from high-quality cotton.",
            "price": Decimal("49.99"),
            "category": Category.objects.get(name="Shirts", gender="Men"),
            "season": spring,
        },
        {
            "name": "Lightweight Chino Pants",
            "description": "Comfortable and stylish chino pants made from lightweight cotton blend, perfect for spring days.",
            "price": Decimal("59.99"),
            "category": Category.objects.get(name="Jeans", gender="Men"),
            "season": spring,
        },
        
        # Summer
        {
            "name": "Graphic Print Summer T-Shirt",
            "description": "A cool and vibrant graphic t-shirt made from 100% cotton, perfect for hot summer days.",
            "price": Decimal("29.99"),
            "category": Category.objects.get(name="T-Shirts", gender="Men"),
            "season": summer,
        },
        {
            "name": "Linen Casual Shirt",
            "description": "A breathable linen shirt that keeps you cool during the hottest summer days. Available in light colors.",
            "price": Decimal("54.99"),
            "category": Category.objects.get(name="Shirts", gender="Men"),
            "season": summer,
        },
        {
            "name": "Bermuda Shorts",
            "description": "Comfortable Bermuda shorts for casual summer outings. Features multiple pockets and durable fabric.",
            "price": Decimal("39.99"),
            "category": Category.objects.get(name="Shorts", gender="Men"),
            "season": summer,
        },
        
        # Fall
        {
            "name": "Flannel Plaid Shirt",
            "description": "A warm and soft flannel shirt with classic plaid pattern, perfect for fall weather.",
            "price": Decimal("44.99"),
            "category": Category.objects.get(name="Shirts", gender="Men"),
            "season": fall,
        },
        {
            "name": "Casual Hoodie",
            "description": "A comfortable hoodie with soft inner lining, perfect for those chilly fall evenings.",
            "price": Decimal("64.99"),
            "category": Category.objects.get(name="Hoodies", gender="Men"),
            "season": fall,
        },
        {
            "name": "Slim Fit Jeans",
            "description": "Stylish slim fit jeans that offer both comfort and durability for the fall season.",
            "price": Decimal("69.99"),
            "category": Category.objects.get(name="Jeans", gender="Men"),
            "season": fall,
        },
        
        # Winter
        {
            "name": "Wool Blend Sweater",
            "description": "A warm wool blend sweater that keeps you cozy during the coldest winter days.",
            "price": Decimal("79.99"),
            "category": Category.objects.get(name="Sweaters", gender="Men"),
            "season": winter,
        },
        {
            "name": "Insulated Winter Jacket",
            "description": "A heavy-duty insulated jacket designed to keep you warm in freezing winter temperatures.",
            "price": Decimal("129.99"),
            "category": Category.objects.get(name="Jackets", gender="Men"),
            "season": winter,
        },
        {
            "name": "Thermal Base Layer",
            "description": "A thermal base layer shirt that helps maintain body heat during winter activities.",
            "price": Decimal("34.99"),
            "category": Category.objects.get(name="T-Shirts", gender="Men"),
            "season": winter,
        },
    ]
    
    # Example products for Women
    women_products = [
        # Spring
        {
            "name": "Floral Print Dress",
            "description": "A beautiful floral print dress perfect for spring occasions. Made from lightweight and breathable fabric.",
            "price": Decimal("59.99"),
            "category": Category.objects.get(name="Dresses", gender="Women"),
            "season": spring,
        },
        {
            "name": "Pastel Blouse",
            "description": "A stylish pastel-colored blouse that's perfect for spring. Features a flattering cut and soft fabric.",
            "price": Decimal("44.99"),
            "category": Category.objects.get(name="Tops", gender="Women"),
            "season": spring,
        },
        {
            "name": "Lightweight Denim Jacket",
            "description": "A versatile lightweight denim jacket, perfect for those cool spring evenings.",
            "price": Decimal("74.99"),
            "category": Category.objects.get(name="Jackets", gender="Women"),
            "season": spring,
        },
        
        # Summer
        {
            "name": "Maxi Summer Dress",
            "description": "A flowing maxi dress perfect for beach days and summer outings. Made from breathable fabric.",
            "price": Decimal("69.99"),
            "category": Category.objects.get(name="Dresses", gender="Women"),
            "season": summer,
        },
        {
            "name": "Sleeveless Crop Top",
            "description": "A trendy sleeveless crop top that's perfect for hot summer days. Available in multiple colors.",
            "price": Decimal("29.99"),
            "category": Category.objects.get(name="Tops", gender="Women"),
            "season": summer,
        },
        {
            "name": "High-Waisted Shorts",
            "description": "Stylish high-waisted shorts that offer comfort and style for summer activities.",
            "price": Decimal("39.99"),
            "category": Category.objects.get(name="Shorts", gender="Women"),
            "season": summer,
        },
        
        # Fall
        {
            "name": "Knit Sweater",
            "description": "A cozy knit sweater that's perfect for fall weather. Features a relaxed fit and soft yarn.",
            "price": Decimal("64.99"),
            "category": Category.objects.get(name="Sweaters", gender="Women"),
            "season": fall,
        },
        {
            "name": "A-Line Skirt",
            "description": "A stylish A-line skirt that pairs well with sweaters and boots for a perfect fall look.",
            "price": Decimal("49.99"),
            "category": Category.objects.get(name="Skirts", gender="Women"),
            "season": fall,
        },
        {
            "name": "Skinny Jeans",
            "description": "Classic skinny jeans that offer both style and comfort for the fall season.",
            "price": Decimal("69.99"),
            "category": Category.objects.get(name="Jeans", gender="Women"),
            "season": fall,
        },
        
        # Winter
        {
            "name": "Down-Filled Parka",
            "description": "A warm down-filled parka designed to keep you comfortable in freezing winter temperatures.",
            "price": Decimal("149.99"),
            "category": Category.objects.get(name="Jackets", gender="Women"),
            "season": winter,
        },
        {
            "name": "Turtleneck Sweater",
            "description": "A cozy turtleneck sweater that provides warmth and style during cold winter months.",
            "price": Decimal("74.99"),
            "category": Category.objects.get(name="Sweaters", gender="Women"),
            "season": winter,
        },
        {
            "name": "Thermal Leggings",
            "description": "Warm thermal leggings that can be worn under skirts or pants for extra warmth in winter.",
            "price": Decimal("49.99"),
            "category": Category.objects.get(name="Jeans", gender="Women"),
            "season": winter,
        },
    ]
    
    # Example products for Unisex
    unisex_products = [
        # Spring
        {
            "name": "Baseball Cap",
            "description": "A classic baseball cap perfect for shielding from the spring sun. One size fits most.",
            "price": Decimal("24.99"),
            "category": Category.objects.get(name="Hats", gender="Unisex"),
            "season": spring,
        },
        
        # Summer
        {
            "name": "Sun Hat",
            "description": "A wide-brimmed sun hat that provides excellent protection from the summer sun.",
            "price": Decimal("34.99"),
            "category": Category.objects.get(name="Hats", gender="Unisex"),
            "season": summer,
        },
        
        # Fall
        {
            "name": "Light Knit Scarf",
            "description": "A stylish light knit scarf that adds warmth and style to any fall outfit.",
            "price": Decimal("29.99"),
            "category": Category.objects.get(name="Scarves", gender="Unisex"),
            "season": fall,
        },
        
        # Winter
        {
            "name": "Wool Beanie",
            "description": "A warm wool beanie that keeps your head and ears protected during cold winter days.",
            "price": Decimal("19.99"),
            "category": Category.objects.get(name="Hats", gender="Unisex"),
            "season": winter,
        },
        {
            "name": "Cashmere Scarf",
            "description": "A luxurious cashmere scarf that provides exceptional warmth and comfort in winter.",
            "price": Decimal("69.99"),
            "category": Category.objects.get(name="Scarves", gender="Unisex"),
            "season": winter,
        },
        {
            "name": "Leather Gloves",
            "description": "Premium leather gloves with soft inner lining for maximum warmth during winter.",
            "price": Decimal("54.99"),
            "category": Category.objects.get(name="Gloves", gender="Unisex"),
            "season": winter,
        },
    ]
    
    # Combine all products
    all_products = men_products + women_products + unisex_products
    
    # Create products in the database
    for product_data in all_products:
        Product.objects.create(**product_data)
    
    print(f"Created {len(all_products)} products!")
    print("Sample data created successfully!")

if __name__ == "__main__":
    create_sample_data() 