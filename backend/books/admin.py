from django.contrib import admin
from books.models import Books
from django.utils.html import format_html


class BooksAdmin(admin.ModelAdmin):
    """书籍管理界面"""

    list_display = [
        'name', 'img', 'type_id', 'stock', 'sales', 'status', 'discount'
    ]
    # list_display_links = None
    ordering = [
        'id',
    ]
    list_editable = ['type_id', 'stock', 'status', 'discount']
    readonly_fields = ['name', 'sales']
    list_filter = ['type_id', 'status']
    search_fields = ['name']
    date_hierarchy = 'create_time'

    def save_model(self, request, obj, form, change):
        if obj.discount <= 1:
            super().save_model(request, obj, form, change)


# Register your models here.
admin.site.register(Books, BooksAdmin)
admin.site.site_title = '荒岛书店后台'
admin.site.site_header = '荒岛书店管理'
admin.site.index_title = '荒岛书店后台'