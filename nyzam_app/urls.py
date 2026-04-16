from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import get_user_model
from django.http import HttpResponse



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
    path('attendance/', include('attendance.urls')),
    path('create-admin/', create_admin),

]




def create_admin(request):
    User = get_user_model()

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@example.com", "admin123")
        return HttpResponse("Admin created")

    return HttpResponse("Admin already exists")



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
