# Generated by Django 3.2.16 on 2023-02-01 08:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shifts', '0011_auto_20220614_1349'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
                ('contact_type', models.CharField(choices=[('email', 'Email'), ('phone', 'Phone Number'), ('link', 'URL'), ('zoom', 'Zoom Link')], default='phone', max_length=5)),
                ('contact', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=False)),
                ('fa_icon', models.CharField(default='fa-phone', max_length=50)),
            ],
            options={
                'verbose_name': 'Contact',
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='revision',
            name='merged',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='revision',
            name='name',
            field=models.CharField(default='Default', max_length=200),
        ),
        migrations.AddField(
            model_name='revision',
            name='ready_for_preview',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='slot',
            name='used_for_lookup',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='slot',
            name='abbreviation',
            field=models.CharField(default='AM', max_length=10, unique=True),
        ),
        migrations.CreateModel(
            name='Desiderata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('stop', models.DateTimeField()),
                ('all_day', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('vac', 'Vacation'), ('conf', 'Conference'), ('other', 'Other')], default='vac', max_length=10)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
