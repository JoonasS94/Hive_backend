from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, PostViewSet, HashtagViewSet,
    LikedUsersViewSet, FollowedHashtagsViewSet, LikedPostsViewSet
)

# Set up the Swagger schema view
schema_view = get_schema_view(
   openapi.Info(
      title="API Documentation",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@myapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Create the router and register the viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'posts', PostViewSet)
router.register(r'hashtags', HashtagViewSet)
router.register(r'liked-users', LikedUsersViewSet)
router.register(r'followed-hashtags', FollowedHashtagsViewSet)
router.register(r'liked-posts', LikedPostsViewSet)

# Define the URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', include(router.urls)),  # Include the viewset routes
    
    # Add the filter-by-hashtags route explicitly
    path('posts/filter-by-hashtags/', PostViewSet.as_view({'get': 'filter_by_hashtags'}), name='filter-by-hashtags'),
]
