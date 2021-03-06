from django.contrib import admin
from .models import Comment


class CommentAdmin(admin.ModelAdmin):
    """评论管理界面"""
    list_display = ('book_name', 'content', 'user_name', 'disabled')
    list_display_links = None
    readonly_fields = ['book', 'content', 'user']
    list_editable = ['disabled']
    list_filter = ['disabled']
    search_fields = ['content']
    date_hierarchy = 'create_time'

    def has_add_permission(self, request):
        return False


# Register your models here.
admin.site.register(Comment, CommentAdmin)
