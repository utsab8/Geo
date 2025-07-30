from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admindashboard.models import AdminActivity, SystemNotification, SystemMetrics, UserSession, UserPageView, UserAction, UserError, UserEngagement
from userdashboard.models import FileUpload, KMLData, CSVData, ShapefileData
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample dashboard data for testing admin dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--activities', type=int, default=20, help='Number of sample activities to create')
        parser.add_argument('--notifications', type=int, default=10, help='Number of sample notifications to create')
        parser.add_argument('--metrics', type=int, default=30, help='Number of sample system metrics to create')
        parser.add_argument('--sessions', type=int, default=15, help='Number of sample user sessions to create')
        parser.add_argument('--pageviews', type=int, default=50, help='Number of sample page views to create')
        parser.add_argument('--actions', type=int, default=30, help='Number of sample user actions to create')
        parser.add_argument('--errors', type=int, default=5, help='Number of sample user errors to create')
        parser.add_argument('--engagement', type=int, default=10, help='Number of sample user engagement records to create')

    def handle(self, *args, **options):
        activities_count = options['activities']
        notifications_count = options['notifications']
        metrics_count = options['metrics']
        sessions_count = options['sessions']
        pageviews_count = options['pageviews']
        actions_count = options['actions']
        errors_count = options['errors']
        engagement_count = options['engagement']
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Get or create regular users
        users = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                email=f'user{i+1}@example.com',
                defaults={
                    'username': f'user{i+1}',
                    'first_name': f'User{i+1}',
                    'last_name': 'Test',
                    'is_staff': False
                }
            )
            users.append(user)
        
        if created:
            self.stdout.write(f'Created admin user: {admin_user.email}')
        
        # Create sample activities
        self.create_sample_activities(admin_user, activities_count)
        
        # Create sample notifications
        self.create_sample_notifications(notifications_count)
        
        # Create sample system metrics
        self.create_sample_metrics(metrics_count)
        
        # Create sample user sessions
        self.create_sample_sessions(users, sessions_count)
        
        # Create sample page views
        self.create_sample_pageviews(users, pageviews_count)
        
        # Create sample user actions
        self.create_sample_actions(users, actions_count)
        
        # Create sample user errors
        self.create_sample_errors(users, errors_count)
        
        # Create sample user engagement (simplified)
        self.create_sample_engagement_simple(users, engagement_count)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created sample dashboard data')
        )
    
    def create_sample_activities(self, admin_user, count):
        """Create sample admin activities"""
        activity_types = [
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
            ('file_deleted', 'File deleted from system'),
            ('setting_updated', 'System setting updated'),
            ('notification_sent', 'System notification sent'),
            ('report_generated', 'System report generated'),
            ('data_exported', 'Data exported successfully'),
            ('maintenance_completed', 'Maintenance completed')
        ]
        
        for i in range(count):
            activity_type, description = random.choice(activity_types)
            AdminActivity.objects.create(
                activity_type=activity_type,
                description=description,
                admin_user=admin_user,
                metadata={'sample': True},
                ip_address='127.0.0.1',
                created_at=timezone.now() - timedelta(hours=random.randint(0, 168))
            )
        
        self.stdout.write(f'Created {count} sample activities')
    
    def create_sample_notifications(self, count):
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
            notification_type, title, message = random.choice(notification_types)
            SystemNotification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                priority='medium' if notification_type == 'info' else 'high',
                is_read=random.choice([True, False]),
                created_at=timezone.now() - timedelta(hours=random.randint(0, 168))
            )
        
        self.stdout.write(f'Created {count} sample notifications')
    
    def create_sample_metrics(self, count):
        """Create sample system metrics"""
        for i in range(count):
            SystemMetrics.objects.create(
                cpu_usage=random.uniform(10, 90),
                memory_usage=random.uniform(20, 85),
                disk_usage=random.uniform(30, 80),
                active_users=random.randint(5, 50),
                total_requests=random.randint(100, 1000),
                error_rate=random.uniform(0.1, 5.0),
                response_time=random.uniform(50, 500)
            )
        
        self.stdout.write(f'Created {count} sample system metrics')
    
    def create_sample_sessions(self, users, count):
        """Create sample user sessions"""
        for i in range(count):
            user = random.choice(users)
            UserSession.objects.create(
                user=user,
                session_key=f'session_{i}_{random.randint(1000, 9999)}',
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                is_active=random.choice([True, False])
            )
        
        self.stdout.write(f'Created {count} sample user sessions')
    
    def create_sample_pageviews(self, users, count):
        """Create sample page views"""
        pages = ['/dashboard/', '/uploads/', '/profile/', '/history/', '/help/', '/settings/']
        page_names = ['Dashboard', 'Uploads', 'Profile', 'History', 'Help', 'Settings']
        
        for i in range(count):
            user = random.choice(users)
            page_index = random.randint(0, len(pages) - 1)
            UserPageView.objects.create(
                user=user,
                page_url=pages[page_index],
                page_name=page_names[page_index],
                session_key=f'session_{random.randint(1000, 9999)}',
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                time_spent=random.randint(30, 600)
            )
        
        self.stdout.write(f'Created {count} sample page views')
    
    def create_sample_actions(self, users, count):
        """Create sample user actions"""
        action_types = ['login', 'logout', 'file_upload', 'file_download', 'profile_update', 'search']
        
        for i in range(count):
            user = random.choice(users)
            action_type = random.choice(action_types)
            UserAction.objects.create(
                user=user,
                action_type=action_type,
                action_data={'sample': True, 'description': f'User performed {action_type} action'},
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                session_key=f'session_{random.randint(1000, 9999)}'
            )
        
        self.stdout.write(f'Created {count} sample user actions')
    
    def create_sample_errors(self, users, count):
        """Create sample user errors"""
        error_types = ['file_upload_error', 'processing_error', 'validation_error', 'export_error', 'authentication_error']
        
        for i in range(count):
            user = random.choice(users)
            error_type = random.choice(error_types)
            UserError.objects.create(
                user=user,
                error_type=error_type,
                error_message=f'Sample {error_type} message {i+1}',
                error_details={'sample': True, 'stack_trace': f'Traceback (most recent call last):\n  File "sample.py", line {random.randint(1, 100)}, in sample_function\n    raise Exception("Sample error")'},
                page_url='/dashboard/',
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
        
        self.stdout.write(f'Created {count} sample user errors')
    
    def create_sample_engagement(self, users, count):
        """Create sample user engagement records"""
        created_count = 0
        for i in range(count):
            user = random.choice(users)
            date = timezone.now().date() - timedelta(days=random.randint(0, 30))
            
            # Use get_or_create to handle unique constraint
            engagement, created = UserEngagement.objects.get_or_create(
                user=user,
                date=date,
                defaults={
                    'total_time_spent': random.randint(300, 3600),  # 5 minutes to 1 hour
                    'pages_visited': random.randint(1, 20),
                    'actions_performed': random.randint(1, 50),
                    'files_uploaded': random.randint(0, 10),
                    'files_downloaded': random.randint(0, 15),
                    'searches_performed': random.randint(0, 25),
                    'exports_created': random.randint(0, 5)
                }
            )
            
            if created:
                created_count += 1
        
        self.stdout.write(f'Created {created_count} sample user engagement records')
    
    def create_sample_engagement_simple(self, users, count):
        """Create sample user engagement records (simplified)"""
        created_count = 0
        for i in range(count):
            user = random.choice(users)
            # Use different dates for each user to avoid conflicts
            date = timezone.now().date() - timedelta(days=i)
            
            try:
                engagement, created = UserEngagement.objects.get_or_create(
                    user=user,
                    date=date,
                    defaults={
                        'total_time_spent': random.randint(300, 3600),
                        'pages_visited': random.randint(1, 20),
                        'actions_performed': random.randint(1, 50),
                        'files_uploaded': random.randint(0, 10),
                        'files_downloaded': random.randint(0, 15),
                        'searches_performed': random.randint(0, 25),
                        'exports_created': random.randint(0, 5)
                    }
                )
                
                if created:
                    created_count += 1
            except Exception as e:
                # Skip if there's an error
                continue
        
        self.stdout.write(f'Created {created_count} sample user engagement records (simplified)') 