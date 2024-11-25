from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from . import views
from .views import upload_file, delete_liked_user

# Import views
from .views import (
    UserViewSet, PostViewSet, HashtagViewSet,
    LikedUsersViewSet, FollowedHashtagsViewSet,
    UserRegistrationView, CustomTokenObtainPairView, CommentListCreateView, CommentRetrieveUpdateDestroyView
)

# Swagger Schema
schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version="v1",
        description="API for Hive Backend",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@myapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Create the router and register the viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename="user")
router.register(r'posts', PostViewSet, basename="post")
router.register(r'hashtags', HashtagViewSet, basename="hashtag")
router.register(r'liked-users', LikedUsersViewSet, basename="liked-user")
router.register(r'followed-hashtags', FollowedHashtagsViewSet, basename="followed-hashtag")

# Define the URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('', include(router.urls)),

    # Add comments-related routes
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentRetrieveUpdateDestroyView.as_view(), name='comment-retrieve-update-destroy'),

    # Adding pictures
    path('api/files/upload/', upload_file, name='upload_file'),

    # DELETE liked user
    path('liked-users/delete', views.delete_liked_user, name='delete_liked_user'),
]
