from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts, FollowedUsers
from .serializers import (
    UserSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer, FollowedUsersSerializer,
    UserRegistrationSerializer
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status

# Hae mukautettu käyttäjämalli
User = get_user_model()

# User ViewSet
class UserViewSet(viewsets.ReadOnlyModelViewSet):  # ReadOnly turvallisuussyistä
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def get_me(self, request):
        """Kirjautuneen käyttäjän tietojen haku."""
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
        """Salli käyttäjän valitseminen pyyntödatassa."""
        serializer.save()

    def get_queryset(self):
        """Haku otsikon tai kuvauksen perusteella."""
        queryset = super().get_queryset()
        query = self.request.query_params.get("search", None)
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return queryset

    @action(detail=True, methods=["post"], url_path="like")
    def like_post(self, request, pk=None):
        """Mahdollista postauksen tykkääminen."""
        post = self.get_object()
        user = request.user

        if LikedPosts.objects.filter(user=user, post=post).exists():
            return Response({"detail": "Olet jo tykännyt tästä postauksesta."}, status=400)

        LikedPosts.objects.create(user=user, post=post)
        return Response({"detail": "Postaus tykätty onnistuneesti."}, status=201)

    @action(detail=True, methods=["post"], url_path="unlike")
    def unlike_post(self, request, pk=None):
        """Mahdollista postauksen tykkäyksen poisto."""
        post = self.get_object()
        user = request.user

        liked_post = LikedPosts.objects.filter(user=user, post=post).first()
        if not liked_post:
            return Response({"detail": "Et ole tykännyt tästä postauksesta."}, status=400)

        liked_post.delete()
        return Response({"detail": "Tykkäys poistettu onnistuneesti."}, status=200)

# Hashtag ViewSet
class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="search")
    def search_hashtags(self, request):
        """Hae hashtageja nimen perusteella."""
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
        """Aseta kirjautunut käyttäjä seuraajaksi."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="my-followed")
    def get_my_followed(self, request):
        """Hae kirjautuneen käyttäjän seuraamat hashtagit."""
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
        """Hae käyttäjät, joita kirjautunut käyttäjä seuraa."""
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
        """Hae kirjautuneen käyttäjän tykkäämät postaukset."""
        liked_posts = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(liked_posts, many=True)
        return Response(serializer.data)
