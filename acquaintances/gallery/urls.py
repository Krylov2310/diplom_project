from django.urls import path

from gallery.views import gallery_detail, GalleryListView, AddImagesView, rate_gallery, delete_gallery, \
    gallery_detail_user, UserGalleryView, user_ratings_history
from django.conf.urls.static import static
from django.conf import settings

app_name = 'gallery'

urlpatterns = [
                  # Gallery
                  path('<int:user_id>/gallery/user/', UserGalleryView.as_view(), name='gallery_user'),
                  path('gallery/', GalleryListView.as_view(), name='gallery_list'),
                  path('add-images/', AddImagesView.as_view(), name='add_images'),
                  path('gallery/<int:pk>/', gallery_detail, name='gallery_detail'),
                  path('gallery/<int:pk>/user/', gallery_detail_user, name='gallery_detail_user'),
                  path('<int:gallery_id>/rate/<str:rating_type>/', rate_gallery, name='rate_gallery'),
                  path('<int:gallery_id>/delete/', delete_gallery, name='delete_gallery'),
                  path('my-ratings/', user_ratings_history, name='user_ratings_history'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
