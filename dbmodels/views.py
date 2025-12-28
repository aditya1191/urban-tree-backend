from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from .models import UserProfile
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    LoginSerializer, 
    RegisterSerializer,
    UpdateRoleSerializer
)


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users to access certain views."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'userprofile') and \
               request.user.userprofile.role == 'admin'


# --- 1. NEW DEDICATED CSRF VIEW ---
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    """
    Handshake view to get the CSRF token.
    React calls this first to populate the 'X-CSRFToken' header.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # 'get_token' ensures the cookie is generated if it doesn't exist
        token = get_token(request)
        return Response({
            'csrfToken': token, 
            'detail': 'CSRF token generated'
        })


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing User instances."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing UserProfile instances."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class RegisterView(APIView):
    """Register a new user and create their profile."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            profile = UserProfile.objects.create(
                user=user,
                role=request.data.get('role', 'viewer')
            )
            # Optional: Log them in immediately after registration
            # login(request, user)
            
            return Response({
                'user': UserSerializer(user).data,
                'profile': UserProfileSerializer(profile).data, 
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Authenticate user and track login time."""
    permission_classes = [permissions.AllowAny]
    
    # Removed the 'get' method. Use CsrfTokenView for the handshake.
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                login(request, user)
                # 1. Get the NEW token
                new_csrf_token = get_token(request)
                
                try:
                    profile = UserProfile.objects.get(user=user)
                    profile.last_login_time = timezone.now()
                    profile.save()
                except UserProfile.DoesNotExist:
                    # Fallback if profile is missing for some reason
                    profile = UserProfile.objects.create(user=user, role='viewer')

                return Response({
                    'user': UserSerializer(user).data,
                    'profile': UserProfileSerializer(profile).data,
                    'csrfToken': new_csrf_token, # <--- CRITICAL ADDITION
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'Invalid credentials'}, 
                          status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Log out user and track logout time."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.last_logout_time = timezone.now()
            profile.save()
            logout(request)
            return Response({'message': 'Logout successful'}, 
                          status=status.HTTP_200_OK)
        except Exception as e:
            # Fallback logout even if profile update fails
            logout(request)
            return Response({'error': str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)


class CurrentUserProfileView(APIView):
    """Get the current authenticated user's profile."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            return Response({
                'user': UserSerializer(request.user).data,
                'profile': UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, 
                          status=status.HTTP_404_NOT_FOUND)


class UpdateUserRoleView(APIView):
    """Update a user's role. Only admins can access this endpoint."""
    permission_classes = [IsAdminUser]
    
    def patch(self, request, user_id):
        serializer = UpdateRoleSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=user_id)
                profile = UserProfile.objects.get(user=user)
                profile.role = serializer.validated_data['role']
                profile.save()
                
                return Response({
                    'user': UserSerializer(user).data,
                    'profile': UserProfileSerializer(profile).data,
                    'message': 'Role updated successfully'
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
            except UserProfile.DoesNotExist:
                return Response({'error': 'Profile not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)