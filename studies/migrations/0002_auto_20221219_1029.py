# Generated by Django 3.1.3 on 2022-12-19 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studyrequest',
            name='slot_end',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='studyrequest',
            name='slot_start',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
