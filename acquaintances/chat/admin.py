from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin.actions import delete_selected
from .models import ChatRoom, Message
from users.models import UserProfile
from datetime import timedelta
from django.utils import timezone


class ParticipantFilter(admin.SimpleListFilter):
    title = 'Участник чата'
    parameter_name = 'participant'

    def lookups(self, request, model_admin):
        users = UserProfile.objects.all()[:100]  # Ограничиваем для производительности
        return [(user.id, user.username) for user in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(participants__id=self.value())
        return queryset


class ChatTypeFilter(admin.SimpleListFilter):
    title = 'Тип чата'
    parameter_name = 'chat_type'

    def lookups(self, request, model_admin):
        return [
            ('public', 'Общий чат'),
            ('private', 'Приватный чат'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'public':
            return queryset.filter(is_public=True)
        elif self.value() == 'private':
            return queryset.filter(is_public=False)
        return queryset

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_public', 'created_at', 'participants_count', 'participant_list')
    list_filter = (ChatTypeFilter, 'created_at', ParticipantFilter)
    search_fields = ('name',)
    filter_horizontal = ('participants',)
    actions = ['make_public', 'make_private']

    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Количество участников'

    def participant_list(self, obj):
        participants = obj.participants.all()
        if participants.count() > 5:
            return format_html(
                '{} и ещё {}',
                ', '.join([p.username for p in participants[:5]]),
                participants.count() - 5
            )
        else:
            return ', '.join([p.username for p in participants])
    participant_list.short_description = 'Участники'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('participants')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "participants":
            kwargs["queryset"] = UserProfile.objects.all().order_by('username')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} чатов переведены в публичные')
    make_public.short_description = "Сделать выбранные чаты публичными"

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} чатов переведены в приватные')
    make_private.short_description = "Сделать выбранные чаты приватными"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat_room', 'sender', 'content_preview', 'timestamp')
    list_filter = ('timestamp', 'chat_room')
    search_fields = ('content', 'sender__username')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('chat_room', 'sender')
    actions = [delete_selected, 'delete_old_messages']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Содержание (превью)'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('chat_room', 'sender')

    def delete_old_messages(self, request, queryset):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        old_messages = queryset.filter(timestamp__lt=thirty_days_ago)
        count = old_messages.count()
        old_messages.delete()
        self.message_user(
            request,
            f'Удалено {count} сообщений старше 30 дней'
        )
    delete_old_messages.short_description = "Удалить сообщения старше 30 дней"
