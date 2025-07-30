from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return ''
    return dictionary.get(key, '')

@register.filter
def get_dict_value(dictionary, key):
    """Alternative filter for getting dictionary values"""
    if dictionary is None:
        return ''
    return dictionary.get(key, '') 