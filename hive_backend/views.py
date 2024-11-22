from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts, FollowedUsers, Comment
from .serializers import (
    PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer,
    LikedPostsSerializer, FollowedUsersSerializer,
    UserRegistrationSerializer, CustomTokenObtainPairSerializer, CommentSerializer
)

from rest_framework import status
from rest_framework import generics

# Get a custom user template
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):  # Vaihdettu ReadOnly -> ModelViewSet
# Retrieves all records of the User model from the database and stores them in the queryset variable.
    queryset = User.objects.all()
    # Specifies that the serializer used in that view is the `UserSerializer`,
    # which converts instances of the `User` model.
    serializer_class = None
    # Specifies that the view can only make requests if the user is logged in and authenticated,
    # because the `IsAuthenticated` class checks that the user is authenticated.
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import UserSerializer
        return UserSerializer

    # Defines a custom `GET` function for route `me`,
    # which is not related to a single resource,
    # but provides information about, for example, the current user.
    @action(detail=False, methods=["get"], url_path="me")
    def get_me(self, request):
        """Searching for logged-in user information."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

# Defines the `UserRegistrationView` class, which inherits the `APIView` class from the Django Rest Framework
# and allows the user registration process to be handled in the API.
class UserRegistrationView(APIView):
    def post(self, request):
        # Creates a `UserRegistrationSerializer` serializer and feeds it the `request.data` data,
        # which contains the information needed to register the user, such as e-mail and password.
        from .serializers import UserRegistrationSerializer
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
    filter_backends = [DjangoFilterBackend]  # Filter feature enabled
    filterset_fields = ['user']  # Allows filtering based on user

    def perform_create(self, serializer):
        """Allow user selection in request data."""
        serializer.save()

    def get_queryset(self):
        """Search by title or description."""
        queryset = super().get_queryset()
        query = self.request.query_params.get("search", None)
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return queryset

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="search")
    def search_hashtags(self, request):
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
        """Estä saman käyttäjän tykkäyksen luominen useasti."""
        liker = request.data.get('liker')
        liked_user = request.data.get('liked_user')

        if LikedUsers.objects.filter(liker_id=liker, liked_user_id=liked_user).exists():
            return Response({"detail": "Olet jo tykännyt tästä käyttäjästä."}, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)


# FollowedHashtags ViewSet
class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()
    serializer_class = FollowedHashtagsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set the logged in user as a follower."""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Estä saman käyttäjän seuraamisen useasti."""
        user = request.data.get('user')
        hashtag = request.data.get('hashtag')

        if FollowedHashtags.objects.filter(user_id=user, hashtag_id=hashtag).exists():
            return Response({"detail": "You have already liked this hashtag."}, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="my-followed")
    def get_my_followed(self, request):
        """Search hashtags followed by a logged in user."""
        hashtags = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(hashtags, many=True)
        return Response(serializer.data)



# FollowedUsers ViewSet
class FollowedUsersViewSet(viewsets.ModelViewSet):
    queryset = FollowedUsers.objects.all()
    serializer_class = FollowedUsersSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="my-followed-users")
    def get_my_followed_users(self, request):
        """Search for users that the logged in user follows."""
        followed_users = self.queryset.filter(follower=request.user)
        serializer = self.get_serializer(followed_users, many=True)
        return Response(serializer.data)


# LikedPosts ViewSet
class LikedPostsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LikedPosts.objects.all()
    serializer_class = LikedPostsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="my-likes")
    def get_my_likes(self, request):
        """Search for posts liked by the logged in user."""
        liked_posts = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(liked_posts, many=True)
        return Response(serializer.data)
    

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-time')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set the comment post and user automatically."""
        post = Post.objects.get(id=self.request.data['post'])  # Get the post
        serializer.save(user=self.request.user, post=post)

    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_comment(self, request, pk=None):
        """Removal of comment"""
        comment = self.get_object()
        if comment.user != request.user:
            return Response({"detail": "Vain kommentin tekijä voi poistaa kommentin."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"detail": "Kommentti poistettu onnistuneesti."}, status=status.HTTP_200_OK)

# List and create comments
class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

# Retrieves, updates, or deletes a single comment
class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
