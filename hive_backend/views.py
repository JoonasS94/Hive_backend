from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView
import os
from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Post, Hashtag, LikedUsers, FollowedHashtags, Comment, CustomUser
from .serializers import (
    PostSerializer, HashtagSerializer,
    LikedUsersSerializer, FollowedHashtagsSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer, CommentSerializer
)

from rest_framework import status
from rest_framework import generics

from rest_framework.parsers import JSONParser

# Get a custom user template
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import UserSerializer
        return UserSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def get_me(self, request):
        """Searching for logged-in user information."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class UserRegistrationView(APIView):
    def post(self, request):
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


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-time')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']

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


class LikedUsersViewSet(viewsets.ModelViewSet):
    queryset = LikedUsers.objects.all()
    serializer_class = LikedUsersSerializer
    permission_classes = [IsAuthenticated]

    # Poistettu delete_by_fields action, koska se oli päällekkäinen delete_liked_user-funktion kanssa


class FollowedHashtagsViewSet(viewsets.ModelViewSet):
    queryset = FollowedHashtags.objects.all()
    serializer_class = FollowedHashtagsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set the logged in user as a follower."""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Estä saman käyttäjän seuraaminen useasti."""
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


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-time')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set the comment post and user automatically."""
        post = Post.objects.get(id=self.request.data['post'])
        serializer.save(user=self.request.user, post=post)

    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_comment(self, request, pk=None):
        """Removal of comment"""
        comment = self.get_object()
        if comment.user != request.user:
            return Response({"detail": "Vain kommentin tekijä voi poistaa kommentin."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"detail": "Kommentti poistettu onnistuneesti."}, status=status.HTTP_200_OK)


class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        content_type = file.content_type
        if content_type in ['image/gif', 'image/jpeg', 'image/png']:
            upload_dir = settings.UPLOAD_DIR
            file_path = os.path.join(upload_dir, file.name)

            with open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            return JsonResponse({'message': f'File uploaded successfully: {file.name}'})
        else:
            raise SuspiciousOperation(f'Unsupported filetype: {content_type}')
    else:
        return JsonResponse({'error': 'No file provided'}, status=400)


liker_param = openapi.Parameter(
    'liker', openapi.IN_BODY,
    description="ID of the user who liked",
    type=openapi.TYPE_INTEGER
)
liked_user_param = openapi.Parameter(
    'liked_user', openapi.IN_BODY,
    description="ID of the user who was liked",
    type=openapi.TYPE_INTEGER
)

@swagger_auto_schema(
    method='delete',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'liker': openapi.Schema(type=openapi.TYPE_INTEGER, description='Liker ID'),
            'liked_user': openapi.Schema(type=openapi.TYPE_INTEGER, description='Liked User ID'),
        },
        required=['liker', 'liked_user']
    ),
    responses={
        200: 'Like removed successfully',
        400: 'Bad Request',
        404: 'Not Found'
    }
)
@api_view(['DELETE'])
def delete_liked_user(request):
    try:
        data = request.data
        liker_id = data.get('liker')
        liked_user_id = data.get('liked_user')

        if not liker_id or not liked_user_id:
            return Response({"error": "Both 'liker' and 'liked_user' must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            liker = CustomUser.objects.get(id=liker_id)
            liked_user = CustomUser.objects.get(id=liked_user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "One or both users not found."}, status=status.HTTP_404_NOT_FOUND)

        like_instance = LikedUsers.objects.filter(
            Q(liker=liker) & Q(liked_user=liked_user)
        ).first()

        if like_instance:
            like_instance.delete()
            return Response({"message": "Like removed successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Like not found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
