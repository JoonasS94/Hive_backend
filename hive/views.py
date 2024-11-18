from rest_framework import viewsets
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
    queryset = Post.objects.all()  # All posts
    serializer_class = PostSerializer  # Use the Post serializer

class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()  # All hashtags
    serializer_class = HashtagSerializer  # Use the Hashtag serializer

class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()  # All liked users
    serializer_class = LikedUsersSerializer  # Use the LikedUsers serializer

class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()  # All followed hashtags
    serializer_class = FollowedHashtagsSerializer  # Use the FollowedHashtags serializer

class LikedPostsViewSet(viewsets.ModelViewSet):
    queryset = LikedPosts.objects.all()  # All liked posts
    serializer_class = LikedPostsSerializer  # Use the LikedPosts serializer
