#!/usr/bin/env python
"""
Script to populate the Size model with default clothing sizes
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Size

def populate_sizes():
    """Create default clothing sizes"""
    
    sizes_data = [
        {'name': 'XS', 'description': 'Extra Small', 'sort_order': 1},
        {'name': 'S', 'description': 'Small', 'sort_order': 2},
        {'name': 'M', 'description': 'Medium', 'sort_order': 3},
        {'name': 'L', 'description': 'Large', 'sort_order': 4},
        {'name': 'XL', 'description': 'Extra Large', 'sort_order': 5},
        {'name': 'XXL', 'description': 'Double Extra Large', 'sort_order': 6},
        {'name': 'XXXL', 'description': 'Triple Extra Large', 'sort_order': 7},
    ]
    
    print("Creating default clothing sizes...")
    
    for size_data in sizes_data:
        size, created = Size.objects.get_or_create(
            name=size_data['name'],
            defaults={
                'description': size_data['description'],
                'sort_order': size_data['sort_order']
            }
        )
        
        if created:
            print(f"✓ Created size: {size.name} ({size.description})")
        else:
            print(f"- Size already exists: {size.name} ({size.description})")
    
    print(f"\nTotal sizes in database: {Size.objects.count()}")
    print("Size population completed!")

if __name__ == '__main__':
    populate_sizes()