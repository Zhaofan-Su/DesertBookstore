# Generated by Django 2.1.7 on 2019-03-18 14:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('books', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_delete', models.BooleanField(db_column='is_delete', default=False, verbose_name='是否删除')),
                ('create_time', models.DateTimeField(auto_now_add=True, db_column='create_time', verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, db_column='update_time', verbose_name='更新时间')),
                ('disabled', models.BooleanField(default=False, verbose_name='禁用评论')),
                ('content', models.CharField(max_length=1000, verbose_name='评论内容')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.Books', verbose_name='书籍ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Passport', verbose_name='用户ID')),
            ],
            options={
                'verbose_name': '评论',
                'verbose_name_plural': '评论',
                'db_table': 'comment',
            },
        ),
    ]