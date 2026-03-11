from django.db import models


class Friendship(models.Model):
    from_user = models.ForeignKey(
        'users.UserProfile',
        related_name='friendships_initiated',
        on_delete=models.CASCADE,
        verbose_name='Кто отправил заявку'
    )
    to_user = models.ForeignKey(
        'users.UserProfile',
        related_name='friendships_received',
        on_delete=models.CASCADE,
        verbose_name='Кому отправлена заявка'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает подтверждения'),
            ('accepted', 'Подтверждено'),
            ('rejected', 'Отклонено'),
        ],
        default='pending',
        verbose_name='Статус дружбы'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = 'Дружба'
        verbose_name_plural = 'Друзья'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['to_user', 'status']),
        ]

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"
