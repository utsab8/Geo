from django.core.management.base import BaseCommand
from django.utils import timezone
from admindashboard.models import (
    AdminSettings, SystemNotification, SystemMetrics, DashboardWidget
)
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Setup initial admin dashboard data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up admin dashboard...')
        
        # Create default admin settings
        self.create_default_settings()
        
        # Create sample notifications
        self.create_sample_notifications()
        
        # Create sample system metrics
        self.create_sample_metrics()
        
        # Create default dashboard widgets
        self.create_default_widgets()
        
        self.stdout.write(
            self.style.SUCCESS('Admin dashboard setup completed successfully!')
        )

    def create_default_settings(self):
        """Create default admin settings"""
        settings_data = [
            {
                'key': 'site_name',
                'value': 'GeoSurveyPro',
                'description': 'Site name displayed in admin dashboard',
                'is_public': True
            },
            {
                'key': 'max_file_size',
                'value': '10',
                'description': 'Maximum file upload size in MB',
                'is_public': False
            },
            {
                'key': 'auto_backup_enabled',
                'value': 'true',
                'description': 'Enable automatic system backups',
                'is_public': False
            },
            {
                'key': 'backup_retention_days',
                'value': '30',
                'description': 'Number of days to retain backup files',
                'is_public': False
            },
            {
                'key': 'maintenance_mode',
                'value': 'false',
                'description': 'Enable maintenance mode',
                'is_public': True
            }
        ]
        
        for setting_data in settings_data:
            AdminSettings.objects.get_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
        
        self.stdout.write('✓ Default settings created')

    def create_sample_notifications(self):
        """Create sample system notifications"""
        notifications_data = [
            {
                'title': 'Welcome to Admin Dashboard',
                'message': 'Your admin dashboard is now ready. You can manage users, monitor system performance, and configure settings.',
                'notification_type': 'info',
                'priority': 'low'
            },
            {
                'title': 'System Backup Available',
                'message': 'Automatic system backup is now available. You can configure backup settings in the system section.',
                'notification_type': 'success',
                'priority': 'medium'
            }
        ]
        
        for notification_data in notifications_data:
            SystemNotification.objects.get_or_create(
                title=notification_data['title'],
                defaults=notification_data
            )
        
        self.stdout.write('✓ Sample notifications created')

    def create_sample_metrics(self):
        """Create sample system metrics"""
        # Create metrics for the last 24 hours
        now = timezone.now()
        for i in range(24):
            timestamp = now - timedelta(hours=i)
            SystemMetrics.objects.get_or_create(
                timestamp=timestamp,
                defaults={
                    'cpu_usage': 15.0 + (i % 10),
                    'memory_usage': 45.0 + (i % 15),
                    'disk_usage': 60.0 + (i % 5),
                    'active_users': 5 + (i % 8),
                    'total_requests': 100 + (i * 50),
                    'error_rate': 0.5 + (i % 2),
                    'response_time': 120 + (i % 50)
                }
            )
        
        self.stdout.write('✓ Sample system metrics created')

    def create_default_widgets(self):
        """Create default dashboard widgets"""
        widgets_data = [
            {
                'name': 'User Statistics',
                'widget_type': 'stats',
                'configuration': {
                    'title': 'User Overview',
                    'metrics': ['total_users', 'active_users', 'new_users_24h']
                },
                'position': 0,
                'is_enabled': True
            },
            {
                'name': 'System Performance',
                'widget_type': 'chart',
                'configuration': {
                    'title': 'System Metrics',
                    'chart_type': 'line',
                    'metrics': ['cpu_usage', 'memory_usage', 'disk_usage']
                },
                'position': 1,
                'is_enabled': True
            },
            {
                'name': 'Recent Activities',
                'widget_type': 'activity',
                'configuration': {
                    'title': 'Latest Activities',
                    'limit': 10
                },
                'position': 2,
                'is_enabled': True
            }
        ]
        
        for widget_data in widgets_data:
            DashboardWidget.objects.get_or_create(
                name=widget_data['name'],
                defaults=widget_data
            )
        
        self.stdout.write('✓ Default dashboard widgets created') 