import hashlib

from django.db import models
from users.models import UserProfile


class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    is_public = models.BooleanField(default=False)  # Флаг для общего чата
    participants = models.ManyToManyField(
        'users.UserProfile',
        related_name='chat_rooms',
        verbose_name='Участники'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Поле для уникального ID приватного чата
    private_chat_id = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Чат-комната'
        verbose_name_plural = 'Чат-комнаты'

    def __str__(self):
        if self.name:
            return self.name
        if self.is_public:
            return "Общий чат"
        # Для приватных чатов формируем имя из имён участников
        participants = self.participants.all()
        if participants.count() == 2:
            return f"Чат: {participants[0].username} и {participants[1].username}"
        return f"Групповой чат ({participants.count()} участников)"

    def save(self, *args, **kwargs):
        """Просто сохраняем объект, генерация private_chat_id происходит отдельно."""
        super().save(*args, **kwargs)

    def _generate_private_chat_id(self):
        """Генерирует уникальный ID на основе ID участников."""
        participants = list(self.participants.order_by('id'))
        if len(participants) != 2:
            raise ValueError("Private chat ID can only be generated for exactly 2 participants")

        sorted_ids = sorted([participants[0].id, participants[1].id])
        chat_string = f"{sorted_ids[0]}:{sorted_ids[1]}"
        chat_hash = hashlib.sha256(chat_string.encode()).hexdigest()
        return chat_hash


class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
