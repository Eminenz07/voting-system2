"""Account serializers for registration, login, profile."""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['matric', 'first_name', 'last_name', 'email',
                  'faculty', 'department', 'password']

    def validate_matric(self, value):
        value = value.strip().upper()
        if User.objects.filter(matric=value).exists():
            raise serializers.ValidationError('This matric number is already registered.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    matric = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        matric = data['matric'].strip().upper()
        user = authenticate(username=matric, password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid matric number or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'matric', 'first_name', 'last_name', 'email',
                  'faculty', 'department', 'role', 'is_verified',
                  'full_name', 'date_joined']
        read_only_fields = ['id', 'matric', 'role', 'is_verified', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
