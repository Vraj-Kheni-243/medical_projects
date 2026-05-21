from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path, include
from django.shortcuts import render


def home(request):
    from doctors.models import Doctor
    featured_doctors = Doctor.objects.filter(available=True).select_related('user')[:6]
    return render(request, 'home.html', {'featured_doctors': featured_doctors})


def deploy_status(request):
    return JsonResponse({
        'app': 'VRAJ Care',
        'email_backend': settings.EMAIL_BACKEND,
        'default_from_email': settings.DEFAULT_FROM_EMAIL,
        'public_site_url': settings.PUBLIC_SITE_URL,
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('__deploy_status__/', deploy_status, name='deploy_status'),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('doctor/', include('doctors.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
