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
