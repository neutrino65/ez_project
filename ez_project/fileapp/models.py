from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from datetime import datetime, timedelta
import hashlib
import os

class User(AbstractUser):
    USER_TYPES = (
        ('ops', 'Operations User'),
        ('client', 'Client User'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.email_verification_token and self.user_type == 'client':
            self.email_verification_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

class UploadedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.original_filename} by {self.uploaded_by.username}"

class SecureDownloadToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    created_for = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            # Create a secure token using file ID + user ID + timestamp
            raw_string = f"{self.file.id}{self.created_for.id}{datetime.now().timestamp()}"
            self.token = hashlib.sha256(raw_string.encode()).hexdigest()
        
        if not self.expires_at:
            # Token expires in 1 hour
            self.expires_at = datetime.now() + timedelta(hours=1)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return datetime.now() > self.expires_at

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('ops', 'Ops User'),
        ('client', 'Client User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.user_type})"

def user_directory_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.uploader.id}/{filename}'

class FileUpload(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=255)

    def __str__(self):
        return self.original_filename

