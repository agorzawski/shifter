# Generated by Django 3.2.16 on 2022-12-06 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_alter_team_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('contact_type', models.CharField(choices=[('email', 'Email'), ('phone', 'Phone Number'), ('link', 'URL')], default='phone', max_length=5)),
                ('contact', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Contact',
                'ordering': ['id'],
            },
        ),
    ]
