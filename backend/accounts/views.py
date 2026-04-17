"""Account views: register, login, logout, me, profile update."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.conf import settings
from .serializers import (
    RegisterSerializer, AdminRegisterSerializer, LoginSerializer,
    UserSerializer, ChangePasswordSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_register(request, secret_key):
    """Register a new admin account (protected by secret key in URL)."""
    expected_key = getattr(settings, 'ADMIN_SIGNUP_SECRET', 'au-admin-secret-2026')
    if secret_key != expected_key:
        return Response({'error': 'Invalid signup link.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = AdminRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new student account."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login with matric + password, returns token."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Delete token to logout."""
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'detail': 'Logged out.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return authenticated user's profile."""
    return Response(UserSerializer(request.user).data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update profile fields or change password."""
    user = request.user

    # Password change
    if 'old_password' in request.data and 'new_password' in request.data:
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password updated.'})

    # Profile field update
    serializer = UserSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
