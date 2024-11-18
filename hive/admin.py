from django.contrib import admin
from .models import User, Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Hashtag)
admin.site.register(LikedUsers)
admin.site.register(FollowedHashtags)
admin.site.register(LikedPosts)
