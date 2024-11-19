from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from .serializers import (
    UserSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer
)

# Create viewsets for each model
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # All users
    serializer_class = UserSerializer  # Use the User serializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')  # All posts, ordered by time (newest first)
    serializer_class = PostSerializer  # Use the Post serializer

class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()  # All hashtags
    serializer_class = HashtagSerializer  # Use the Hashtag serializer

class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()  # All liked users
    serializer_class = LikedUsersSerializer  # Use the LikedUsers serializer

    @action(detail=False, methods=['get'], url_path='count-likes')
    # Functionality for http://127.0.0.1:8000/liked-users/count-likes/?user_id=X
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

class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()  # All followed hashtags
    serializer_class = FollowedHashtagsSerializer  # Use the FollowedHashtags serializer

class LikedPostsViewSet(viewsets.ModelViewSet):
    queryset = LikedPosts.objects.all()  # All liked posts
    serializer_class = LikedPostsSerializer  # Use the LikedPosts serializer