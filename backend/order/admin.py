from django.contrib import admin
from .models import OrderBooks, OrderInfo


# Register your models here.
class OrderInfoAdmin(admin.ModelAdmin):
    """订单信息管理界面"""
    list_display = ('order_id', 'user_name', 'address', 'total_price',
                    'pay_method', 'status_color', 'trade_id')
    list_display_links = None
    fk_fields = ('user_name', 'address')
    list_filter = ['status', 'pay_method']
    date_hierarchy = 'create_time'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request):
        return False


# admin.site.register(OrderBooks)
admin.site.register(OrderInfo, OrderInfoAdmin)
