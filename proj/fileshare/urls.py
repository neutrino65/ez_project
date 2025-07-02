"""
URL configuration for fileshare project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from api import views
from django.http import HttpResponse

def homepage(request):
    return HttpResponse('<h1>Welcome to the Secure File Sharing API</h1><p>Visit /admin/ for admin or use the API endpoints under /api/</p>')

urlpatterns = [
    path('', homepage, name='homepage'),
    # Client User
    path('admin/', admin.site.urls),
    path('api/client/signup/', views.ClientSignUpView.as_view(), name='client-signup'),
    path('api/client/verify-email/', views.ClientVerifyEmailView.as_view(), name='client-verify-email'),
    path('api/client/login/', views.UserLoginView.as_view(), name='client-login'),
    path('api/client/files/', views.ClientFileListView.as_view(), name='client-list-files'),
    path('api/client/download/<str:assignment_id>/', views.ClientDownloadLinkView.as_view(), name='client-download-link'),
    path('api/client/download-file/<str:token>/', views.ClientDownloadFileView.as_view(), name='client-download-file'),
    # Ops User
    path('api/ops/login/', views.UserLoginView.as_view(), name='ops-login'),
    path('api/ops/upload/', views.OpsFileUploadView.as_view(), name='ops-upload'),
]
