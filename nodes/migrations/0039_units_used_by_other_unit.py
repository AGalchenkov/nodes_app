# Generated by Django 3.2.8 on 2021-11-08 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0038_units_in_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='units',
            name='used_by_other_unit',
            field=models.BooleanField(default=False),
        ),
    ]
