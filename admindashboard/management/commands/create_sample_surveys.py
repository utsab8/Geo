from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from userdashboard.models import FileUpload, CSVData, ShapefileData
from django.utils import timezone
from datetime import timedelta
import random
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample survey data for testing admin dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sample files to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': True
            }
        )
        
        if created:
            self.stdout.write(f'Created test user: {user.email}')
        
        # Create sample files
        file_types = ['csv', 'shapefile']  # Remove KML for now to avoid complexity
        statuses = ['pending', 'processing', 'completed', 'failed']
        
        for i in range(count):
            file_type = random.choice(file_types)
            status = random.choice(statuses)
            
            # Create file upload
            file_upload = FileUpload.objects.create(
                user=user,
                original_filename=f'sample_{file_type}_{i+1}.{file_type}',
                file_type=file_type,
                file_size=random.randint(1024, 1024*1024),  # 1KB to 1MB
                mime_type=f'application/{file_type}',
                description=f'Sample {file_type.upper()} file for testing',
                status=status,
                feature_count=random.randint(10, 1000),
                download_count=random.randint(0, 50),
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            
            # Add processing times for completed files
            if status == 'completed':
                file_upload.processing_started = file_upload.created_at + timedelta(minutes=5)
                file_upload.processing_completed = file_upload.processing_started + timedelta(minutes=random.randint(1, 10))
                file_upload.save()
            
            # Add error message for failed files
            if status == 'failed':
                file_upload.error_message = f'Sample error message for {file_upload.original_filename}'
                file_upload.save()
            
            # Create sample data based on file type
            if file_type == 'csv':
                self.create_csv_data(file_upload, i)
            elif file_type == 'shapefile':
                self.create_shapefile_data(file_upload, i)
            
            self.stdout.write(f'Created sample file: {file_upload.original_filename}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} sample survey files')
        )
    

    
    def create_csv_data(self, file_upload, index):
        """Create sample CSV data"""
        for j in range(random.randint(10, 50)):
            CSVData.objects.create(
                file_upload=file_upload,
                row_number=j+1,
                data={
                    'id': j+1,
                    'name': f'Feature {j+1}',
                    'type': random.choice(['Residential', 'Commercial', 'Agricultural']),
                    'area': random.uniform(100, 10000),
                    'coordinates': '85.3240,27.7172',
                    'description': f'Sample CSV row {j+1}'
                },
                geometry_type='Point',
                coordinates='[[85.3240, 27.7172]]'
            )
    
    def create_shapefile_data(self, file_upload, index):
        """Create sample Shapefile data"""
        for j in range(random.randint(5, 15)):
            ShapefileData.objects.create(
                file_upload=file_upload,
                feature_id=j+1,
                geometry_type=random.choice(['Point', 'Polygon', 'LineString']),
                coordinates='[[85.3240, 27.7172], [85.3241, 27.7173]]',
                attributes={
                    'FID': j+1,
                    'NAME': f'Shapefile Feature {j+1}',
                    'TYPE': random.choice(['Building', 'Road', 'Parcel']),
                    'AREA': random.uniform(100, 5000),
                    'DESCRIPTION': f'Sample shapefile feature {j+1}'
                }
            ) 