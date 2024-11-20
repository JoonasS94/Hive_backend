from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from .serializers import (
    UserSerializer, PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, LikedPostsSerializer
)
#uutta

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

# Hashtag ViewSet
class HashtagViewSet(viewsets.ModelViewSet):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = [IsAuthenticated]

# LikedUsers ViewSet
class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()
    serializer_class = LikedUsersSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Tarkistetaan, onko suhde jo olemassa
        liker = request.data.get('liker')
        liked_user = request.data.get('liked_user')

        if LikedUsers.objects.filter(liker_id=liker, liked_user_id=liked_user).exists():
            # Jos merkintä on jo olemassa, palautetaan 200-koodinen vastaus
            return Response(
                {"detail": "You already like this user."},
                status=status.HTTP_200_OK
            )
        
        # Jos merkintää ei ole, jatketaan normaalisti
        return super().create(request, *args, **kwargs)

# FollowedHashtags ViewSet
class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()
    serializer_class = FollowedHashtagsSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # Hae käyttäjä
        user = self.get_object().user

        # Laske, kuinka monta hashtagiä käyttäjä seuraa
        followed_hashtags_count = FollowedHashtags.objects.filter(user=user).count()

        # Palauta vastaus, joka sisältää seuraamien hashtagien määrän
        return Response({
            'user': user.id,
            'amount_of_followed_hashtags': followed_hashtags_count
        })

# LikedPosts ViewSet
class LikedPostsViewSet(viewsets.ModelViewSet):
    queryset = LikedPosts.objects.all()
    serializer_class = LikedPostsSerializer
    permission_classes = [IsAuthenticated]
