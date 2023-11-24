# Generated by Django 3.2.16 on 2023-08-30 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0012_auto_20230201_0923'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Leave or early cancellation, not counted for the HR.'),
        ),
        migrations.AddField(
            model_name='shift',
            name='is_cancelled',
            field=models.BooleanField(default=False, help_text='Last minute cancellation? Will be counted for the HR.'),
        ),
        migrations.AddField(
            model_name='shift',
            name='post_comment',
            field=models.TextField(blank=True, help_text='Summary/comment for the end/post shift time. [Shifters view ONLY]', null=True),
        ),
        migrations.AddField(
            model_name='shift',
            name='pre_comment',
            field=models.TextField(blank=True, help_text='Text to be displayed in shifters as shift constraint. [Shifters view ONLY] ', null=True),
        ),
    ]