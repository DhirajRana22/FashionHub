from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Access dictionary values by key in Django templates"""
    return dictionary.get(key, '')

@register.simple_tag
def get_product_size(product_sizes, size):
    """Get the ProductSize object for a given size."""
    return product_sizes.filter(size=size).first()