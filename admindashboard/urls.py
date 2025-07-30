from django.urls import path
from .views import (
    AdminDashboardView, UsersManagementView, SurveysManagementView,
    SystemManagementView, SettingsManagementView,
    DashboardStatsAPIView, UsersAPIView, SystemMetricsAPIView,
    NotificationsAPIView, BackupAPIView, ActivityAPIView,
    UserActivityAPIView, RealTimeActivityAPIView, UserErrorsAPIView,
    SurveysAPIView, mark_notification_read, update_system_metrics
)

urlpatterns = [
    # Main dashboard pages
    path('', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('users/', UsersManagementView.as_view(), name='admin-users'),
    path('surveys/', SurveysManagementView.as_view(), name='admin-survey'),
    path('system/', SystemManagementView.as_view(), name='admin-system'),
    path('settings/', SettingsManagementView.as_view(), name='admin-settings'),
    
    # API endpoints
    path('api/stats/', DashboardStatsAPIView.as_view(), name='admin_api_stats'),
    path('api/users/', UsersAPIView.as_view(), name='admin_api_users'),
    path('api/users/<int:user_id>/', UsersAPIView.as_view(), name='admin_api_user_detail'),
    path('api/metrics/', SystemMetricsAPIView.as_view(), name='admin_api_metrics'),
    path('api/notifications/', NotificationsAPIView.as_view(), name='admin_api_notifications'),
    path('api/backup/', BackupAPIView.as_view(), name='admin_api_backup'),
    path('api/activities/', ActivityAPIView.as_view(), name='admin_api_activities'),
    path('api/user-activity/', UserActivityAPIView.as_view(), name='admin_api_user_activity'),
    path('api/real-time-activity/', RealTimeActivityAPIView.as_view(), name='admin_api_real_time_activity'),
    path('api/user-errors/', UserErrorsAPIView.as_view(), name='admin_api_user_errors'),
    path('api/notifications/<int:notification_id>/read/', mark_notification_read, name='admin_api_notification_read'),
    path('api/metrics/update/', update_system_metrics, name='admin_api_update_metrics'),
    
    # Survey API endpoints
    path('api/surveys/files/', SurveysAPIView.as_view(), name='admin_api_surveys_files'),
    path('api/surveys/files/<uuid:file_id>/', SurveysAPIView.as_view(), name='admin_api_survey_file_detail'),
    path('api/surveys/files/<uuid:file_id>/preview/', SurveysAPIView.as_view(), name='admin_api_surveys_file_preview'),
    path('api/surveys/files/<uuid:file_id>/download/', SurveysAPIView.as_view(), name='admin_api_surveys_file_download'),
    path('api/surveys/files/<uuid:file_id>/delete/', SurveysAPIView.as_view(), name='admin_api_surveys_file_delete'),
    path('api/surveys/upload/', SurveysAPIView.as_view(), name='admin_api_surveys_upload'),
    
    # Additional API endpoints for system
    path('api/system/status/', SystemManagementView.as_view(), name='admin_api_system_status'),
    path('api/system/performance/', SystemManagementView.as_view(), name='admin_api_system_performance'),
    path('api/system/activity/', SystemManagementView.as_view(), name='admin_api_system_activity'),
    path('api/system/logs/', SystemManagementView.as_view(), name='admin_api_system_logs'),
    path('api/system/backup/', SystemManagementView.as_view(), name='admin_api_system_backup'),
    path('api/system/maintenance/', SystemManagementView.as_view(), name='admin_api_system_maintenance'),
    
    # Additional API endpoints for settings
    path('api/settings/', SettingsManagementView.as_view(), name='admin_api_settings'),
]

