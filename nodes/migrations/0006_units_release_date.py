# Generated by Django 3.2.8 on 2021-10-29 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0005_alter_units_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='units',
            name='release_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
