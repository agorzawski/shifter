# Generated by Django 3.1.3 on 2021-03-15 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_role_abbreviation'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='photo',
            field=models.TextField(blank=True, max_length=10000, null=True),
        ),
    ]
