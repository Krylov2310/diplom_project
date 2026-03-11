# WEB Form
from django.db.models import Q
from rest_framework.views import APIView
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied
from django.views.generic import UpdateView
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from friends.models import Friendship
# User Forms
from gallery.models import GalleryRating, Gallery
from .models import UserProfile
from .forms import EmailAuthenticationForm, CustomUserCreationForm, ProfileEditForm, CustomPasswordChangeForm, \
    UserProfileForm
# API Form
from .serializers import UserProfileSerializer, ProfileSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


# WEB Form
def index(request):
    template_name = 'users/index.html'
    return render(request, template_name)


def info(request):
    template_name = 'users/info.html'
    return render(request, template_name)


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.email}!')
            return redirect('/')
    else:
        form = EmailAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('/info/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def edit_password(request):
    # print('\033[31medit_password\033[0m')
    profile_form = ProfileEditForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        profile_form = ProfileEditForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        password_form = CustomPasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        # Обработка формы профиля
        if 'profile_submit' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Профиль успешно обновлён!')
                return redirect('/profile/pass/')
            else:
                messages.error(request, 'Ошибка при сохранении профиля. Проверьте поля.')

        # Обработка формы смены пароля
        elif 'password_submit' in request.POST:
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)  # Важно: обновляем сессию
                messages.success(request, 'Пароль успешно изменён!')
                return redirect('/profile/pass/')
            else:
                # Выводим ошибки формы пароля
                for field, errors in password_form.errors.items():
                    for error in errors:
                        print(error)
                messages.error(request, f'Поле "{field}": {error}')

    return render(request, 'users/edit_password.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user': request.user
    })


@login_required
def profile_detail(request, user_id):
    print('\033[31mprofile_detail\033[0m', user_id)
    profile_user = get_object_or_404(UserProfile, id=user_id)
    current_user = request.user

    # Подсчёт статистики (остаётся без изменений)
    total_images = Gallery.objects.filter(author=profile_user).count()
    total_likes_received = GalleryRating.objects.filter(
        gallery__author=profile_user,
        rating='like'
    ).count()
    total_dislikes_received = GalleryRating.objects.filter(
        gallery__author=profile_user,
        rating='dislike'
    ).count()
    total_ratings_given = GalleryRating.objects.filter(user=profile_user).count()

    # Проверка дружбы
    is_friend = False
    if current_user.is_authenticated and current_user != profile_user:
        is_friend = Friendship.objects.filter(
            from_user=current_user,
            to_user=profile_user,
            status='accepted'
        ).exists() or Friendship.objects.filter(
            from_user=profile_user,
            to_user=current_user,
            status='accepted'
        ).exists()

    # Получаем или создаём приватный чат между текущим пользователем и профилем
    chat_room_id = None
    chat_url = None
    if is_friend:
        try:
            from chat.services import get_or_create_private_chat
            chat_room = get_or_create_private_chat(current_user, profile_user)
            chat_room_id = chat_room.private_chat_id
            chat_url = f"/chat/{chat_room.id}/"
            print('chat_url', chat_url)
        except Exception as e:
            print(f"Ошибка при получении чата: {e}")

    context = {
        'profile_user': profile_user,
        'total_images': total_images,
        'total_likes_received': total_likes_received,
        'total_dislikes_received': total_dislikes_received,
        'total_ratings_given': total_ratings_given,
        'avatar_url': profile_user.get_avatar_url(),  # Добавляем URL аватара в контекст
        'is_friend': is_friend,
        'chat_room_id': chat_room_id,  # ID комнаты чата
        'chat_url': chat_url,  # URL для быстрого перехода
    }

    return render(request, 'users/profile_detail.html', context)


@login_required
def profile_edit(request, user_id):
    # print('\033[31mprofile_detail_edit\033[0m', user_id)
    user = get_object_or_404(UserProfile, id=user_id)

    # Проверяем, может ли текущий пользователь редактировать этот профиль
    can_edit = (request.user == user)
    # print('can_edit:', can_edit)

    if request.method == 'POST' and can_edit:
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # print('Форма валидна')
            # Сохраняем профиль
            user = form.save(commit=False)

            # Обрабатываем выбор аватара из галереи
            selected_avatar = form.cleaned_data.get('avatar_gallery_image')
            if selected_avatar:
                # Устанавливаем выбранное изображение как аватар
                user.avatar_gallery_image = selected_avatar
            else:
                # Если аватар не выбран, очищаем связь
                user.avatar_gallery_image = None

            user.save()
            messages.success(request, 'Профиль успешно обновлён!')
            redirect_url = reverse('users:profile_edit', args=[user_id])
            return HttpResponseRedirect(redirect_url)
        else:
            print('Форма невалидна:', form.errors)
            # Верните форму с ошибками в шаблон
            return render(request, 'users/profile_edit.html', {'form': form, 'can_edit': can_edit})
    else:
        # print('GET запрос или нет прав на редактирование')
        form = UserProfileForm(instance=user)

    return render(request, 'users/profile_edit.html', {
        'can_edit': can_edit,
        'form': form
    })


@login_required
def profile_list_view(request):
    """
    Представление для вывода списка пользователей в виде карточек
    """
    # Получаем параметры фильтрации из GET-запроса
    search_query = request.GET.get('search', '')
    gender_filter = request.GET.get('gender', '')
    city_filter = request.GET.get('city', '')
    age_filter = request.GET.get('age', '')

    # Начинаем с полного набора пользователей
    users = UserProfile.objects.all()

    # Применяем фильтры, если они указаны
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            # Q(is_active__icontains=search_query) |
            Q(age__icontains=search_query)
        )

    if gender_filter:
        users = users.filter(gender=gender_filter)

    if city_filter:
        users = users.filter(city__icontains=city_filter)

    if age_filter:
        users = users.filter(age__icontains=age_filter)

    # Пагинация
    per_page_options = list(range(3, 49, 3))  # 3, 6, 9, ..., 48
    per_page = int(request.GET.get('per_page', per_page_options[3]))  # Количество на страницу

    # print('\033[31mper_page\033[0m', per_page_options)
    paginator = Paginator(users, per_page)
    page = request.GET.get('page')

    try:
        user_list = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не число, показываем первую
        user_list = paginator.page(1)
    except EmptyPage:
        # Если страница вне диапазона, показываем последнюю
        user_list = paginator.page(paginator.num_pages)

    # Подсчёт общего количества сотрудников
    num_employees = users.count()

    context = {
        'object_list': user_list,
        'num_employees': num_employees,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'city_filter': city_filter,
        'age_filter': age_filter,
        'per_page_options': per_page_options,
        'per_page': per_page,
        'page_obj': user_list,  # Для пагинации
        'is_paginated': user_list.has_other_pages(),
    }

    return render(request, 'users/profile_list.html', context)


class ProfilesList(APIView):
    # print('\033[31mProfilesList\033[0m')

    def get(self, request, format=None):
        articles = UserProfile.objects.all()
        # print('\033[31marticles\033[0m', articles)
        # many=True Значит, список
        serializer = ProfileSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileUpdateView(UpdateView):
    # print('\033[31mProfileUpdateView\033[0m')
    model = UserProfile
    form_class = ProfileEditForm
    template_name = 'users/edit_profile.html'

    def dispatch(self, request, *args, **kwargs):
        # print('\033[31mdispatch\033[0m')
        # Проверяем, что редактируется именно профиль текущего пользователя
        if self.get_object() != request.user:
            raise PermissionDenied("Вы не имеете права редактировать этот профиль")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # print('\033[31mget_success_url\033[0m')
        return reverse_lazy('profile_detail', kwargs={'user_id': self.object.id})


# API Form
class UserProfileViewSet(viewsets.ModelViewSet):
    # print('\033[31mUserProfileViewSet\033[0m')
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]  # Добавляем защиту

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save()  # Сохраняем изменения, включая аватар

    def perform_create(self, serializer):
        # Явно передаём текущего пользователя перед сохранением
        serializer.save(user=self.request.user)


@login_required
def user_logout(request):
    print('\033[31muser_logout\033[0m')
    logout(request)
    template_name = 'users/index.html'
    return render(request, template_name)
