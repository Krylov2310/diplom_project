from django import template
from friends.models import Friendship

register = template.Library()


@register.filter
def is_friends(user1, user2):
    """Проверяет, являются ли два пользователя друзьями."""
    if not user1.is_authenticated or not user2.is_authenticated:
        return False
    if user1 == user2:
        return False

    return Friendship.objects.filter(
        from_user=user1,
        to_user=user2,
        status='accepted'
    ).exists() or Friendship.objects.filter(
        from_user=user2,
        to_user=user1,
        status='accepted'
    ).exists()
