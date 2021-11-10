# Generated by Django 3.2.8 on 2021-11-07 18:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0035_alter_comments_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='units',
            name='unit_num',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='negative unit number'), django.core.validators.MaxValueValidator(48, message='to much unit number')]),
        ),
        migrations.AlterUniqueTogether(
            name='units',
            unique_together={('rack_id', 'unit_num')},
        ),
    ]
