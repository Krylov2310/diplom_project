import django_filters
from .models import UserProfile


class ImageFieldFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value is None:
            return qs
        if value == 'has_avatar':
            return qs.exclude(avatar__isnull=True).exclude(avatar='')
        elif value == 'no_avatar':
            return qs.filter(avatar__isnull=True) | qs.filter(avatar='')
        return qs


class ProfileFilter(django_filters.FilterSet):
    avatar = ImageFieldFilter(
        label='Наличие аватара',
        choices=[
            ('has_avatar', 'С аватаром'),
            ('no_avatar', 'Без аватара'),
        ],
        required=False
    )

    class Meta:
        model = UserProfile
        fields = {
            'email': ['exact', 'icontains'],
            'username': ['icontains'],
            'gender': ['exact'],
            'age': ['exact', 'lt', 'gt', 'gte', 'lte'],
            'city': ['icontains'],
            'status': ['icontains'],
            'is_active': ['exact'],
        }
