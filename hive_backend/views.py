from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserSerializer, UserRegistrationSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer
)

# Get the custom user model
User = get_user_model()

# User ViewSet
class UserViewSet(viewsets.ReadOnlyModelViewSet):  # Changed to ReadOnly for security
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def get_me(self, request):
        """Endpoint to retrieve the logged-in user's details."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "bio": user.bio
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Ensure the logged-in user is set as the post's owner."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="like")
    def like_post(self, request, pk=None):
        """Allow a user to like a post."""
        post = self.get_object()
        user = request.user

        # Check if the user has already liked the post
        if LikedPosts.objects.filter(user=user, post=post).exists():
            return Response({"detail": "You have already liked this post."}, status=400)

        # Create a new like
        LikedPosts.objects.create(user=user, post=post)
        return Response({"detail": "Post liked successfully."}, status=201)

    @action(detail=True, methods=["post"], url_path="unlike")
    def unlike_post(self, request, pk=None):
        """Allow a user to unlike a post."""
        post = self.get_object()
        user = request.user

        # Check if the user has liked the post
        liked_post = LikedPosts.objects.filter(user=user, post=post).first()
        if not liked_post:
            return Response({"detail": "You haven't liked this post."}, status=400)

        # Remove the like
        liked_post.delete()
        return Response({"detail": "Post unliked successfully."}, status=200)

# Hashtag ViewSet
class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="search")
    def search_hashtags(self, request):
        """Search for hashtags by name."""
        query = request.query_params.get("q", "")
        hashtags = self.queryset.filter(name__icontains=query)
        serializer = self.get_serializer(hashtags, many=True)
        return Response(serializer.data)

# LikedUsers ViewSet
class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()
    serializer_class = LikedUsersSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Ensure the liker is the logged-in user."""
        serializer.save(liker=self.request.user)

# FollowedHashtags ViewSet
class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()
    serializer_class = FollowedHashtagsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Ensure the follower is the logged-in user."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="my-followed")
    def get_my_followed(self, request):
        """Retrieve hashtags followed by the logged-in user."""
        hashtags = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(hashtags, many=True)
        return Response(serializer.data)

# LikedPosts ViewSet
class LikedPostsViewSet(viewsets.ReadOnlyModelViewSet):  # Changed to ReadOnly
    queryset = LikedPosts.objects.all()
    serializer_class = LikedPostsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="my-likes")
    def get_my_likes(self, request):
        """Retrieve posts liked by the logged-in user."""
        liked_posts = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(liked_posts, many=True)
        return Response(serializer.data)
