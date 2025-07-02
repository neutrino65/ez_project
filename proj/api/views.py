from django.shortcuts import render
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from .models import FileUpload, User
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    FileUploadSerializer, FileListSerializer
)
import uuid

signer = TimestampSigner()

# Create your views here.

# Client User Signup
class ClientSignUpView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['role'] = 'client'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Send verification email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = signer.sign(user.email)
        verify_url = request.build_absolute_uri(
            reverse('client-verify-email') + f'?uid={uid}&token={token}'
        )
        send_mail(
            'Verify your email',
            f'Click to verify: {verify_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        return Response({'verify_url': verify_url, 'message': 'success'}, status=201)

# Email Verification
class ClientVerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        uid = request.GET.get('uid')
        token = request.GET.get('token')
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid, role='client')
            signer.unsign(token, max_age=60*60*24)  # 24 hours
            user.email_verified = True
            user.save()
            return Response({'message': 'Email verified successfully.'})
        except (User.DoesNotExist, BadSignature, SignatureExpired):
            return Response({'message': 'Invalid or expired verification link.'}, status=400)

# Login (Ops & Client)
class UserLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user is not None:
            if user.role == 'client' and not user.email_verified:
                return Response({'message': 'Email not verified.'}, status=403)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': user.role
            })
        return Response({'message': 'Invalid credentials.'}, status=401)

# Ops User File Upload
class OpsFileUploadView(generics.CreateAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'ops':
            return Response({'message': 'Only Ops users can upload files.'}, status=403)
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

# Client User List Files
class ClientFileListView(generics.ListAPIView):
    serializer_class = FileListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FileUpload.objects.all()

    def list(self, request, *args, **kwargs):
        if request.user.role != 'client':
            return Response({'message': 'Only client users can list files.'}, status=403)
        return super().list(request, *args, **kwargs)

# Client User Get Secure Download Link
class ClientDownloadLinkView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, assignment_id):
        if request.user.role != 'client':
            return Response({'message': 'Only client users can get download links.'}, status=403)
        try:
            file_obj = FileUpload.objects.get(assignment_id=assignment_id)
            token = signer.sign(f'{file_obj.assignment_id}:{request.user.pk}')
            download_url = request.build_absolute_uri(
                reverse('client-download-file', args=[token])
            )
            return Response({'download-link': download_url, 'message': 'success'})
        except FileUpload.DoesNotExist:
            return Response({'message': 'File not found.'}, status=404)

# Client User Download File
from django.http import FileResponse
class ClientDownloadFileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, token):
        try:
            value = signer.unsign(token, max_age=60*30)  # 30 minutes
            assignment_id, user_pk = value.split(':')
            if str(request.user.pk) != user_pk or request.user.role != 'client':
                return Response({'message': 'Access denied.'}, status=403)
            file_obj = FileUpload.objects.get(assignment_id=assignment_id)
            response = FileResponse(file_obj.file.open('rb'), as_attachment=True, filename=file_obj.file.name)
            return response
        except (BadSignature, SignatureExpired, FileUpload.DoesNotExist):
            return Response({'message': 'Invalid or expired download link.'}, status=400)
