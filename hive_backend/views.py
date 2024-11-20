from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts, FollowedUsers
from .serializers import (
    UserSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer, FollowedUsersSerializer
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from .serializers import UserRegistrationSerializer


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

    def get_queryset(self):
        """Allow searching for posts by title or description."""
        queryset = super().get_queryset()
        query = self.request.query_params.get("search", None)
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return queryset

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

    def create(self, request, *args, **kwargs):
        """Check if the like relationship already exists before creating a new one."""
        liker = request.data.get('liker')
        liked_user = request.data.get('liked_user')

        # Check if the like relationship already exists
        if LikedUsers.objects.filter(liker_id=liker, liked_user_id=liked_user).exists():
            # If the like already exists, return a 200 OK response
            return Response(
                {"detail": "You already like this user."},
                status=status.HTTP_200_OK
            )
        
        # If the like doesn't exist, proceed with the normal creation process
        return super().create(request, *args, **kwargs)


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

    @action(detail=True, methods=["get"], url_path="followed-count")
    def followed_hashtags_count(self, request, pk=None):
        """Retrieve the count of hashtags the user is following."""
        user = self.get_object().user
        followed_hashtags_count = FollowedHashtags.objects.filter(user=user).count()
        return Response({
            'user': user.id,
            'amount_of_followed_hashtags': followed_hashtags_count
        })

    # Lisätty retrieve-metodi
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single followed hashtag and the count of hashtags followed by the user."""
        instance = self.get_object()
        user = instance.user
        followed_hashtags_count = FollowedHashtags.objects.filter(user=user).count()
        return Response({
            'user': user.id,
            'amount_of_followed_hashtags': followed_hashtags_count
        })

# FollowedUsers ViewSet - Uusi toiminnallisuus
class FollowedUsersViewSet(viewsets.ModelViewSet):
    queryset = FollowedUsers.objects.all()
    serializer_class = FollowedUsersSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="my-followed-users")
    def get_my_followed_users(self, request):
        """Retrieve users followed by the logged-in user."""
        followed_users = self.queryset.filter(follower=request.user)
        serializer = self.get_serializer(followed_users, many=True)
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
