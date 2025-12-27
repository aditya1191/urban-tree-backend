from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .UploadCSVFile import UploadCSVFile
from .TreeData import TreeData

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')
# Using DefaultRouter, don’t need to manually define each URL for CRUD operations. It automatically creates standard RESTful endpoints like:

# GET /users/ (list all users)
# POST /users/ (create new users)
# GET /users/{id}/ (retrieve a single users)
# PUT /users/{id}/ (update a users)
# DELETE /users/{id}/ (delete a users)

app_name = 'dbmodels'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/csrf/', views.CsrfTokenView.as_view(), name='csrf-token'), # <--- Add this line
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/me/', views.CurrentUserProfileView.as_view(), name='current-user'),
    # path('profile/me/', views.CurrentUserProfileView.as_view(), name='current-profile'),
    path('profile/update-role/<int:user_id>/', views.UpdateUserRoleView.as_view(), name='update-role'),
    path('upload-csv/', UploadCSVFile.as_view(), name='upload_csv'),
    path('treeData/', TreeData.as_view(), name='get_treeData')
]
