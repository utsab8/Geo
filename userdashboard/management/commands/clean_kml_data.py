from django.core.management.base import BaseCommand
from userdashboard.models import KMLData
import re


class Command(BaseCommand):
    help = 'Clean KML data by removing HTML tags and formatting text properly'

    def handle(self, *args, **options):
        self.stdout.write('Starting KML data cleaning process...')
        
        kml_data = KMLData.objects.all()
        processed_count = 0
        cleaned_count = 0
        
        for item in kml_data:
            original_owner = item.owner_name
            original_placemark = item.placemark_name
            original_description = item.description
            
            # Clean HTML tags from text fields
            if item.owner_name:
                item.owner_name = re.sub(r'<[^>]+>', '', item.owner_name)
                item.owner_name = re.sub(r'\s+', ' ', item.owner_name).strip()
            
            if item.placemark_name:
                item.placemark_name = re.sub(r'<[^>]+>', '', item.placemark_name)
                item.placemark_name = re.sub(r'\s+', ' ', item.placemark_name).strip()
            
            if item.description:
                item.description = re.sub(r'<[^>]+>', '', item.description)
                item.description = re.sub(r'\s+', ' ', item.description).strip()
            
            # Clean address fields
            if item.address:
                item.address = re.sub(r'<[^>]+>', '', item.address)
                item.address = re.sub(r'\s+', ' ', item.address).strip()
            
            if item.locality:
                item.locality = re.sub(r'<[^>]+>', '', item.locality)
                item.locality = re.sub(r'\s+', ' ', item.locality).strip()
            
            if item.administrative_area:
                item.administrative_area = re.sub(r'<[^>]+>', '', item.administrative_area)
                item.administrative_area = re.sub(r'\s+', ' ', item.administrative_area).strip()
            
            # Check if any changes were made
            if (original_owner != item.owner_name or 
                original_placemark != item.placemark_name or 
                original_description != item.description):
                cleaned_count += 1
            
            processed_count += 1
            item.save()
            
            if processed_count % 100 == 0:
                self.stdout.write(f'Processed {processed_count} records...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {processed_count} records. Cleaned {cleaned_count} records.'
            )
        ) 