# Generated by Django 3.1.3 on 2021-11-18 08:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0008_auto_20211107_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='shiftID',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='shifts.shiftid'),
        ),
    ]
