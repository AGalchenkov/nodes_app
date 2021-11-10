# Generated by Django 3.2.8 on 2021-10-31 20:07

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0019_auto_20211029_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='customer',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='locations',
            name='rack_location',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='models',
            name='model_name',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='units',
            name='mng_ip',
            field=models.CharField(blank=True, max_length=15, unique=True),
        ),
        migrations.AlterField(
            model_name='units',
            name='sn',
            field=models.CharField(max_length=30, unique=True),
        ),
        migrations.AlterField(
            model_name='units',
            name='unit_num',
            field=models.IntegerField(unique=True, validators=[django.core.validators.MinValueValidator(0, message='negative unit number'), django.core.validators.MaxValueValidator(48, message='to much unit number')]),
        ),
    ]
