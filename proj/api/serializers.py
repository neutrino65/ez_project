from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FileUpload
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            role=validated_data['role'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ('id', 'uploader', 'file', 'uploaded_at', 'assignment_id')
        read_only_fields = ('uploader', 'uploaded_at', 'assignment_id')

    def create(self, validated_data):
        user = self.context['request'].user
        file_obj = validated_data['file']
        ext = file_obj.name.split('.')[-1].lower()
        if ext not in FileUpload.allowed_types:
            raise serializers.ValidationError('Only pptx, docx, and xlsx files are allowed.')
        import uuid
        assignment_id = uuid.uuid4().hex
        return FileUpload.objects.create(
            uploader=user,
            file=file_obj,
            assignment_id=assignment_id
        )

class FileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ('assignment_id', 'file', 'uploaded_at') 