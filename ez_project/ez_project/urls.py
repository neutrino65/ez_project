from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from fileapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Ops User
    path('api/ops/login/', views.OpsLoginView.as_view(), name='ops-login'),
    path('api/ops/upload/', views.FileUploadView.as_view(), name='ops-upload'),
    # Client User
    path('api/client/signup/', views.ClientSignUpView.as_view(), name='client-signup'),
    path('api/client/verify/<str:token>/', views.ClientVerifyEmailView.as_view(), name='client-verify-email'),
    path('api/client/login/', views.ClientLoginView.as_view(), name='client-login'),
    path('api/client/files/', views.FileListView.as_view(), name='client-list-files'),
    path('api/client/download-link/<int:pk>/', views.DownloadFileLinkView.as_view(), name='client-download-link'),
    path('api/client/download/<str:token>/', views.DownloadFileView.as_view(), name='client-download-file'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

