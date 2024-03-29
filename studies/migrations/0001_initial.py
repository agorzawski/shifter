# Generated by Django 3.2.16 on 2022-11-29 13:30

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Title', max_length=200, null=True)),
                ('description', models.TextField(blank=True, help_text='Study Description', max_length=2000, null=True)),
                ('beam_current', models.FloatField(blank=True, default=6.0, help_text='Max. Beam Current (mA)', null=True)),
                ('beam_pulse_length', models.FloatField(blank=True, default=5.0, help_text='Max. Beam Pulse Length (us)', null=True)),
                ('beam_destination', models.CharField(blank=True, choices=[('LEBT', 'LEBT FC'), ('MEBT', 'MEBT FC'), ('DTL2', 'DTL2 FC'), ('DTL4', 'DTL4 FC'), ('OTHER', 'OTHER')], default='LEBT', help_text='Beam Destination', max_length=200, null=True)),
                ('beam_reprate', models.IntegerField(blank=True, choices=[(1, '1 Hz'), (2, '2 Hz'), (3, '3.5 Hz'), (4, '7 Hz'), (5, '14 Hz'), (6, 'Uneven rate')], default=1, help_text='Max. beam repetition rate (Hz)', null=True)),
                ('jira', models.URLField(blank=True, help_text='Add a JIRA link if possible', null=True)),
                ('duration', models.IntegerField(blank=True, choices=[(1, '30 min'), (2, '60 min'), (3, '1.5 hour'), (4, '2.0 hours'), (5, '2.5 hours'), (6, '3 hours'), (7, 'more than 3 hours')], default=1, help_text='Study duration (30 min steps)', null=True)),
                ('slot_start', models.DateTimeField(default=datetime.datetime(2022, 11, 29, 14, 30, 59, 553202))),
                ('slot_end', models.DateTimeField(default=datetime.datetime(2022, 11, 29, 14, 30, 59, 553216))),
                ('priority', models.BooleanField(default=False)),
                ('state', models.CharField(choices=[('R', 'Requested'), ('B', 'Booked'), ('C', 'Canceled'), ('D', 'Done')], default='R', max_length=1)),
                ('booking_created', models.DateTimeField()),
                ('booking_finished', models.DateTimeField(blank=True, null=True)),
                ('after_comment', models.TextField(blank=True, default=None, max_length=2000, null=True)),
                ('booked_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='study_booking_member', to=settings.AUTH_USER_MODEL)),
                ('finished_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='study_closing_member', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(help_text='study leader', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='study_using_member', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
