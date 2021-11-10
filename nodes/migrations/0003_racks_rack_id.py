# Generated by Django 3.2.8 on 2021-10-29 08:38

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0002_comments_pub_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='racks',
            name='rack_id',
            field=models.IntegerField(default=999, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1000)]),
        ),
    ]
