from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from .serializers import (
    UserSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer
)

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')  # Posts ordered by time
    serializer_class = PostSerializer

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
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer

# LikedUsers ViewSet
class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()
    serializer_class = LikedUsersSerializer

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
    queryset = FollowedHashtags.objects.all()
    serializer_class = FollowedHashtagsSerializer

# LikedPosts ViewSet
class LikedPostsViewSet(viewsets.ModelViewSet):
    queryset = LikedPosts.objects.all()
    serializer_class = LikedPostsSerializer
