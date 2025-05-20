from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),
]

# Add media URL configuration for file downloads
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # For production, still serve media files through Django
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
