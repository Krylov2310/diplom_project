from django.contrib import admin
from django.utils.html import format_html
from .models import Gallery, GalleryRating


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview',
        'author',
        'comment',
        'likes_count',
        'dislikes_count',
        'created_at'
    )
    list_filter = ('author', 'created_at')  # Корректный кортеж
    search_fields = ('comment', 'author__username')
    readonly_fields = ('likes_count', 'dislikes_count', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('author', 'image', 'image_preview', 'comment')
        }),
        ('Статистика', {
            'fields': ('likes_count', 'dislikes_count'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "Нет изображения"

    image_preview.short_description = 'Превью'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related('ratings')


@admin.register(GalleryRating)
class GalleryRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'gallery', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'gallery__id']
    readonly_fields = ['created_at']
