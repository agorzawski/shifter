# Generated by Django 3.1.3 on 2021-04-23 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0004_auto_20210223_1327'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='color_in_calendar',
            field=models.CharField(default='#0000FF', max_length=7),
        ),
    ]
