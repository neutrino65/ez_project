from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UploadedFile, UserProfile, FileUpload
import os

class UserRegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'user_type')

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, user_type=user_type)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Invalid credentials')

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ('id', 'file', 'original_filename', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at', 'original_filename')

    def validate_file(self, value):
        allowed_types = ['application/vnd.openxmlformats-officedocument.presentationml.presentation',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Only pptx, docx, and xlsx files are allowed.')
        return value

    def create(self, validated_data):
        validated_data['original_filename'] = validated_data['file'].name
        return super().create(validated_data)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('user_type', 'email_verified')

class FileListSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = UploadedFile
        fields = ['id', 'original_filename', 'file_size', 'uploaded_at', 'uploaded_by_name']

