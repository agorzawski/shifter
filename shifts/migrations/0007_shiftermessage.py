# Generated by Django 3.1.3 on 2021-05-31 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0006_slot_op'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShifterMessage',
            fields=[
                ('number', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.TextField()),
                ('valid', models.BooleanField(default=False)),
            ],
        ),
    ]
