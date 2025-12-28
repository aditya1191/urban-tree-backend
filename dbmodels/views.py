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
from rest_framework.authtoken.models import Token # Import is crucial
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


# --- 1. CSRF VIEW (Still useful for initial handshake) ---
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    """
    Handshake view to get the CSRF token.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
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
            # 1. Check for Admin Role Security
            requested_role = request.data.get('role', 'viewer')
            final_role = 'viewer'
            
            # Only allow setting 'admin' role if the REQUESTER is already an admin
            # (Note: request.user might be anonymous here if public registration)
            if (request.user.is_authenticated and 
                hasattr(request.user, 'userprofile') and 
                request.user.userprofile.role == 'admin'):
                final_role = requested_role

            user = serializer.save()
            profile = UserProfile.objects.create(
                user=user,
                role=final_role
            )
            
            # 2. Generate Token immediately (Optional, helps if you want auto-login)
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'token': token.key, # Return token so frontend can auto-login if desired
                'user': UserSerializer(user).data,
                'profile': UserProfileSerializer(profile).data, 
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Authenticate user and return API Token."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                # 1. Standard Django Login (Maintains Session/CSRF capabilities)
                login(request, user)
                
                # 2. GET OR CREATE AUTH TOKEN (The Fix for Cross-Site Auth)
                token, created = Token.objects.get_or_create(user=user)
                
                # 3. Update Last Login Time
                try:
                    profile = UserProfile.objects.get(user=user)
                    profile.last_login_time = timezone.now()
                    profile.save()
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(user=user, role='viewer')

                # 4. Return Token + User Data
                return Response({
                    'token': token.key, # <--- SEND THIS TO REACT
                    'user': UserSerializer(user).data,
                    'profile': UserProfileSerializer(profile).data,
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'Invalid credentials'}, 
                          status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Log out user and invalidate Token."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # 1. Update Logout Time
            profile = UserProfile.objects.get(user=request.user)
            profile.last_logout_time = timezone.now()
            profile.save()
            
            # 2. Delete the Token (Invalidates the API Key)
            # This ensures the stolen token cannot be used again
            request.user.auth_token.delete()
            
            # 3. Standard Logout
            logout(request)
            
            return Response({'message': 'Logout successful'}, 
                          status=status.HTTP_200_OK)
        except Exception as e:
            # Even if something fails, try to logout
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