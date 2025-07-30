from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

User = get_user_model()

class AdminActivity(models.Model):
    """Track admin activities and system events"""
    ACTIVITY_TYPES = [
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_deleted', 'User Deleted'),
        ('file_uploaded', 'File Uploaded'),
        ('file_deleted', 'File Deleted'),
        ('system_backup', 'System Backup'),
        ('system_maintenance', 'System Maintenance'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('error', 'System Error'),
    ]
    
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities', null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Admin Activities'
    
    def __str__(self):
        return f"{self.activity_type} - {self.description[:50]}"

class SystemMetrics(models.Model):
    """System performance and usage metrics"""
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    disk_usage = models.FloatField(default=0.0)
    active_users = models.IntegerField(default=0)
    total_requests = models.IntegerField(default=0)
    error_rate = models.FloatField(default=0.0)
    response_time = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'System Metrics'
    
    def __str__(self):
        return f"System Metrics - {self.timestamp}"

class UserAnalytics(models.Model):
    """User behavior and analytics data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    login_count = models.IntegerField(default=0)
    file_uploads = models.IntegerField(default=0)
    file_downloads = models.IntegerField(default=0)
    session_duration = models.IntegerField(default=0)  # in minutes
    pages_visited = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name_plural = 'User Analytics'
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"

class SystemNotification(models.Model):
    """System notifications and alerts"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    is_read = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'System Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.notification_type}"

class AdminSettings(models.Model):
    """Admin dashboard settings and configuration"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Admin Settings'
    
    def __str__(self):
        return f"{self.key}: {self.value}"

class BackupLog(models.Model):
    """System backup logs"""
    BACKUP_TYPES = [
        ('database', 'Database'),
        ('files', 'Files'),
        ('full', 'Full System'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name_plural = 'Backup Logs'
    
    def __str__(self):
        return f"{self.backup_type} backup - {self.status}"

class MaintenanceWindow(models.Model):
    """Scheduled maintenance windows"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name_plural = 'Maintenance Windows'
    
    def __str__(self):
        return f"{self.title} - {self.start_time}"

class UserSession(models.Model):
    """Track user sessions for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-login_time']
        verbose_name_plural = 'User Sessions'
    
    def __str__(self):
        return f"{self.user.email} - {self.login_time}"

class DashboardWidget(models.Model):
    """Customizable dashboard widgets for admins"""
    WIDGET_TYPES = [
        ('stats', 'Statistics'),
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('activity', 'Activity Feed'),
    ]
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    configuration = models.JSONField(default=dict)
    position = models.IntegerField(default=0)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
        verbose_name_plural = 'Dashboard Widgets'
    
    def __str__(self):
        return f"{self.name} ({self.widget_type})"

# Enhanced User Activity Tracking Models
class UserPageView(models.Model):
    """Track every page view by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='page_views')
    page_url = models.CharField(max_length=500)
    page_name = models.CharField(max_length=100)
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.CharField(max_length=500, blank=True)
    time_spent = models.IntegerField(default=0)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User Page Views'
    
    def __str__(self):
        return f"{self.user.email} - {self.page_name}"

class UserAction(models.Model):
    """Track specific user actions"""
    ACTION_TYPES = [
        ('file_upload', 'File Upload'),
        ('file_download', 'File Download'),
        ('file_delete', 'File Delete'),
        ('file_share', 'File Share'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('search', 'Search'),
        ('export', 'Export'),
        ('preview', 'Preview'),
        ('contact_form', 'Contact Form'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    action_data = models.JSONField(default=dict)  # Store action-specific data
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User Actions'
    
    def __str__(self):
        return f"{self.user.email} - {self.action_type}"

class UserEngagement(models.Model):
    """Track user engagement metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement')
    date = models.DateField(auto_now_add=True)
    total_time_spent = models.IntegerField(default=0)  # minutes
    pages_visited = models.IntegerField(default=0)
    actions_performed = models.IntegerField(default=0)
    files_uploaded = models.IntegerField(default=0)
    files_downloaded = models.IntegerField(default=0)
    searches_performed = models.IntegerField(default=0)
    exports_created = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name_plural = 'User Engagement'
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"

class RealTimeUserActivity(models.Model):
    """Real-time user activity tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='real_time_activity')
    current_page = models.CharField(max_length=500)
    current_action = models.CharField(max_length=100, blank=True)
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name_plural = 'Real-time User Activity'
    
    def __str__(self):
        return f"{self.user.email} - {self.current_page}"

class UserError(models.Model):
    """Track user-facing errors"""
    ERROR_TYPES = [
        ('file_upload_error', 'File Upload Error'),
        ('processing_error', 'Processing Error'),
        ('validation_error', 'Validation Error'),
        ('export_error', 'Export Error'),
        ('authentication_error', 'Authentication Error'),
        ('permission_error', 'Permission Error'),
        ('system_error', 'System Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='errors', null=True, blank=True)
    error_type = models.CharField(max_length=50, choices=ERROR_TYPES)
    error_message = models.TextField()
    error_details = models.JSONField(default=dict)
    page_url = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User Errors'
    
    def __str__(self):
        return f"{self.error_type} - {self.created_at}"

class UserPerformance(models.Model):
    """Track user performance metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance')
    date = models.DateField(auto_now_add=True)
    avg_session_duration = models.FloatField(default=0.0)  # minutes
    avg_pages_per_session = models.FloatField(default=0.0)
    avg_actions_per_session = models.FloatField(default=0.0)
    file_upload_success_rate = models.FloatField(default=0.0)  # percentage
    file_processing_success_rate = models.FloatField(default=0.0)
    export_success_rate = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name_plural = 'User Performance'
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"
