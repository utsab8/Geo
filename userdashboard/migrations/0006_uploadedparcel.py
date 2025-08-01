# Generated by Django 5.2.4 on 2025-07-26 13:16

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userdashboard', '0005_contactformsubmission'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedParcel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, verbose_name='Parcel Name')),
                ('kitta_no', models.CharField(blank=True, max_length=100, verbose_name='Kitta Number')),
                ('sn_no', models.CharField(blank=True, max_length=100, verbose_name='SN Number')),
                ('district', models.CharField(blank=True, max_length=255, verbose_name='District')),
                ('municipality', models.CharField(blank=True, max_length=255, verbose_name='Municipality')),
                ('ward', models.CharField(blank=True, max_length=100, verbose_name='Ward')),
                ('location', models.CharField(blank=True, max_length=255, verbose_name='Location')),
                ('geometry', models.JSONField(blank=True, null=True, verbose_name='Geometry (GeoJSON)')),
                ('coordinates', models.TextField(blank=True, null=True, verbose_name='Coordinates')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Uploaded At')),
                ('file_type', models.CharField(choices=[('KML', 'KML File'), ('CSV', 'CSV File'), ('SHP', 'Shapefile')], max_length=20, verbose_name='File Type')),
                ('original_file', models.FileField(blank=True, null=True, upload_to='parcels/', verbose_name='Original File')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_parcels', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Uploaded Parcel',
                'verbose_name_plural': 'Uploaded Parcels',
                'ordering': ['-uploaded_at'],
                'indexes': [models.Index(fields=['user', 'uploaded_at'], name='userdashboa_user_id_2ab58f_idx'), models.Index(fields=['district', 'municipality'], name='userdashboa_distric_f4988d_idx'), models.Index(fields=['kitta_no'], name='userdashboa_kitta_n_d1b53e_idx')],
            },
        ),
    ]
