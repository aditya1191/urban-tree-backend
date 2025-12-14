from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')

app_name = 'dbmodels'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/csrf/', views.LoginView.as_view(), name='get-csrf-token'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('profile/me/', views.CurrentUserProfileView.as_view(), name='current-profile'),
    path('profile/update-role/<int:user_id>/', views.UpdateUserRoleView.as_view(), name='update-role'),
]
