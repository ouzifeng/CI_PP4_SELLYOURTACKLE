from django import template

register = template.Library()

class LookupFilter:
    def __init__(self, value):
        self.value = value

    def __call__(self, arg):
        return self.value.get(arg)

@register.filter(name='lookup')
def lookup(value, arg):
    return LookupFilter(value)(arg)

@register.filter(name='equalto')
def equalto(value, arg):
    """Compares if value is equal to arg."""
    return value == arg

@register.filter
def multiply(value, arg):
    return value * arg