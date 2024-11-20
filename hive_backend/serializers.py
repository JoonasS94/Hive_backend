from rest_framework import serializers
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
#uuta

# HashtagSerializer
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']  # Palautetaan sekä ID että nimi

class UserSerializer(serializers.ModelSerializer):
    amount_of_liked_users = serializers.SerializerMethodField()
    amount_of_me_liked_users = serializers.SerializerMethodField()
    amount_of_followed_hashtags = serializers.SerializerMethodField()  # Lisätty kenttä
    id_and_name_of_followed_hashtags = serializers.SerializerMethodField()  # Uusi kenttä

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'password', 'bio',
            'amount_of_liked_users', 'amount_of_me_liked_users',
            'amount_of_followed_hashtags', 'id_and_name_of_followed_hashtags'
        ]

    def get_amount_of_liked_users(self, obj):
        return LikedUsers.objects.filter(liker=obj).count()

    def get_amount_of_me_liked_users(self, obj):
        return LikedUsers.objects.filter(liked_user=obj).count()

    def get_amount_of_followed_hashtags(self, obj):
        return FollowedHashtags.objects.filter(user=obj).values('hashtag').distinct().count()

    def get_id_and_name_of_followed_hashtags(self, obj):
        followed_hashtags = FollowedHashtags.objects.filter(user=obj).select_related('hashtag')
        return [{"id": hashtag.hashtag.id, "name": hashtag.hashtag.name} for hashtag in followed_hashtags]


# PostSerializer
class PostSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True)  # Käytetään nested-hashtag serializeriä
    references = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)  # Viittaukset käyttäjä-ID:llä
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)  # Lisää käyttäjäkenttä POST-pyyntöön

    class Meta:
        model = Post
        fields = ['id', 'text', 'time', 'user', 'hashtags', 'references']

    def get_user(self, obj):
        """Palauttaa käyttäjän id:n ja nimen"""
        return {
            "id": obj.user.id,
            "username": obj.user.username
        }

    def to_representation(self, instance):
        """Mukautettu GET-vastaus"""
        representation = super().to_representation(instance)
        # Muodostetaan viittaukset käyttäjien ID:n ja nimien perusteella
        representation['references'] = [
            {
                "id": user.id,
                "username": user.username
            }
            for user in instance.references.all()
        ]
        # Muodostetaan käyttäjän tiedot
        representation['user'] = {
            "id": instance.user.id,
            "username": instance.user.username
        }
        return representation

    def create(self, validated_data):
        hashtags_data = validated_data.pop('hashtags', [])
        references_data = validated_data.pop('references', [])
        user = validated_data.pop('user', None)  # Käyttäjän määrittäminen POSTissa (voi olla myös kirjautunut käyttäjä)
        
        # Jos user ei ole mukana, käytetään kirjautunutta käyttäjää
        if not user:
            user = self.context['request'].user
        
        # Luodaan postaus
        post = Post.objects.create(user=user, **validated_data)

        # Lisää hashtagit
        for hashtag_data in hashtags_data:
            # Hae olemassa oleva hashtagi tai luo uusi
            hashtag, created = Hashtag.objects.get_or_create(name=hashtag_data['name'])
            post.hashtags.add(hashtag)

        # Lisää viittaukset
        post.references.set(references_data)
        return post

    def update(self, instance, validated_data):
        hashtags_data = validated_data.pop('hashtags', None)
        references_data = validated_data.pop('references', None)

        # Päivitä tekstikentät
        instance.text = validated_data.get('text', instance.text)
        instance.save()

        # Päivitä hashtagit
        if hashtags_data is not None:
            instance.hashtags.clear()
            for hashtag_data in hashtags_data:
                # Hae olemassa oleva hashtagi tai luo uusi
                hashtag, created = Hashtag.objects.get_or_create(name=hashtag_data['name'])
                instance.hashtags.add(hashtag)

        # Päivitä viittaukset
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
