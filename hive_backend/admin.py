from django.contrib import admin
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


admin.site.register(Post)
admin.site.register(Hashtag)
admin.site.register(LikedUsers)
admin.site.register(FollowedHashtags)
admin.site.register(LikedPosts)
