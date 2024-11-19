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

# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')  # All posts, ordered by time (newest first)
    serializer_class = PostSerializer  # Use the Post serializer
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

    # Functionality for fetching posts with a specific hashtag
    @action(detail=False, methods=['get'], url_path='with-hashtag')
    def posts_with_hashtag(self, request):
        hashtag_id = request.query_params.get('hashtag_id', None)
        if hashtag_id is None:
            return Response({"error": "hashtag_id is required."}, status=400)

        # Validate hashtag_id as integer
        try:
            hashtag_id = int(hashtag_id)
        except ValueError:
            return Response({"error": "hashtag_id must be a valid integer."}, status=400)

        # Fetch posts that have the specific hashtag
        posts = Post.objects.filter(hashtags__id=hashtag_id)

        # Serialize posts with Hashtags as ID + Name
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

# Hashtag ViewSet
class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()  # All hashtags
    serializer_class = HashtagSerializer  # Use the Hashtag serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication

# LikedUsers ViewSet
class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()  # All liked users
    serializer_class = LikedUsersSerializer  # Use the LikedUsers serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication

    # Count how many users you liked
    @action(detail=False, methods=['get'], url_path='count-likes')
    def count_likes(self, request):
        user_id = request.query_params.get('user_id', None)
        if user_id is None:
            return Response({'error': 'user_id parameter is required.'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be a valid integer.'}, status=400)
        
        liked_count = LikedUsers.objects.filter(liker=user_id).count()
        return Response({'user_id': user_id, 'liked_count': liked_count})

    # Count how many users like you
    @action(detail=False, methods=['get'], url_path='count-liked-by')
    def count_liked_by(self, request):
        user_id = request.query_params.get('user_id', None)
        if user_id is None:
            return Response({'error': 'user_id parameter is required.'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be a valid integer.'}, status=400)
        
        liked_by_count = LikedUsers.objects.filter(liked_user=user_id).count()
        return Response({'user_id': user_id, 'liked_by_count': liked_by_count})

# FollowedHashtags ViewSet
class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()  # All followed hashtags
    serializer_class = FollowedHashtagsSerializer  # Use the FollowedHashtags serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication

# LikedPosts ViewSet
class LikedPostsViewSet(viewsets.ModelViewSet):
    queryset = LikedPosts.objects.all()  # All liked posts
    serializer_class = LikedPostsSerializer  # Use the LikedPosts serializer
    permission_classes = [IsAuthenticated]  # Require JWT Authentication
