# from django.views.generic import ListView
# from gallery.models import Gallery, GalleryRating
#
#
# class UserGalleryView(ListView):
#     print('\033[31mUserGalleryView\033[0m')
#     model = Gallery
#     template_name = 'users/gallery_user.html'
#     context_object_name = 'galleries'
#     paginate_by = 12
#     ordering = ['-created_at']  # сортировка по дате создания (новые первыми)
#
#     def get_queryset(self):
#         # Получаем user_id из URL (например, /gallery/user/5/)
#         user_id = self.kwargs.get('user_id')
#         if user_id:
#             # Фильтруем галереи по указанному пользователю
#             return super().get_queryset().filter(
#                 author_id=user_id
#             ).select_related('author')
#         else:
#             # Если user_id не передан, возвращаем все галереи (или можно вернуть пустой QuerySet)
#             return super().get_queryset().select_related('author')
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         gallery_ids = [gallery.id for gallery in context['galleries']]
#
#         if self.request.user.is_authenticated:
#             # Получаем все оценки текущего пользователя для галерей на странице
#             user_ratings = GalleryRating.objects.filter(
#                 gallery_id__in=gallery_ids,
#                 user=self.request.user
#             ).values_list('gallery_id', 'rating')
#             # Преобразуем в словарь: {gallery_id: rating}
#             context['user_ratings_dict'] = dict(user_ratings)
#         else:
#             context['user_ratings_dict'] = {}
#
#         # Добавляем ID просматриваемого пользователя в контекст для использования в шаблоне
#         context['viewed_user_id'] = self.kwargs.get('user_id')
#
#         return context