from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    AdminActivity, SystemMetrics, UserAnalytics, SystemNotification,
    AdminSettings, BackupLog, MaintenanceWindow, UserSession, DashboardWidget,
    UserPageView, UserAction, UserEngagement, RealTimeUserActivity, UserError, UserPerformance
)
from userdashboard.models import FileUpload, KMLData, UploadedParcel
from account.models import User
from django.utils import timezone

User = get_user_model()

# Enhanced User Activity Tracking Serializers
class UserPageViewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserPageView
        fields = [
            'id', 'user', 'user_email', 'page_url', 'page_name', 'session_key',
            'ip_address', 'user_agent', 'referrer', 'time_spent', 'created_at'
        ]

class UserActionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserAction
        fields = [
            'id', 'user', 'user_email', 'action_type', 'action_data',
            'ip_address', 'user_agent', 'session_key', 'created_at'
        ]

class UserEngagementSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserEngagement
        fields = [
            'id', 'user', 'user_email', 'date', 'total_time_spent', 'pages_visited',
            'actions_performed', 'files_uploaded', 'files_downloaded',
            'searches_performed', 'exports_created', 'last_activity'
        ]

class RealTimeUserActivitySerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = RealTimeUserActivity
        fields = [
            'id', 'user', 'user_email', 'current_page', 'current_action',
            'session_key', 'ip_address', 'is_active', 'last_activity', 'created_at'
        ]

class UserErrorSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserError
        fields = [
            'id', 'user', 'user_email', 'error_type', 'error_message',
            'error_details', 'page_url', 'ip_address', 'user_agent', 'created_at'
        ]

class UserPerformanceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserPerformance
        fields = [
            'id', 'user', 'user_email', 'date', 'avg_session_duration',
            'avg_pages_per_session', 'avg_actions_per_session',
            'file_upload_success_rate', 'file_processing_success_rate',
            'export_success_rate', 'error_rate'
        ]

# Existing Serializers
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()
    last_login_formatted = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone_number',
            'avatar', 'avatar_url', 'linkedin', 'github', 'is_staff',
            'is_active', 'date_joined', 'last_login', 'last_login_formatted',
            'is_online'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None
    
    def get_last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M:%S')
        return 'Never'
    
    def get_is_online(self, obj):
        # Check if user has active session
        return UserSession.objects.filter(user=obj, is_active=True).exists()

class AdminActivitySerializer(serializers.ModelSerializer):
    """Serializer for AdminActivity model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    admin_user_email = serializers.CharField(source='admin_user.email', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminActivity
        fields = [
            'id', 'activity_type', 'activity_type_display', 'description',
            'user', 'user_email', 'admin_user', 'admin_user_email',
            'ip_address', 'user_agent', 'metadata', 'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

class SystemMetricsSerializer(serializers.ModelSerializer):
    """Serializer for SystemMetrics model"""
    timestamp_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'timestamp', 'timestamp_formatted', 'cpu_usage',
            'memory_usage', 'disk_usage', 'active_users', 'total_requests',
            'error_rate', 'response_time'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_timestamp_formatted(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')

class UserAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for UserAnalytics model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    date_formatted = serializers.SerializerMethodField()
    last_activity_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAnalytics
        fields = [
            'id', 'user', 'user_email', 'user_full_name', 'date', 'date_formatted',
            'login_count', 'file_uploads', 'file_downloads', 'session_duration',
            'pages_visited', 'last_activity', 'last_activity_formatted'
        ]
        read_only_fields = ['id', 'last_activity']
    
    def get_date_formatted(self, obj):
        return obj.date.strftime('%Y-%m-%d')
    
    def get_last_activity_formatted(self, obj):
        return obj.last_activity.strftime('%Y-%m-%d %H:%M:%S')

class SystemNotificationSerializer(serializers.ModelSerializer):
    """Serializer for SystemNotification model"""
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'is_read', 'is_active', 'created_at',
            'created_at_formatted', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

class AdminSettingsSerializer(serializers.ModelSerializer):
    """Serializer for AdminSettings model"""
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminSettings
        fields = [
            'id', 'key', 'value', 'description', 'is_public',
            'updated_at', 'updated_at_formatted'
        ]
        read_only_fields = ['id', 'updated_at']
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')

class BackupLogSerializer(serializers.ModelSerializer):
    """Serializer for BackupLog model"""
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)
    started_at_formatted = serializers.SerializerMethodField()
    completed_at_formatted = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupLog
        fields = [
            'id', 'backup_type', 'backup_type_display', 'status', 'status_display',
            'file_path', 'file_size', 'file_size_formatted', 'started_at',
            'started_at_formatted', 'completed_at', 'completed_at_formatted',
            'error_message', 'initiated_by', 'initiated_by_email'
        ]
        read_only_fields = ['id', 'started_at']
    
    def get_started_at_formatted(self, obj):
        return obj.started_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_completed_at_formatted(self, obj):
        if obj.completed_at:
            return obj.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_file_size_formatted(self, obj):
        if obj.file_size == 0:
            return '0 B'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size < 1024.0:
                return f"{obj.file_size:.1f} {unit}"
            obj.file_size /= 1024.0
        return f"{obj.file_size:.1f} TB"

class MaintenanceWindowSerializer(serializers.ModelSerializer):
    """Serializer for MaintenanceWindow model"""
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    start_time_formatted = serializers.SerializerMethodField()
    end_time_formatted = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceWindow
        fields = [
            'id', 'title', 'description', 'start_time', 'start_time_formatted',
            'end_time', 'end_time_formatted', 'is_active', 'created_at',
            'created_at_formatted', 'created_by', 'created_by_email'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_start_time_formatted(self, obj):
        return obj.start_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_end_time_formatted(self, obj):
        return obj.end_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    login_time_formatted = serializers.SerializerMethodField()
    logout_time_formatted = serializers.SerializerMethodField()
    session_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'user_email', 'user_full_name', 'session_key',
            'ip_address', 'user_agent', 'login_time', 'login_time_formatted',
            'logout_time', 'logout_time_formatted', 'is_active', 'session_duration'
        ]
        read_only_fields = ['id', 'login_time']
    
    def get_login_time_formatted(self, obj):
        return obj.login_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_logout_time_formatted(self, obj):
        if obj.logout_time:
            return obj.logout_time.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_session_duration(self, obj):
        if obj.logout_time:
            duration = obj.logout_time - obj.login_time
            return int(duration.total_seconds() / 60)  # Return minutes
        elif obj.is_active:
            duration = timezone.now() - obj.login_time
            return int(duration.total_seconds() / 60)  # Return minutes
        return 0

class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializer for DashboardWidget model"""
    widget_type_display = serializers.CharField(source='get_widget_type_display', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'name', 'widget_type', 'widget_type_display', 'configuration',
            'position', 'is_enabled', 'created_at', 'created_at_formatted',
            'updated_at', 'updated_at_formatted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')

# Dashboard Statistics Serializer
class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_24h = serializers.IntegerField()
    new_users_7d = serializers.IntegerField()
    total_files = serializers.IntegerField()
    total_surveys = serializers.IntegerField()
    total_parcels = serializers.IntegerField()
    total_page_views = serializers.IntegerField()
    total_user_actions = serializers.IntegerField()
    total_errors = serializers.IntegerField()
    avg_session_duration = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    recent_activities_count = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()

# User Management Serializer
class UserManagementSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['activate', 'deactivate', 'delete', 'change_role'])
    user_ids = serializers.ListField(child=serializers.IntegerField())
    new_role = serializers.ChoiceField(choices=['staff', 'regular'], required=False)

# System Backup Serializer
class SystemBackupSerializer(serializers.Serializer):
    backup_type = serializers.ChoiceField(choices=['database', 'files', 'full'])

# Notification Create Serializer
class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemNotification
        fields = ['title', 'message', 'notification_type', 'priority', 'expires_at'] 