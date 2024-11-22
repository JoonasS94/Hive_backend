from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Count
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts, FollowedUsers

User = get_user_model()


# Custom Token Serializer to include user data in token response
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Call the parent method to get the token data
        data = super().validate(attrs)

        # Serialize the user object
        user_data = UserSerializer(self.user).data

        # Add the serialized user data to the token response
        data["user"] = user_data

        return data


# User Registration Serializer
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'bio']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure the password is write-only
        }

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return make_password(value)  # Hash the password before saving


# Hashtag Serializer
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    amount_of_liked_users = serializers.SerializerMethodField()  # Number of users this user has liked
    liked_user_id = serializers.SerializerMethodField()  # IDs of users this user has liked
    amount_of_me_liked_users = serializers.SerializerMethodField()  # Number of users who have liked this user
    amount_of_followed_hashtags = serializers.SerializerMethodField()  # Count of followed hashtags
    id_and_name_of_followed_hashtags = serializers.SerializerMethodField()  # ID and name of followed hashtags
    posts_count = serializers.SerializerMethodField()  # Count of posts created by the user
    liked_posts_count = serializers.SerializerMethodField()  # Count of liked posts by the user

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'bio',
            'amount_of_liked_users', 'liked_user_id',
            'amount_of_me_liked_users', 'amount_of_followed_hashtags',
            'id_and_name_of_followed_hashtags', 'posts_count', 'liked_posts_count',
            'date_joined',  # Included for GET requests
        ]
        read_only_fields = ['date_joined']  # Make date_joined read-only for updates

    def get_amount_of_liked_users(self, obj):
        return LikedUsers.objects.filter(liker=obj).count()

    def get_liked_user_id(self, obj):
        liked_users = LikedUsers.objects.filter(liker=obj).values_list('liked_user__id', flat=True)
        return [{"id": user_id} for user_id in liked_users]

    def get_amount_of_me_liked_users(self, obj):
        return LikedUsers.objects.filter(liked_user=obj).count()

    def get_amount_of_followed_hashtags(self, obj):
        return FollowedHashtags.objects.filter(user=obj).values('hashtag').distinct().count()

    def get_id_and_name_of_followed_hashtags(self, obj):
        followed_hashtags = FollowedHashtags.objects.filter(user=obj).select_related('hashtag')
        return [{"id": hashtag.hashtag.id, "name": hashtag.hashtag.name} for hashtag in followed_hashtags]

    def get_posts_count(self, obj):
        return Post.objects.filter(user=obj).count()

    def get_liked_posts_count(self, obj):
        return LikedPosts.objects.filter(user=obj).count()

    def to_internal_value(self, data):
        # Explicitly remove 'date_joined' from the incoming data for PUT/PATCH requests
        if 'date_joined' in data:
            del data['date_joined']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        # Customize the representation for GET requests to include date_joined
        representation = super().to_representation(instance)
        representation['date_joined'] = instance.date_joined.strftime('%Y-%m-%d %H:%M:%S')  # Customize the format if needed
        return representation




# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True)  # Nested Hashtag serializer
    references = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Post
        fields = ['id', 'text', 'time', 'user', 'hashtags', 'references']

    def to_representation(self, instance):
        """Convert data to a more readable format in the response."""
        representation = super().to_representation(instance)
        representation['references'] = [
            {"id": user.id, "username": user.username}
            for user in instance.references.all()
        ]
        representation['user'] = {"id": instance.user.id, "username": instance.user.username}
        return representation

    def create(self, validated_data):
        hashtags_data = validated_data.pop('hashtags', [])
        references_data = validated_data.pop('references', [])

        # Use the authenticated user as the post's user
        user = validated_data.pop('user', self.context['request'].user)

        # Create the post
        post = Post.objects.create(user=user, **validated_data)

        # Add hashtags
        for hashtag_data in hashtags_data:
            hashtag_name = hashtag_data.get('name')
            if hashtag_name:
                hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name)
                post.hashtags.add(hashtag)

        # Add references
        post.references.set(references_data)

        return post

    def update(self, instance, validated_data):
        hashtags_data = validated_data.pop('hashtags', None)
        references_data = validated_data.pop('references', None)

        # Update the post's text
        instance.text = validated_data.get('text', instance.text)
        instance.save()

        if hashtags_data is not None:
            instance.hashtags.clear()
            for hashtag_data in hashtags_data:
                hashtag_name = hashtag_data.get('name')
                if hashtag_name:
                    hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name)
                    instance.hashtags.add(hashtag)

        if references_data is not None:
            instance.references.set(references_data)

        return instance


# Liked Users Serializer
class LikedUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedUsers
        fields = ['liker', 'liked_user']


# Followed Hashtags Serializer
class FollowedHashtagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowedHashtags
        fields = ['user', 'hashtag']


# Liked Posts Serializer
class LikedPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedPosts
        fields = ['user', 'post']


# Followed Users Serializer
class FollowedUsersSerializer(serializers.ModelSerializer):
    follower = serializers.StringRelatedField()
    followed_user = serializers.StringRelatedField()

    class Meta:
        model = FollowedUsers
        fields = ['follower', 'followed_user']
