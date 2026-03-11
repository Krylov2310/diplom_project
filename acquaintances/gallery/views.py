from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy, reverse

from .forms import AddImageForms
from .models import Gallery, GalleryRating


class GalleryListView(LoginRequiredMixin, ListView):
    # print('\033[31mGalleryListView\033[0m')
    model = Gallery
    template_name = 'gallery/gallery_list.html'
    context_object_name = 'galleries'
    paginate_by = 6
    ordering = ['-created_at']

    def get_queryset(self):
        return super().get_queryset().select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gallery_ids = [gallery.id for gallery in context['galleries']]
        # print('\033[31mgallery_ids\033[0m', gallery_ids)

        if self.request.user.is_authenticated:
            user_ratings = GalleryRating.objects.filter(
                gallery_id__in=gallery_ids,
                user=self.request.user
            ).values_list('gallery_id', 'rating')
            # print('\033[31muser_ratings', user_ratings, '\033[0m')
            context['user_ratings_dict'] = dict(user_ratings)
            # print('\033[31mcontext', context,'\033[0m')
        else:
            context['user_ratings_dict'] = {}
        return context


class UserGalleryView(LoginRequiredMixin, ListView):
    # print('\033[31mUserGalleryView\033[0m')
    model = Gallery
    template_name = 'users/gallery_user.html'
    context_object_name = 'galleries'
    paginate_by = 6
    ordering = ['-created_at']  # сортировка по дате создания (новые первыми)

    def get_queryset(self):
        # Получаем user_id из URL (например, /gallery/user/5/)
        user_id = self.kwargs.get('user_id')
        if user_id:
            # Фильтруем галереи по указанному пользователю
            return super().get_queryset().filter(
                author_id=user_id
            ).select_related('author')
        else:
            # Если user_id не передан, возвращаем все галереи (или можно вернуть пустой QuerySet)
            return super().get_queryset().select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gallery_ids = [gallery.id for gallery in context['galleries']]

        if self.request.user.is_authenticated:
            # Получаем все оценки текущего пользователя для галерей на странице
            user_ratings = GalleryRating.objects.filter(
                gallery_id__in=gallery_ids,
                user=self.request.user
            ).values_list('gallery_id', 'rating')
            # Преобразуем в словарь: {gallery_id: rating}
            context['user_ratings_dict'] = dict(user_ratings)
        else:
            context['user_ratings_dict'] = {}

        # Добавляем ID просматриваемого пользователя в контекст для использования в шаблоне
        context['viewed_user_id'] = self.kwargs.get('user_id')
        return context


class AddImagesView(CreateView):
    model = Gallery
    form_class = AddImageForms
    template_name = 'gallery/add_images.html'
    success_url = reverse_lazy('gallery:gallery_list')

    def form_valid(self, form):
        # Проверяем, есть ли файл в поле image
        image_file = self.request.FILES.get('image')
        if not image_file:
            # Добавляем ошибку в форму, если файл не выбран
            form.add_error('image', 'Пожалуйста, выберите изображение для загрузки.')
            return self.form_invalid(form)

        # Если пользователь авторизован, устанавливаем его как автора
        if self.request.user.is_authenticated:
            form.instance.author = self.request.user

        response = super().form_valid(form)
        messages.success(self.request, 'Изображение успешно загружено!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при загрузке изображения. Проверьте форму.')
        return super().form_invalid(form)


@login_required
def gallery_detail(request, pk):
    gallery = get_object_or_404(Gallery, pk=pk)
    user_rating = None

    if request.user.is_authenticated:
        try:
            rating = GalleryRating.objects.get(gallery=gallery, user=request.user)
            user_rating = rating.rating
        except GalleryRating.DoesNotExist:
            pass

    return render(request, 'gallery/gallery_detail.html', {
        'gallery': gallery,
        'user_rating': user_rating
    })


@login_required
def gallery_detail_user(request, pk):
    gallery = get_object_or_404(Gallery, pk=pk)
    user_rating = None

    if request.user.is_authenticated:
        try:
            rating = GalleryRating.objects.get(gallery=gallery, user=request.user)
            user_rating = rating.rating
        except GalleryRating.DoesNotExist:
            pass

    return render(request, 'gallery/gallery_detail.html', {
        'gallery': gallery,
        'user_rating': user_rating
    })


@require_POST
@login_required
def rate_gallery(request, gallery_id, rating_type):
    """Обработчик для оценки галереи с сохранением истории"""
    if rating_type not in ['like', 'dislike']:
        return redirect(request.META.get('HTTP_REFERER', 'gallery:gallery_list'))

    gallery = get_object_or_404(Gallery, id=gallery_id)

    # Запрет оценки своих галерей
    if gallery.author.id == request.user.id:
        return redirect(request.META.get('HTTP_REFERER', 'gallery:gallery_list'))

    existing_rating = GalleryRating.objects.filter(
        gallery=gallery,
        user=request.user
    ).first()

    if existing_rating:
        if existing_rating.rating == rating_type:
            # Если пользователь отменяет свою оценку
            existing_rating.delete()
            new_rating = None
        else:
            # Если меняет лайк на дизлайк или наоборот
            existing_rating.rating = rating_type
            existing_rating.save()
            new_rating = rating_type
    else:
        # Создаём новую оценку
        GalleryRating.objects.create(
            gallery=gallery,
            user=request.user,
            rating=rating_type
        )
        new_rating = rating_type

    # Обновляем счётчики галереи
    likes = gallery.ratings.filter(rating='like').count()
    dislikes = gallery.ratings.filter(rating='dislike').count()
    gallery.likes_count = likes
    gallery.dislikes_count = dislikes
    gallery.save()

    # Обновляем статистику пользователя
    request.user.update_rating_stats()

    return redirect(request.META.get('HTTP_REFERER', 'gallery:gallery_list'))


@login_required
def user_ratings_history(request):
    # Получаем все оценки пользователя
    user_ratings = GalleryRating.objects.filter(user=request.user).select_related('gallery', 'gallery__author')

    # Пагинация: 9 элементов на страницу
    paginator = Paginator(user_ratings, 6)
    page_number = request.GET.get('page', 1)

    try:
        ratings_page = paginator.get_page(page_number)
    except EmptyPage:
        # Если запрошена страница за пределами диапазона, вернуть последнюю
        ratings_page = paginator.get_page(paginator.num_pages)

    context = {
        'ratings_page': ratings_page,
        'total_ratings': user_ratings.count(),
        'is_paginated': ratings_page.has_other_pages(),
        'page_obj': ratings_page,
    }

    return render(request, 'gallery/user_ratings_history.html', context)


@login_required
def delete_gallery(request, gallery_id):
    """Удаление изображения автором"""
    gallery = get_object_or_404(Gallery, id=gallery_id)

    # Проверка, что текущий пользователь — автор изображения
    if gallery.author != request.user:
        messages.error(request, 'Вы не являетесь автором этого изображения и не можете его удалить.')
        return HttpResponseRedirect(reverse('gallery_detail', args=[gallery_id]))

    if request.method == 'POST':
        # Сохраняем ID для сообщения
        gallery_id = gallery.id
        gallery.delete()
        messages.success(request, f'Изображение №{gallery_id} успешно удалено.')
        # return HttpResponseRedirect(reverse('users/gallery/'))
        return redirect(reverse('gallery:gallery_list'))

    # Если GET-запрос, просто показываем страницу с подтверждением
    return render(request, 'gallery/delete_confirm.html', {
        'gallery': gallery
    })
