from django.contrib import admin
from users.models import Passport, Address


# Register your models here.
class PassportAdmin(admin.ModelAdmin):
    """用户信息管理界面"""
    list_display = ('username', 'email', 'create_time', 'delete_or_not')
    list_filter = ['is_delete']
    list_display_links = None
    date_hierarchy = 'create_time'
    readonly_fields = ['username', 'email']


class AddressAdmin(admin.ModelAdmin):
    """用户地址管理界面"""
    list_display = ('user_name', 'recipient_name', 'recipient_phone',
                    'recipient_addr', 'zip_code', 'is_default')
    list_display_links = None
    fk_fields = ('user_name', )
    search_fields = ['passport__username']
    date_hierarchy = 'create_time'
    readonly_fields = list_display

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request):
        return False


admin.site.register(Passport, PassportAdmin)
admin.site.register(Address, AddressAdmin)
