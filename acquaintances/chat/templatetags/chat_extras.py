from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Фильтр для доступа к элементам словаря в шаблонах"""
    return dictionary.get(key)
