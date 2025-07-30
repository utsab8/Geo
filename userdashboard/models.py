from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os
import json
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField

User = get_user_model()

class FileUpload(models.Model):
    """Enhanced model for all file uploads with conversion tracking"""
    FILE_TYPES = [
        ('kml', 'KML File'),
        ('csv', 'CSV File'),
        ('shapefile', 'Shapefile'),
        ('geojson', 'GeoJSON'),
        ('excel', 'Excel File'),
        ('pdf', 'PDF Document'),
        ('image', 'Image File'),
        ('other', 'Other File'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('validated', 'Validated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='file_uploads')
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    validation_errors = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Enhanced metadata fields
    geometry_type = models.CharField(max_length=50, blank=True, null=True)
    coordinate_system = models.CharField(max_length=50, blank=True, null=True)
    feature_count = models.PositiveIntegerField(default=0)
    bounds = models.JSONField(default=dict, blank=True)  # minx, miny, maxx, maxy
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['file_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.file_type}) - {getattr(self.user, 'email', self.user)}"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def file_size_kb(self):
        return round(self.file_size / 1024, 2)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.original_filename)[1].lower()
    
    @property
    def is_image(self):
        return self.file_type == 'image'
    
    @property
    def is_geospatial(self):
        return self.file_type in ['kml', 'csv', 'shapefile', 'geojson']
    
    def get_absolute_url(self):
        return f'/dashboard/uploads/{self.id}/'
    
    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

class FileProcessingLog(models.Model):
    """Model to track file processing history"""
    PROCESSING_TYPES = [
        ('validation', 'File Validation'),
        ('parsing', 'File Parsing'),
        ('conversion', 'File Conversion'),
        ('analysis', 'Data Analysis'),
        ('export', 'File Export'),
    ]
    
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='processing_logs')
    processing_type = models.CharField(max_length=20, choices=PROCESSING_TYPES)
    status = models.CharField(max_length=20, choices=FileUpload.STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.file_upload.original_filename} - {self.processing_type} - {self.status}"

class FileValidationRule(models.Model):
    """Model to define validation rules for different file types"""
    file_type = models.CharField(max_length=20, choices=FileUpload.FILE_TYPES)
    rule_name = models.CharField(max_length=100)
    rule_description = models.TextField()
    max_file_size_mb = models.PositiveIntegerField(default=10)
    allowed_extensions = models.JSONField(default=list)
    required_fields = models.JSONField(default=list, blank=True)
    validation_regex = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['file_type', 'rule_name']
        ordering = ['file_type', 'rule_name']
    
    def __str__(self):
        return f"{self.file_type} - {self.rule_name}"

class FileShare(models.Model):
    """Model for file sharing functionality"""
    SHARE_TYPES = [
        ('public', 'Public Link'),
        ('private', 'Private Link'),
        ('email', 'Email Share'),
        ('expiring', 'Expiring Link'),
    ]
    
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='shares')
    share_type = models.CharField(max_length=20, choices=SHARE_TYPES)
    share_token = models.UUIDField(default=uuid.uuid4, editable=False)
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_files')
    shared_with_email = models.EmailField(blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    download_limit = models.PositiveIntegerField(null=True, blank=True)
    current_downloads = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.file_upload.original_filename} - {self.share_type} - {self.shared_by}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_download_limit_reached(self):
        if self.download_limit:
            return self.current_downloads >= self.download_limit
        return False
    
    def can_be_downloaded(self):
        return self.is_active and not self.is_expired and not self.is_download_limit_reached

class FileConversion(models.Model):
    """Model to track file conversions"""
    CONVERSION_TYPES = [
        ('kml_to_csv', 'KML to CSV'),
        ('kml_to_shapefile', 'KML to Shapefile'),
        ('csv_to_kml', 'CSV to KML'),
        ('csv_to_shapefile', 'CSV to Shapefile'),
        ('shapefile_to_kml', 'Shapefile to KML'),
        ('shapefile_to_csv', 'Shapefile to CSV'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='conversions')
    conversion_type = models.CharField(max_length=30, choices=CONVERSION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    output_file = models.FileField(upload_to='exports/', blank=True, null=True)
    output_filename = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    processing_started = models.DateTimeField(auto_now_add=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-processing_started']
        indexes = [
            models.Index(fields=['source_file', 'conversion_type']),
            models.Index(fields=['status', 'processing_started']),
        ]
    
    def __str__(self):
        return f"{self.source_file.original_filename} → {self.get_conversion_type_display()}"

class CSVData(models.Model):
    """Model to store parsed CSV data"""
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='csv_data')
    row_number = models.PositiveIntegerField()
    data = models.JSONField()  # Store all row data as JSON
    geometry_type = models.CharField(max_length=50, blank=True, null=True)
    coordinates = models.TextField(blank=True, null=True)  # JSON string of coordinates
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['row_number']
        indexes = [
            models.Index(fields=['file_upload', 'row_number']),
        ]
    
    def __str__(self):
        return f"Row {self.row_number} - {self.file_upload.original_filename}"

class ShapefileData(models.Model):
    """Model to store parsed Shapefile data"""
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='shapefile_data')
    feature_id = models.PositiveIntegerField()
    geometry_type = models.CharField(max_length=50)
    coordinates = models.TextField()  # JSON string of coordinates
    attributes = models.JSONField(default=dict)  # All attribute fields
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['feature_id']
        indexes = [
            models.Index(fields=['file_upload', 'feature_id']),
        ]
    
    def __str__(self):
        return f"Feature {self.feature_id} - {self.file_upload.original_filename}"

# Keep existing KML models for backward compatibility
class KMLFile(models.Model):
    """Model to store uploaded KML files"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kml_files')
    file = models.FileField(upload_to='kml/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=50, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_filename} - {getattr(self.user, 'email', self.user)}"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

class KMLData(models.Model):
    """Enhanced model to store comprehensive parsed KML data"""
    kml_file = models.ForeignKey(KMLFile, on_delete=models.CASCADE, related_name='parsed_data')
    
    # Basic fields (shown in preview)
    kitta_number = models.CharField(max_length=100, blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    geometry_type = models.CharField(max_length=50)  # Point, Polygon, etc.
    coordinates = models.TextField()  # JSON string of coordinates
    area_hectares = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    area_sqm = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    placemark_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Extended data (hidden in preview, included in CSV export)
    extended_data = models.JSONField(default=dict, blank=True)  # All ExtendedData as JSON
    time_begin = models.CharField(max_length=100, blank=True, null=True)
    time_end = models.CharField(max_length=100, blank=True, null=True)
    time_when = models.CharField(max_length=100, blank=True, null=True)
    altitude = models.CharField(max_length=50, blank=True, null=True)
    altitude_mode = models.CharField(max_length=50, blank=True, null=True)
    tessellate = models.CharField(max_length=10, blank=True, null=True)
    extrude = models.CharField(max_length=10, blank=True, null=True)
    style_id = models.CharField(max_length=100, blank=True, null=True)
    style_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Address information
    address = models.TextField(blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    administrative_area = models.CharField(max_length=255, blank=True, null=True)
    sub_administrative_area = models.CharField(max_length=255, blank=True, null=True)
    locality = models.CharField(max_length=255, blank=True, null=True)
    sub_locality = models.CharField(max_length=255, blank=True, null=True)
    thoroughfare = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Contact information
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Additional KML elements
    snippet = models.TextField(blank=True, null=True)
    visibility = models.CharField(max_length=10, blank=True, null=True)
    open_status = models.CharField(max_length=10, blank=True, null=True)  # 'open' field
    atom_author = models.CharField(max_length=255, blank=True, null=True)
    atom_link = models.URLField(max_length=500, blank=True, null=True)
    xal_address_details = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['kml_file', 'geometry_type']),
            models.Index(fields=['kitta_number']),
            models.Index(fields=['owner_name']),
        ]
    
    def __str__(self):
        return f"{self.placemark_name or 'Unnamed'} - {self.geometry_type} ({self.kml_file.original_filename})"
    
    @property
    def has_extended_data(self):
        """Check if this placemark has any extended data"""
        return bool(self.extended_data)
    
    @property
    def has_time_data(self):
        """Check if this placemark has time information"""
        return any([self.time_begin, self.time_end, self.time_when])
    
    @property
    def has_address_data(self):
        """Check if this placemark has address information"""
        return any([self.address, self.locality, self.administrative_area])
    
    @property
    def has_contact_data(self):
        """Check if this placemark has contact information"""
        return bool(self.phone_number)
    
    def get_all_fields_for_csv(self):
        """Get all fields as a dictionary for CSV export"""
        return {
            'Placemark Name': self.placemark_name or '',
            'Kitta Number': self.kitta_number or '',
            'Owner Name': self.owner_name or '',
            'Geometry Type': self.geometry_type,
            'Coordinates': self.coordinates,
            'Area (Hectares)': float(self.area_hectares) if self.area_hectares else '',
            'Area (Square Meters)': float(self.area_sqm) if self.area_sqm else '',
            'Description': self.description or '',
            'Snippet': self.snippet or '',
            'Visibility': self.visibility or '',
            'Open': self.open_status or '',
            'Time Begin': self.time_begin or '',
            'Time End': self.time_end or '',
            'Time When': self.time_when or '',
            'Altitude': self.altitude or '',
            'Altitude Mode': self.altitude_mode or '',
            'Tessellate': self.tessellate or '',
            'Extrude': self.extrude or '',
            'Style ID': self.style_id or '',
            'Style URL': self.style_url or '',
            'Address': self.address or '',
            'Country Code': self.country_code or '',
            'Administrative Area': self.administrative_area or '',
            'Sub Administrative Area': self.sub_administrative_area or '',
            'Locality': self.locality or '',
            'Sub Locality': self.sub_locality or '',
            'Thoroughfare': self.thoroughfare or '',
            'Postal Code': self.postal_code or '',
            'Phone Number': self.phone_number or '',
            'Atom Author': self.atom_author or '',
            'Atom Link': self.atom_link or '',
            'XAL Address Details': self.xal_address_details or '',
            'Extended Data': json.dumps(self.extended_data) if self.extended_data else '',
        }

class DownloadLog(models.Model):
    """Model to track download history"""
    DOWNLOAD_TYPES = [
        ('csv', 'CSV Export'),
        ('shapefile', 'Shapefile Export'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='download_logs')
    kml_file = models.ForeignKey(KMLFile, on_delete=models.CASCADE, related_name='downloads')
    download_type = models.CharField(max_length=20, choices=DOWNLOAD_TYPES)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    downloaded_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"{self.download_type} - {self.kml_file.original_filename} - {self.downloaded_at}"

class ContactFormSubmission(models.Model):
    """Model to store contact form submissions"""
    SUBJECT_CHOICES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('support', 'Technical Support'),
        ('feedback', 'General Feedback'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_submissions')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Form Submission'
        verbose_name_plural = 'Contact Form Submissions'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.submitted_at.strftime('%Y-%m-%d %H:%M')})"

class UploadedParcel(models.Model):
    """Model for storing uploaded geospatial parcel data with JSON geometry"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_parcels')
    name = models.CharField(max_length=255, blank=True, verbose_name="Parcel Name")
    kitta_no = models.CharField(max_length=100, blank=True, verbose_name="Kitta Number")
    sn_no = models.CharField(max_length=100, blank=True, verbose_name="SN Number")
    district = models.CharField(max_length=255, blank=True, verbose_name="District")
    municipality = models.CharField(max_length=255, blank=True, verbose_name="Municipality")
    ward = models.CharField(max_length=100, blank=True, verbose_name="Ward")
    location = models.CharField(max_length=255, blank=True, verbose_name="Location")
    geometry = models.JSONField(blank=True, null=True, verbose_name="Geometry (GeoJSON)")
    coordinates = models.TextField(blank=True, null=True, verbose_name="Coordinates")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploaded At")
    file_type = models.CharField(max_length=20, choices=[
        ('KML', 'KML File'),
        ('CSV', 'CSV File'),
        ('SHP', 'Shapefile'),
    ], verbose_name="File Type")
    original_file = models.FileField(upload_to='parcels/', blank=True, null=True, verbose_name="Original File")
    
    class Meta:
        verbose_name = "Uploaded Parcel"
        verbose_name_plural = "Uploaded Parcels"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'uploaded_at']),
            models.Index(fields=['district', 'municipality']),
            models.Index(fields=['kitta_no']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.kitta_no} ({self.district})"
    
    def get_geojson(self):
        """Return GeoJSON representation of the parcel"""
        if self.geometry:
            return {
                'type': 'Feature',
                'geometry': self.geometry,
                'properties': {
                    'id': str(self.id),
                    'name': self.name,
                    'kitta_no': self.kitta_no,
                    'sn_no': self.sn_no,
                    'district': self.district,
                    'municipality': self.municipality,
                    'ward': self.ward,
                    'location': self.location,
                    'file_type': self.file_type,
                    'uploaded_at': self.uploaded_at.isoformat(),
                }
            }
        return None

class SurveyHistoryLog(models.Model):
    ACTION_CHOICES = [
        ('upload', 'File Upload'),
        ('filter', 'Filter Applied'),
        ('export', 'PDF Export'),
        ('download', 'File Download'),
        ('delete', 'File Deleted'),
    ]
    
    action_type = models.CharField(choices=ACTION_CHOICES, max_length=10)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(max_length=10, null=True, blank=True)
    filters_applied = models.JSONField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    record_count = models.IntegerField(default=0)
    map_coordinates_count = models.IntegerField(default=0)
    export_file_path = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Survey History Log'
        verbose_name_plural = 'Survey History Logs'
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.file_name or 'N/A'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_filter_summary(self):
        """Get a human-readable summary of applied filters"""
        if not self.filters_applied:
            return "No filters applied"
        
        summary_parts = []
        filters = self.filters_applied
        
        if filters.get('kitta_filter'):
            summary_parts.append(f"Kitta: {filters['kitta_filter']}")
        if filters.get('owner_filter'):
            summary_parts.append(f"Owner: {filters['owner_filter']}")
        if filters.get('location_filter'):
            summary_parts.append(f"Location: {filters['location_filter']}")
        if filters.get('area_min') or filters.get('area_max'):
            area_range = []
            if filters.get('area_min'):
                area_range.append(f"≥{filters['area_min']} ha")
            if filters.get('area_max'):
                area_range.append(f"≤{filters['area_max']} ha")
            summary_parts.append(f"Area: {' - '.join(area_range)}")
        if filters.get('geometry_filter'):
            summary_parts.append(f"Type: {filters['geometry_filter']}")
        
        return " | ".join(summary_parts) if summary_parts else "No specific filters"
    
    def get_short_description(self):
        """Get a short description for display"""
        if self.description:
            return self.description[:100] + "..." if len(self.description) > 100 else self.description
        return self.get_filter_summary()
