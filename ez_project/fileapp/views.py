from rest_framework import generics, status, permissions, views
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import UserProfile, FileUpload
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, FileUploadSerializer, UserProfileSerializer
)
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework.parsers import MultiPartParser, FormParser
import base64
import hashlib
import hmac
import time

# Helper for encrypted URL
def generate_encrypted_url(user_id, file_id, secret=None, expires_in=600):
    if not secret:
        secret = settings.SECRET_KEY
    expires = int(time.time()) + expires_in
    data = f"{user_id}:{file_id}:{expires}"
    sig = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{data}:{sig}".encode()).decode()
    return token

def decode_encrypted_url(token, secret=None):
    if not secret:
        secret = settings.SECRET_KEY
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, file_id, expires, sig = decoded.rsplit(':', 3)
        data = f"{user_id}:{file_id}:{expires}"
        expected_sig = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        if int(expires) < int(time.time()):
            return None
        return int(user_id), int(file_id)
    except Exception:
        return None

# Permissions
class IsOpsUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'ops'

class IsClientUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'client'

# Ops User: Login
class OpsLoginView(views.APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        if not hasattr(user, 'userprofile') or user.userprofile.user_type != 'ops':
            return Response({'error': 'Not an Ops User'}, status=403)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

# Ops User: Upload File
class FileUploadView(generics.CreateAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsOpsUser]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

# Client User: Sign Up
class ClientSignUpView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        profile = user.userprofile
        if profile.user_type != 'client':
            return Response({'error': 'Only client users can sign up here.'}, status=400)
        # Generate encrypted URL
        token = generate_encrypted_url(user.id, 0, expires_in=3600)
        verify_url = request.build_absolute_uri(reverse('client-verify-email', args=[token]))
        # Send email (console backend)
        send_mail(
            'Verify your email',
            f'Click to verify: {verify_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return Response({'verify_url': verify_url, 'message': 'Check your email for verification link.'})

# Client User: Email Verify
class ClientVerifyEmailView(views.APIView):
    def get(self, request, token):
        result = decode_encrypted_url(token)
        if not result:
            return Response({'error': 'Invalid or expired link.'}, status=400)
        user_id, _ = result
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        profile.email_verified = True
        profile.save()
        return Response({'message': 'Email verified successfully.'})

# Client User: Login
class ClientLoginView(views.APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        if not hasattr(user, 'userprofile') or user.userprofile.user_type != 'client':
            return Response({'error': 'Not a Client User'}, status=403)
        if not user.userprofile.email_verified:
            return Response({'error': 'Email not verified'}, status=403)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

# Client User: List Files
class FileListView(generics.ListAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def get_queryset(self):
        return FileUpload.objects.all()

# Client User: Download File (returns encrypted URL)
class DownloadFileLinkView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def get(self, request, pk):
        file = get_object_or_404(FileUpload, pk=pk)
        token = generate_encrypted_url(request.user.id, file.id, expires_in=600)
        download_url = request.build_absolute_uri(reverse('client-download-file', args=[token]))
        return Response({'download-link': download_url, 'message': 'success'})

# Actual file download endpoint
class DownloadFileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def get(self, request, token):
        result = decode_encrypted_url(token)
        if not result:
            return Response({'error': 'Invalid or expired link.'}, status=400)
        user_id, file_id = result
        if request.user.id != user_id or not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'client':
            return Response({'error': 'Access denied.'}, status=403)
        file = get_object_or_404(FileUpload, pk=file_id)
        response = FileResponse(file.file.open('rb'), as_attachment=True, filename=file.original_filename)
        return response

