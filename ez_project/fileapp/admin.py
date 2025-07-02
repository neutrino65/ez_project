from django.contrib import admin
from .models import UserProfile, FileUpload

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(FileUpload)
