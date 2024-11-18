from rest_framework import serializers
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # Serialize all fields

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = '__all__'

class LikedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedUsers
        fields = '__all__'

class FollowedHashtagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowedHashtags
        fields = '__all__'

class LikedPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedPosts
        fields = '__all__'
