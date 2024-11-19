from rest_framework import serializers
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts

# Määritellään HashtagSerializer ennen PostSerializeria
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']  # Palautetaan sekä ID että nimi

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'bio', 'registered']

class PostSerializer(serializers.ModelSerializer):
    # Käytämme HashtagSerializeriä hashtags-kentässä
    hashtags = HashtagSerializer(many=True)  # Tämä palauttaa hashtagin ID:n ja nimen
    references = UserSerializer(many=True)  # Viittaukset käyttäjiin, lisätään myös UserSerializer

    class Meta:
        model = Post
        fields = ['id', 'text', 'time', 'user', 'hashtags', 'references']

class LikedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedUsers
        fields = ['liker', 'liked_user']

class FollowedHashtagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowedHashtags
        fields = ['user', 'hashtag']

class LikedPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedPosts
        fields = ['user', 'post']
