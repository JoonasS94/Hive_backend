# Can use Django's default user-model with get_user_model .
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Count
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# Decentralize (= make default characters long wording) passwords.  
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts, FollowedUsers, Comment, CustomUser

# Retrieves the custom user model.
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


# UserRegistrationSerializer
# Validate and transform user data so it can be stored in a database.
class UserRegistrationSerializer(serializers.ModelSerializer):
    # What information is provided with GET-requests.
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'bio']
        # Define additional settings for fields (for exmaple field validation, password length)
        # without having to modify the template itself.
        extra_kwargs = {
            # Ensure the password is write-only
            'password': {'write_only': True},
        }

    # Make sure password is at least 8 characters long.
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        # Hash the password        
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
        """Retrieve the IDs of users this user has liked."""
        liked_users = LikedUsers.objects.filter(liker=obj).values_list('liked_user__id', flat=True)
        return [{"id": user_id} for user_id in liked_users]

    def get_amount_of_me_liked_users(self, obj):
        return LikedUsers.objects.filter(liked_user=obj).count()

    def get_amount_of_followed_hashtags(self, obj):
        """Count the number of hashtags this user follows."""
        return FollowedHashtags.objects.filter(user=obj).values('hashtag').distinct().count()

    def get_id_and_name_of_followed_hashtags(self, obj):
        """Retrieve the ID and name of hashtags this user follows."""
        followed_hashtags = FollowedHashtags.objects.filter(user=obj).select_related('hashtag')
        return [{"id": hashtag.hashtag.id, "name": hashtag.hashtag.name} for hashtag in followed_hashtags]

    def get_posts_count(self, obj):
        """Count the number of posts created by this user."""
        return Post.objects.filter(user=obj).count()

    def get_liked_posts_count(self, obj):
        """Count the number of posts liked by this user."""
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

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), required=False)
    text = serializers.CharField(max_length=144)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'user_name', 'text', 'time']

    def get_user_name(self, obj):
        """Gets the username comment for the user."""
        return obj.user.username if obj.user else None  # Returns the username or None if the user is missing

    def validate_text(self, value):
        """Comment text validation"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Kommentti ei voi olla tyhjä.")
        if len(value) > 144:
            raise serializers.ValidationError("Kommentin pituus ei saa ylittää 144 merkkiä.")
        return value


# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True)  # Nested Hashtag serializer
    references = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    comments = CommentSerializer(many=True, read_only=True)  # Add this to include comments in the post response
    comments_count = serializers.SerializerMethodField()  # Amount of comments field

    class Meta:
        model = Post
        fields = ['id', 'text', 'time', 'user', 'hashtags', 'references', 'comments', 'comments_count']

    def to_representation(self, instance):
        """Convert data to a more readable format in the response."""
        representation = super().to_representation(instance)
        representation['references'] = [
            {"id": user.id, "username": user.username}
            for user in instance.references.all()
        ]
        representation['user'] = {"id": instance.user.id, "username": instance.user.username}

        # Arrange the comments in descending chronological order (newest first)
        representation['comments'] = sorted(representation['comments'], key=lambda x: x['time'], reverse=True)

        return representation
    
    def get_comments_count(self, obj):
        """Counts the number of comments on the post."""
        return obj.comments.count()

    def create(self, validated_data):
        hashtags_data = validated_data.pop('hashtags', [])
        references_data = validated_data.pop('references', [])

        # Use the authenticated user as the post's user
        user = validated_data.pop('user', self.context['request'].user)

        # Create the post
        post = Post.objects.create(user=user, **validated_data)

        # Go through existing hashtag's and add a new one(s).
        for hashtag_data in hashtags_data:
            hashtag_name = hashtag_data.get('name')
            if hashtag_name:
                hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name)
                post.hashtags.add(hashtag)

            if not hashtag_name:
                continue  # Skip empty names

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
            # Clear and add hashtags again
            instance.hashtags.clear()
            for hashtag_data in hashtags_data:
                hashtag_name = hashtag_data.get('name')
                if hashtag_name:
                    hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name)
                    instance.hashtags.add(hashtag)
                if not hashtag_name:
                    continue

                # Use the get_or_create method before adding hashtags
                hashtag, created = Hashtag.objects.get_or_create(name=hashtag_name)
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
        fields = ['id', 'user', 'hashtag']


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


# New DeleteLikedUserSerializer
class DeleteLikedUserSerializer(serializers.Serializer):
    liker = serializers.IntegerField(required=True)
    liked_user = serializers.IntegerField(required=True)
