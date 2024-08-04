"""
URL configuration for kit_web_ui project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", views.index, name="index"),
    path("config", views.config, name="config"),
    path("config.json", views.config, name="config"),
    path("status", views.view_status, name="status"),
    path("runs/<str:user>", views.view_runs, name="runs"),
    path("recall/<str:run_uuid>", views.recall, name="recall"),
    path("logs/<str:run_uuid>", views.get_run_logs, name="run_logs"),
    path("run_bundle/<str:run_uuid>", views.generate_run_bundle, name="run_bundle"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
