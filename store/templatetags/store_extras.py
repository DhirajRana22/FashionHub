from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Access dictionary values by key in Django templates"""
    return dictionary.get(key, '') 