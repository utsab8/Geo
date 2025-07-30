from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admindashboard.models import SystemNotification, MaintenanceWindow, BackupLog, AdminActivity
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample system data for testing admin dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--notifications',
            type=int,
            default=10,
            help='Number of sample notifications to create'
        )
        parser.add_argument(
            '--maintenance',
            type=int,
            default=3,
            help='Number of sample maintenance windows to create'
        )
        parser.add_argument(
            '--backups',
            type=int,
            default=5,
            help='Number of sample backup logs to create'
        )

    def handle(self, *args, **options):
        notifications_count = options['notifications']
        maintenance_count = options['maintenance']
        backups_count = options['backups']
        
        # Get or create a test admin user
        user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            self.stdout.write(f'Created admin user: {user.email}')
        
        # Create sample notifications
        self.create_sample_notifications(user, notifications_count)
        
        # Create sample maintenance windows
        self.create_sample_maintenance_windows(user, maintenance_count)
        
        # Create sample backup logs
        self.create_sample_backup_logs(user, backups_count)
        
        # Create sample admin activities
        self.create_sample_admin_activities(user)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created sample system data')
        )
    
    def create_sample_notifications(self, user, count):
        """Create sample system notifications"""
        notification_types = [
            ('info', 'System Update', 'System update completed successfully'),
            ('warning', 'High CPU Usage', 'CPU usage is above 80%'),
            ('error', 'Database Connection', 'Database connection timeout'),
            ('critical', 'Disk Space Low', 'Disk space is critically low'),
            ('info', 'Backup Completed', 'Daily backup completed successfully'),
            ('warning', 'Memory Usage', 'Memory usage is high'),
            ('error', 'Service Down', 'Email service is not responding'),
            ('info', 'Security Scan', 'Security scan completed'),
            ('warning', 'Network Latency', 'High network latency detected'),
            ('critical', 'System Crash', 'Application server crashed')
        ]
        
        for i in range(count):
            notification_type = random.choice(notification_types)
            severity, title, message = notification_type
            
            # Map severity to notification_type and priority
            notification_type_map = {
                'info': 'info',
                'warning': 'warning',
                'error': 'error',
                'critical': 'error'
            }
            
            priority_map = {
                'info': 'low',
                'warning': 'medium',
                'error': 'high',
                'critical': 'critical'
            }
            
            SystemNotification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type_map[severity],
                priority=priority_map[severity],
                is_read=random.choice([True, False]),
                created_at=timezone.now() - timedelta(
                    hours=random.randint(0, 168)  # Last 7 days
                )
            )
        
        self.stdout.write(f'Created {count} sample notifications')
    
    def create_sample_maintenance_windows(self, user, count):
        """Create sample maintenance windows"""
        maintenance_types = [
            ('System Maintenance', 'Regular system maintenance and updates'),
            ('Database Optimization', 'Database optimization and cleanup'),
            ('Security Updates', 'Security patches and updates'),
            ('Hardware Maintenance', 'Hardware maintenance and upgrades'),
            ('Backup System', 'Backup system maintenance')
        ]
        
        for i in range(count):
            title, description = random.choice(maintenance_types)
            
            # Create maintenance window in the future
            start_time = timezone.now() + timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23)
            )
            end_time = start_time + timedelta(hours=random.randint(1, 4))
            
            MaintenanceWindow.objects.create(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                created_by=user
            )
        
        self.stdout.write(f'Created {count} sample maintenance windows')
    
    def create_sample_backup_logs(self, user, count):
        """Create sample backup logs"""
        backup_types = ['database', 'files', 'system', 'configuration']
        
        for i in range(count):
            backup_type = random.choice(backup_types)
            status = random.choice(['completed', 'failed', 'running'])
            
            backup_log = BackupLog.objects.create(
                backup_type=backup_type,
                status=status,
                initiated_by=user
            )
            
            # Set custom created_at time
            backup_log.started_at = timezone.now() - timedelta(
                days=random.randint(0, 30)
            )
            backup_log.save()
            
            if status == 'completed':
                backup_log.completed_at = backup_log.started_at + timedelta(minutes=random.randint(5, 30))
                backup_log.file_path = f'/backups/{backup_type}_{backup_log.started_at.strftime("%Y%m%d_%H%M%S")}.backup'
                backup_log.file_size = random.randint(1024 * 1024, 100 * 1024 * 1024)  # 1MB to 100MB
                backup_log.save()
            elif status == 'failed':
                backup_log.error_message = f'Backup failed due to {random.choice(["disk space", "permission error", "network timeout", "database error"])}'
                backup_log.save()
        
        self.stdout.write(f'Created {count} sample backup logs')
    
    def create_sample_admin_activities(self, user):
        """Create sample admin activities"""
        activities = [
            ('user_created', 'New user account created'),
            ('user_updated', 'User profile updated'),
            ('file_uploaded', 'New file uploaded to system'),
            ('backup_created', 'System backup completed'),
            ('maintenance_scheduled', 'Maintenance window scheduled'),
            ('cache_cleared', 'System cache cleared'),
            ('service_restarted', 'Service restarted'),
            ('security_scan', 'Security scan initiated'),
            ('system_update', 'System update applied'),
            ('log_analyzed', 'System logs analyzed'),
            ('performance_check', 'Performance metrics checked'),
            ('error_resolved', 'System error resolved'),
            ('backup_restored', 'Backup restored successfully'),
            ('user_deleted', 'User account deleted'),
            ('file_deleted', 'File deleted from system')
        ]
        
        for activity_type, description in activities:
            AdminActivity.objects.create(
                activity_type=activity_type,
                description=description,
                admin_user=user,
                metadata={'sample': True},
                ip_address='127.0.0.1',
                created_at=timezone.now() - timedelta(
                    hours=random.randint(0, 168)  # Last 7 days
                )
            )
        
        self.stdout.write(f'Created {len(activities)} sample admin activities') 