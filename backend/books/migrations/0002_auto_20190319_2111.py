# Generated by Django 2.1.7 on 2019-03-19 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='books',
            name='discount',
            field=models.DecimalField(db_column='discount', decimal_places=2, default=1.0, max_digits=3, verbose_name='折扣'),
        ),
    ]
