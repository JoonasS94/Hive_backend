from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from .serializers import (
    UserSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer
)

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

# Create viewsets for each model
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # All users
    serializer_class = UserSerializer  # Use the User serializer
    permission_classes = [IsAuthenticated] # Require JWT Authentication

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')  # All posts, ordered by time (newest first)
    serializer_class = PostSerializer  # Use the Post serializer
    filter_backends = [DjangoFilterBackend]  # Enable filtering
    filterset_fields = ['hashtags']  # Allow filtering by hashtags

    # Custom action for filtering by multiple hashtags
    @action(detail=False, methods=['get'], url_path='filter-by-hashtags')
    def filter_by_hashtags(self, request):
        hashtags = request.query_params.getlist('hashtags')  # Ota vastaan useita häshtägejä listana
        if not hashtags:
            return Response({'error': 'Please provide at least one hashtag id.'}, status=400)

        # Sort for multiple queries
        posts = self.queryset.filter(
            Q(hashtags__id__in=hashtags)
        ).distinct()  # distinct estää duplikaattipostaukset

        # Serialize and return answer
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()  # All hashtags
    serializer_class = HashtagSerializer  # Use the Hashtag serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication

class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()  # All liked users
    serializer_class = LikedUsersSerializer  # Use the LikedUsers serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication

    # Functionality for http://127.0.0.1:8000/liked-users/count-likes/?user_id=X
    # Get to know how many users you liked.
    @action(detail=False, methods=['get'], url_path='count-likes')
    def count_likes(self, request):
        # Get the user_id from query parameters
        user_id = request.query_params.get('user_id', None)
        if user_id is None:
            return Response({'error': 'user_id parameter is required.'}, status=400)
        
        # Validate user_id as an integer
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be a valid integer.'}, status=400)
        
        # Count how many users the specified user has liked
        liked_count = LikedUsers.objects.filter(liker=user_id).count()
        return Response({'user_id': user_id, 'liked_count': liked_count})

    # Functionality for http://127.0.0.1:8000/liked-users/count-liked-by/?user_id=X
    # Get to know how many users likes you.
    @action(detail=False, methods=['get'], url_path='count-liked-by')
    def count_liked_by(self, request):
        # Get the user_id from query parameters
        user_id = request.query_params.get('user_id', None)
        if user_id is None:
            return Response({'error': 'user_id parameter is required.'}, status=400)
        
        # Validate user_id as an integer
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be a valid integer.'}, status=400)
        
        # Count how many users have liked the specified user
        liked_by_count = LikedUsers.objects.filter(liked_user=user_id).count()
        return Response({'user_id': user_id, 'liked_by_count': liked_by_count})

class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()  # All followed hashtags
    serializer_class = FollowedHashtagsSerializer  # Use the FollowedHashtags serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication

class LikedPostsViewSet(viewsets.ModelViewSet):
    queryset = LikedPosts.objects.all()  # All liked posts
    serializer_class = LikedPostsSerializer  # Use the LikedPosts serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication
