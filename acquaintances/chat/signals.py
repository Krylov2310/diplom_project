from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Message


@receiver(post_save, sender=Message)
def notify_on_new_message(sender, instance, created, **kwargs):
    if created:
        print(f"Новое сообщение от {instance.sender}: {instance.content}")
        # Здесь может быть отправка уведомления через WebSocket и т. д.


def friendship_post_delete_handler(sender, instance, **kwargs):
    """
    Обработчик сигнала post_delete для Friendship.
    Удаляет приватный чат после удаления записи о дружбе.
    """
    from chat.services import delete_private_chat_if_needed

    user1 = instance.from_user
    user2 = instance.to_user

    delete_private_chat_if_needed(user1, user2)


class FriendsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'friends'

    def ready(self):
        post_delete.connect(
            friendship_post_delete_handler,
            sender='friends.Friendship'
        )
