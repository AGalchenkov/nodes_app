# Generated by Django 3.2.8 on 2021-11-07 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0027_alter_comments_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='units',
            name='mng_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
