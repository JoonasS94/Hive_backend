from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Post, Hashtag, LikedUsers, FollowedHashtags, LikedPosts

# Get the custom User model
User = get_user_model()

# Customize the UserAdmin to display custom fields or configurations
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Fields to display in the user list in the admin panel
    list_display = ('id', 'email', 'username', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_active')
    ordering = ('id',)

    # Customize the fields displayed on the detail/edit page
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('bio',)}),  # Include 'bio' or other custom fields if applicable
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Define fields for the "Add User" page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

# Register the other models
admin.site.register(Post)
admin.site.register(Hashtag)
admin.site.register(LikedUsers)
admin.site.register(FollowedHashtags)
admin.site.register(LikedPosts)
