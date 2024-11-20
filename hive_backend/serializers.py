from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from django.contrib.auth.hashers import make_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'bio']  # Include desired fields
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure the password is write-only
        }

    def validate_password(self, value):
        # You can add custom password validation here
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return make_password(value)  # Hash the password

# Retrieve the custom User model
User = get_user_model()

# HashtagSerializer
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']  # Returns both ID and name

# UserSerializer
class UserSerializer(serializers.ModelSerializer):
    amount_of_liked_users = serializers.SerializerMethodField()  # Number of users this user has liked
    amount_of_me_liked_users = serializers.SerializerMethodField()  # Number of users who have liked this user

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'bio', 'amount_of_liked_users', 'amount_of_me_liked_users']

    def get_amount_of_liked_users(self, obj):
        # Count the number of users liked by this user
        return LikedUsers.objects.filter(liker=obj).count()

    def get_amount_of_me_liked_users(self, obj):
        # Count the number of users who have liked this user
        return LikedUsers.objects.filter(liked_user=obj).count()

# PostSerializer
class PostSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True)  # Nested Hashtag serializer
    references = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)  # References by user ID
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)  # User field for POST requests

    class Meta:
        model = Post
        fields = ['id', 'text', 'time', 'user', 'hashtags', 'references']

    def to_representation(self, instance):
        """Custom GET response"""
        representation = super().to_representation(instance)
        # Build references based on user IDs and usernames
        representation['references'] = [
            {
                "id": user.id,
                "username": user.username
            }
            for user in instance.references.all()
        ]
        # Include user details
        representation['user'] = {
            "id": instance.user.id,
            "username": instance.user.username
        }
        return representation

    def create(self, validated_data):
        hashtags_data = validated_data.pop('hashtags', [])
        references_data = validated_data.pop('references', [])
        user = self.context['request'].user  # Automatically set the current user

        # Create the post
        post = Post.objects.create(user=user, **validated_data)

        # Add hashtags
        for hashtag_data in hashtags_data:
            hashtag, created = Hashtag.objects.get_or_create(name=hashtag_data['name'])
            post.hashtags.add(hashtag)

        # Set references
        post.references.set(references_data)
        return post

    def update(self, instance, validated_data):
        hashtags_data = validated_data.pop('hashtags', None)
        references_data = validated_data.pop('references', None)

        # Update text fields
        instance.text = validated_data.get('text', instance.text)
        instance.save()

        # Update hashtags
        if hashtags_data is not None:
            instance.hashtags.clear()
            for hashtag_data in hashtags_data:
                hashtag, created = Hashtag.objects.get_or_create(name=hashtag_data['name'])
                instance.hashtags.add(hashtag)

        # Update references
        if references_data is not None:
            instance.references.set(references_data)

        return instance

# LikedUsersSerializer
class LikedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedUsers
        fields = ['liker', 'liked_user']

# FollowedHashtagsSerializer
class FollowedHashtagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowedHashtags
        fields = ['user', 'hashtag']

# LikedPostsSerializer
class LikedPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedPosts
        fields = ['user', 'post']
