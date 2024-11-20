from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts, FollowedUsers
from django.contrib.auth.hashers import make_password

User = get_user_model()

# UserRegistrationSerializer
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
        return make_password(value)  # Hash the password

# HashtagSerializer
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']

# UserSerializer
class UserSerializer(serializers.ModelSerializer):
    amount_of_liked_users = serializers.SerializerMethodField()  # Number of users this user has liked
    amount_of_me_liked_users = serializers.SerializerMethodField()  # Number of users who have liked this user
    amount_of_followed_hashtags = serializers.SerializerMethodField()  # Count of followed hashtags
    id_and_name_of_followed_hashtags = serializers.SerializerMethodField()  # ID and name of followed hashtags
    posts_count = serializers.SerializerMethodField()  # Count of posts created by the user
    liked_posts_count = serializers.SerializerMethodField()  # Count of liked posts by the user

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'bio',
            'amount_of_liked_users', 'amount_of_me_liked_users',
            'amount_of_followed_hashtags', 'id_and_name_of_followed_hashtags',
            'posts_count', 'liked_posts_count'
        ]

    def get_amount_of_liked_users(self, obj):
        return LikedUsers.objects.filter(liker=obj).count()

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

class PostSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True)  # Nested Hashtag serializer
    references = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Post
        fields = ['id', 'text', 'time', 'user', 'hashtags', 'references']

    def to_representation(self, instance):
        """Muuntaa datan luettavampaan muotoon vastauksessa."""
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

        # Ota käyttäjä validated_data:sta tai requestin kontekstista
        user = validated_data.pop('user', self.context['request'].user)

        # Luo postaus
        post = Post.objects.create(user=user, **validated_data)

        # Käy läpi hashtagit ja lisää ne
        for hashtag_data in hashtags_data:
            hashtag_name = hashtag_data.get('name')
            if not hashtag_name:
                continue  # Ohitetaan tyhjät nimet

            # Käytetään get_or_create-metodia, jotta luodaan vain, jos hashtagi ei ole olemassa
            hashtag, created = Hashtag.objects.get_or_create(name=hashtag_name)
            post.hashtags.add(hashtag)

        # Lisää referenssit
        post.references.set(references_data)

        return post

    def update(self, instance, validated_data):
        hashtags_data = validated_data.pop('hashtags', None)
        references_data = validated_data.pop('references', None)

        # Päivitä postauksen teksti
        instance.text = validated_data.get('text', instance.text)
        instance.save()

        if hashtags_data is not None:
            # Tyhjennä ja lisää hashtagit uudestaan
            instance.hashtags.clear()
            for hashtag_data in hashtags_data:
                hashtag_name = hashtag_data.get('name')
                if not hashtag_name:
                    continue

                # Käytä get_or_create-metodia ennen hashtagien lisäämistä
                hashtag, created = Hashtag.objects.get_or_create(name=hashtag_name)
                instance.hashtags.add(hashtag)

        if references_data is not None:
            # Päivitä referenssit
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

# FollowedUsersSerializer
class FollowedUsersSerializer(serializers.ModelSerializer):
    follower = serializers.StringRelatedField()  # Vaihtoehtoisesti voit käyttää CustomUserSerializeria
    followed_user = serializers.StringRelatedField()

    class Meta:
        model = FollowedUsers
        fields = ['follower', 'followed_user']
