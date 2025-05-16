from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент."""
    return value * arg

@register.filter
def div(value, arg):
    """Делит значение на аргумент."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0