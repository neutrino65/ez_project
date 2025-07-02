from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ops', 'Ops User'),
        ('client', 'Client User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email_verified = models.BooleanField(default=False)

class FileUpload(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    assignment_id = models.CharField(max_length=64, unique=True)
    allowed_types = ['pptx', 'docx', 'xlsx']

    def save(self, *args, **kwargs):
        ext = self.file.name.split('.')[-1].lower()
        if ext not in self.allowed_types:
            raise ValueError('Only pptx, docx, and xlsx files are allowed.')
        super().save(*args, **kwargs)
