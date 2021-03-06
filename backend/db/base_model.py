from django.db import models


class BaseModel(models.Model):

    is_delete = models.BooleanField(
        default=False, verbose_name='是否删除', db_column='is_delete')
    create_time = models.DateTimeField(
        auto_now_add=True, verbose_name='创建时间', db_column='create_time')
    update_time = models.DateTimeField(
        auto_now=True, verbose_name='更新时间', db_column='update_time')

    class Meta:
        abstract = True
