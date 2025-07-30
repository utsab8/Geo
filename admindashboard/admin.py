from django.contrib import admin
from .models import (
    AdminActivity, SystemMetrics, UserAnalytics, SystemNotification,
    AdminSettings, BackupLog, MaintenanceWindow, UserSession, DashboardWidget,
    UserPageView, UserAction, UserEngagement, RealTimeUserActivity, UserError, UserPerformance
)

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'description', 'user', 'admin_user', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['description', 'user__email', 'admin_user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'cpu_usage', 'memory_usage', 'disk_usage', 'active_users']
    list_filter = ['timestamp']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'login_count', 'file_uploads', 'session_duration', 'last_activity']
    list_filter = ['date', 'last_activity']
    search_fields = ['user__email']
    readonly_fields = ['last_activity']
    ordering = ['-date']

@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'priority', 'is_read', 'is_active', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'is_active', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_public', 'updated_at']
    list_filter = ['is_public', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at']
    ordering = ['key']

@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['backup_type', 'status', 'initiated_by', 'started_at', 'completed_at', 'file_size']
    list_filter = ['backup_type', 'status', 'started_at']
    search_fields = ['initiated_by__email', 'error_message']
    readonly_fields = ['started_at']
    ordering = ['-started_at']

@admin.register(MaintenanceWindow)
class MaintenanceWindowAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'end_time', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'start_time', 'end_time']
    search_fields = ['title', 'description', 'created_by__email']
    readonly_fields = ['created_at']
    ordering = ['-start_time']

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'ip_address', 'login_time', 'logout_time', 'is_active']
    list_filter = ['is_active', 'login_time', 'logout_time']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['login_time']
    ordering = ['-login_time']

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'position', 'is_enabled', 'created_at']
    list_filter = ['widget_type', 'is_enabled', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['position']

# Enhanced User Activity Tracking Admin
@admin.register(UserPageView)
class UserPageViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'page_name', 'page_url', 'ip_address', 'time_spent', 'created_at']
    list_filter = ['page_name', 'created_at']
    search_fields = ['user__email', 'page_url', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 50

@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'ip_address', 'session_key', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__email', 'action_type', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 50

@admin.register(UserEngagement)
class UserEngagementAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'total_time_spent', 'pages_visited', 'actions_performed',
        'files_uploaded', 'files_downloaded', 'last_activity'
    ]
    list_filter = ['date', 'last_activity']
    search_fields = ['user__email']
    readonly_fields = ['last_activity']
    ordering = ['-date']

@admin.register(RealTimeUserActivity)
class RealTimeUserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_page', 'current_action', 'ip_address', 'is_active', 'last_activity']
    list_filter = ['is_active', 'last_activity']
    search_fields = ['user__email', 'current_page', 'ip_address']
    readonly_fields = ['last_activity', 'created_at']
    ordering = ['-last_activity']

@admin.register(UserError)
class UserErrorAdmin(admin.ModelAdmin):
    list_display = ['user', 'error_type', 'error_message', 'page_url', 'ip_address', 'created_at']
    list_filter = ['error_type', 'created_at']
    search_fields = ['user__email', 'error_message', 'page_url', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 50

@admin.register(UserPerformance)
class UserPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'avg_session_duration', 'avg_pages_per_session',
        'file_upload_success_rate', 'error_rate'
    ]
    list_filter = ['date']
    search_fields = ['user__email']
    ordering = ['-date']
