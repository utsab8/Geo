from django.core.management.base import BaseCommand
from admindashboard.models import AdminSettings

class Command(BaseCommand):
    help = 'Create default settings for admin dashboard'

    def handle(self, *args, **options):
        default_settings = {
            # General Settings
            'siteName': 'GeoSurveyPro',
            'siteDescription': 'Advanced Geospatial Survey Management System',
            'timezone': 'UTC',
            'maintenanceMode': False,
            'debugMode': False,
            
            # Security Settings
            'twoFactorAuth': False,
            'sessionTimeout': 30,
            'passwordComplexity': 'medium',
            'ipWhitelist': '',
            'rateLimit': 100,
            
            # Backup Settings
            'autoBackup': True,
            'backupFrequency': 'weekly',
            'backupRetention': 30,
            'backupLocation': '/backups/',
            'compressBackups': True,
            
            # Notification Settings
            'emailNotifications': True,
            'systemAlerts': True,
            'userActivityNotifications': False,
            'adminEmail': 'admin@geosurveypro.com',
            
            # Appearance Settings
            'theme': 'light',
            'primaryColor': '#2563eb',
            'sidebarPosition': 'left',
            'compactMode': False,
            
            # System Settings
            'maxFileSize': 10,  # MB
            'allowedFileTypes': 'kml,csv,shp,zip',
            'autoProcessFiles': True,
            'enableAnalytics': True,
            'enableLogging': True,
            'logRetentionDays': 30,
            
            # Email Settings
            'smtpHost': '',
            'smtpPort': 587,
            'smtpUsername': '',
            'smtpPassword': '',
            'smtpUseTLS': True,
            'fromEmail': 'noreply@geosurveypro.com',
            
            # API Settings
            'apiRateLimit': 1000,
            'apiKeyExpiration': 30,  # days
            'enableAPIAccess': True,
            'requireAPIKey': False,
            
            # User Settings
            'allowRegistration': True,
            'requireEmailVerification': True,
            'maxLoginAttempts': 5,
            'lockoutDuration': 15,  # minutes
            'passwordExpirationDays': 90,
            
            # File Processing Settings
            'enableAutoValidation': True,
            'enableAutoConversion': True,
            'maxProcessingTime': 300,  # seconds
            'enableParallelProcessing': True,
            'maxParallelJobs': 4,
            
            # Storage Settings
            'storageProvider': 'local',  # local, s3, azure
            'storagePath': '/uploads/',
            'enableCompression': True,
            'maxStorageQuota': 1024,  # MB per user
            'enableStorageQuota': True,
            
            # Monitoring Settings
            'enableSystemMonitoring': True,
            'monitoringInterval': 60,  # seconds
            'enablePerformanceTracking': True,
            'enableErrorTracking': True,
            'enableUserTracking': True,
            
            # Maintenance Settings
            'enableAutoMaintenance': True,
            'maintenanceSchedule': 'weekly',
            'maintenanceTime': '02:00',
            'enableAutoCleanup': True,
            'cleanupRetentionDays': 90,
        }
        
        created_count = 0
        updated_count = 0
        
        for key, value in default_settings.items():
            setting, created = AdminSettings.objects.get_or_create(
                key=key,
                defaults={
                    'value': str(value),
                    'description': f'Default setting for {key}',
                    'is_public': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created setting: {key} = {value}')
            else:
                # Update existing setting if it's different
                if setting.value != str(value):
                    setting.value = str(value)
                    setting.save()
                    updated_count += 1
                    self.stdout.write(f'Updated setting: {key} = {value}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed settings: {created_count} created, {updated_count} updated'
            )
        ) 