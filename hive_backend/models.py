from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
import json  # Lisää tämä, jos käytät json-kirjastoa follow_user-funktiossa

# CustomUser: Lisäämällä profiilikuva ja bio-kenttä peritylle AbstractUser-mallille
class CustomUser(AbstractUser):
    # Custom fields for user profile
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.username

# Retrieve the custom user model after it's defined
CustomUser = get_user_model()

# Hashtag: Malli, joka tallentaa tunnisteet, joita voi käyttää postauksissa
class Hashtag(models.Model):
    name = models.CharField(max_length=20, unique=False)

    def __str__(self):
        return self.name

# Post: Malli postauksille, joissa on teksti, aika, käyttäjä ja hashtagit
class Post(models.Model):
    text = models.CharField(max_length=144)
    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
    hashtags = models.ManyToManyField(Hashtag, related_name="posts")
    references = models.ManyToManyField(CustomUser, related_name="referenced_posts", blank=True)

    def __str__(self):
        return f"{self.text[:20]}... by {self.user.username}"

# LikedUsers: Malli, joka tallentaa, kuka tykkää kenestäkin
class LikedUsers(models.Model):
    liker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="liked_users")
    liked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="users_liked_by")

    class Meta:
        unique_together = ("liker", "liked_user")

    def __str__(self):
        return f"{self.liker.username} likes {self.liked_user.username}"

# FollowedHashtags: Malli, joka tallentaa, mitä hashtageja käyttäjä seuraa
class FollowedHashtags(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="followed_hashtags")
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name="followers")

    class Meta:
        unique_together = ("user", "hashtag")

    def __str__(self):
        return f"{self.user.username} follows #{self.hashtag.name}"

# LikedPosts: Malli, joka tallentaa, kuka on tykännyt mistäkin postauksesta
class LikedPosts(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="liked_posts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="liked_by")

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"

# FollowedUsers: Malli, joka tallentaa, kuka seuraa ketäkin
class FollowedUsers(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="following")
    followed_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="followers")

    class Meta:
        unique_together = ("follower", "followed_user")

    def __str__(self):
        return f"{self.follower.username} follows {self.followed_user.username}"

# `follow_user` -funktio, joka käsittelee käyttäjän seuraamisen
def follow_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        follower_username = data.get('follower')
        followed_username = data.get('followed_user')

        try:
            follower = CustomUser.objects.get(username=follower_username)
            followed_user = CustomUser.objects.get(username=followed_username)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "One or both users not found."}, status=404)

        if follower == followed_user:
            return JsonResponse({"error": "You cannot follow yourself."}, status=400)

        follow_instance = FollowedUsers(follower=follower, followed_user=followed_user)
        try:
            follow_instance.save()
        except IntegrityError:
            return JsonResponse({"error": "This follow relationship already exists."}, status=400)

        return JsonResponse({"message": "User followed successfully!"}, status=200)

# Comment: Malli postauksille lisätyille kommenteille
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on post {self.post.id}"

# delete_liked_user: Funktio tykkäyksen poistamiseen käyttäjäparin perusteella
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
