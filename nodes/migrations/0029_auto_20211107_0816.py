# Generated by Django 3.2.8 on 2021-11-07 08:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0028_alter_units_mng_ip'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comments',
            name='unit',
        ),
        migrations.AddField(
            model_name='units',
            name='comment',
            field=models.OneToOneField(blank=True, default='', null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='nodes.comments'),
        ),
        migrations.AlterField(
            model_name='comments',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nodes.customers'),
        ),
    ]
