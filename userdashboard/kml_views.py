from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import os
from .models import KMLFile, KMLData, DownloadLog
from .kml_utils import KMLParser, KMLExporter, log_download, cleanup_temp_files
import logging

logger = logging.getLogger(__name__)

class KMLUploadView(LoginRequiredMixin, View):
    """View for KML file upload"""
    
    def get(self, request):
        """Display KML upload form"""
        return render(request, 'userdashboard/kml_upload.html')
    
    def post(self, request):
        """Handle KML file upload"""
        print("=== KML UPLOAD STARTED ===")
        logger.info("KML upload request received")
        
        try:
            if 'kml_file' not in request.FILES:
                print("❌ No kml_file in request.FILES")
                logger.error("No kml_file in request.FILES")
                messages.error(request, 'Please select a KML file to upload.')
                return redirect('kml_upload')
            
            kml_file = request.FILES['kml_file']
            print(f"✅ File received: {kml_file.name}, size: {kml_file.size}")
            logger.info(f"KML file received: {kml_file.name}, size: {kml_file.size}")
            
            # Validate file
            if not self._validate_kml_file(kml_file):
                print("❌ File validation failed")
                logger.error(f"KML file validation failed for {kml_file.name}")
                messages.error(request, 'Please upload a valid KML file (max 50MB).')
                return redirect('kml_upload')
            
            print("✅ File validation passed")
            logger.info("KML file validation passed")
            
            # Save KML file
            print("📁 Saving KML file to database...")
            kml_instance = KMLFile.objects.create(
                user=request.user,
                file=kml_file,
                original_filename=kml_file.name,
                file_size=kml_file.size,
                processing_status='processing'
            )
            print(f"✅ KML file saved with ID: {kml_instance.id}")
            logger.info(f"KML file saved with ID: {kml_instance.id}")
            
            # Parse KML file
            try:
                print("🔍 Parsing KML file...")
                parsed_data = self._parse_kml_file(kml_instance)
                print(f"✅ Parsed {len(parsed_data)} placemarks")
                logger.info(f"KML parsing successful: {len(parsed_data)} placemarks found")
                
                # Save parsed data
                print("💾 Saving parsed data to database...")
                # Get allowed fields from KMLData model
                allowed_fields = set(f.name for f in KMLData._meta.get_fields() if f.concrete and not f.auto_created and f.name != 'id')
                for i, data in enumerate(parsed_data):
                    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                    KMLData.objects.create(
                        kml_file=kml_instance,
                        **filtered_data
                    )
                    if i < 3:  # Log first 3 items
                        print(f"  - Saved placemark {i+1}: {data.get('placemark_name', 'Unnamed')}")
                
                print(f"✅ Saved {len(parsed_data)} placemarks to database")
                logger.info(f"Saved {len(parsed_data)} placemarks to database")
                
                kml_instance.is_processed = True
                kml_instance.processing_status = 'completed'
                kml_instance.save()
                
                print("✅ KML processing completed successfully")
                logger.info("KML processing completed successfully")
                
                messages.success(request, f'KML file "{kml_file.name}" uploaded and parsed successfully!')
                print(f"🔄 Redirecting to kml_preview with kml_id: {kml_instance.id}")
                logger.info(f"Redirecting to kml_preview with kml_id: {kml_instance.id}")
                return redirect('kml_preview', kml_id=kml_instance.id)
                
            except Exception as e:
                print(f"❌ Error parsing KML file: {str(e)}")
                logger.error(f"Error parsing KML file: {str(e)}", exc_info=True)
                kml_instance.processing_status = 'error'
                kml_instance.error_message = str(e)
                kml_instance.save()
                
                messages.error(request, f'Error parsing KML file: {str(e)}')
                return redirect('kml_upload')
                
        except Exception as e:
            print(f"❌ General error in KML upload: {str(e)}")
            logger.error(f"General error in KML upload: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred during upload. Please try again.')
            return redirect('kml_upload')
    
    def _validate_kml_file(self, file):
        """Validate KML file"""
        # Check file extension
        if not file.name.lower().endswith('.kml'):
            return False
        
        # Check file size (50MB limit)
        if file.size > 50 * 1024 * 1024:
            return False
        
        return True
    
    def _parse_kml_file(self, kml_instance):
        """Parse KML file and return comprehensive parsed data"""
        print(f"🔍 Starting KML parsing for file: {kml_instance.original_filename}")
        logger.info(f"Starting KML parsing for file: {kml_instance.original_filename}")
        
        try:
            # Get file path
            file_path = kml_instance.file.path
            print(f"📂 File path: {file_path}")
            logger.info(f"KML file path: {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"❌ File does not exist: {file_path}")
                logger.error(f"KML file does not exist: {file_path}")
                raise ValueError(f"KML file not found: {file_path}")
            
            print("✅ File exists, proceeding with parsing")
            
            # Parse KML with comprehensive data extraction
            parser = KMLParser(file_path)
            print("🔧 KMLParser created, calling parse_kml()...")
            parsed_data = parser.parse_kml()
            
            print(f"✅ KML parsing completed. Found {len(parsed_data)} placemarks")
            logger.info(f"KML parsing completed. Found {len(parsed_data)} placemarks")
            
            if not parsed_data:
                print("❌ No placemarks found in KML file")
                logger.warning("No placemarks found in KML file")
                raise ValueError("No valid placemarks found in KML file")
            
            # Log first few placemarks for debugging
            for i, data in enumerate(parsed_data[:3]):
                print(f"  Placemark {i+1}: {data.get('placemark_name', 'Unnamed')} - {data.get('geometry_type', 'Unknown')}")
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error in _parse_kml_file: {str(e)}")
            logger.error(f"Error in _parse_kml_file: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to parse KML file: {str(e)}")

class KMLPreviewView(LoginRequiredMixin, View):
    """View for KML data preview"""
    
    def get(self, request, kml_id):
        """Display KML data preview"""
        kml_file = get_object_or_404(KMLFile, id=kml_id, user=request.user)
        
        # Get parsed data with pagination
        kml_data = KMLData.objects.filter(kml_file=kml_file)
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            kml_data = kml_data.filter(
                Q(placemark_name__icontains=search_query) |
                Q(kitta_number__icontains=search_query) |
                Q(owner_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Sorting
        sort_by = request.GET.get('sort', 'created_at')
        sort_order = request.GET.get('order', 'asc')
        
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        
        kml_data = kml_data.order_by(sort_by)
        
        # Pagination
        paginator = Paginator(kml_data, 20)  # 20 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get download logs
        download_logs = DownloadLog.objects.filter(kml_file=kml_file).order_by('-downloaded_at')[:10]
        
        context = {
            'kml_file': kml_file,
            'page_obj': page_obj,
            'search_query': search_query,
            'sort_by': sort_by.replace('-', ''),
            'sort_order': sort_order,
            'download_logs': download_logs,
            'total_features': kml_data.count(),
            'geometry_types': kml_data.values_list('geometry_type', flat=True).distinct(),
        }
        
        return render(request, 'userdashboard/kml_preview.html', context)
    
    def post(self, request, kml_id):
        """Handle export requests"""
        kml_file = get_object_or_404(KMLFile, id=kml_id, user=request.user)
        
        if 'export_csv' in request.POST:
            return self._export_csv(request, kml_file)
        elif 'export_shapefile' in request.POST:
            return self._export_shapefile(request, kml_file)
        elif 'export_kml' in request.POST:
            return self._export_kml(request, kml_file)
        else:
            messages.error(request, 'Invalid export request.')
            return redirect('kml_preview', kml_id=kml_id)
    
    def _export_csv(self, request, kml_file):
        """Export KML data to CSV"""
        try:
            kml_data = KMLData.objects.filter(kml_file=kml_file)
            if not kml_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('kml_preview', kml_id=kml_file.id)
            filename = f"{kml_file.original_filename.replace('.kml', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = KMLExporter.export_to_csv(kml_data, filename)
            if not hasattr(response, 'content') or not response.content:
                logger.error('CSV export: No content in response!')
                messages.error(request, 'CSV export failed: No content generated.')
                return redirect('kml_preview', kml_id=kml_file.id)
            log_download(
                user=request.user,
                kml_file=kml_file,
                download_type='csv',
                file_path=f"{filename}.csv",
                file_size=len(response.content),
                request=request
            )
            logger.info(f"CSV export successful for KML {kml_file.id}")
            return response
        except Exception as e:
            logger.error(f"Error exporting CSV for KML {kml_file.id}: {e}")
            messages.error(request, f'Error creating CSV export: {str(e)}')
            return redirect('kml_preview', kml_id=kml_file.id)

    def _export_shapefile(self, request, kml_file):
        """Export KML data to Shapefile"""
        try:
            kml_data = KMLData.objects.filter(kml_file=kml_file)
            if not kml_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('kml_preview', kml_id=kml_file.id)
            filename = f"{kml_file.original_filename.replace('.kml', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = KMLExporter.export_to_shapefile(kml_data, filename)
            if not hasattr(response, 'content') or not response.content:
                logger.error('Shapefile export: No content in response!')
                messages.error(request, 'Shapefile export failed: No content generated.')
                return redirect('kml_preview', kml_id=kml_file.id)
            log_download(
                user=request.user,
                kml_file=kml_file,
                download_type='shapefile',
                file_path=f"{filename}.zip",
                file_size=len(response.content),
                request=request
            )
            logger.info(f"Shapefile export successful for KML {kml_file.id}")
            return response
        except Exception as e:
            logger.error(f"Error exporting shapefile for KML {kml_file.id}: {e}")
            messages.error(request, f'Error creating shapefile export: {str(e)}')
            return redirect('kml_preview', kml_id=kml_file.id)

    def _export_kml(self, request, kml_file):
        """Export KML data to KML file"""
        try:
            kml_data = KMLData.objects.filter(kml_file=kml_file)
            if not kml_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('kml_preview', kml_id=kml_file.id)
            filename = f"{kml_file.original_filename.replace('.kml', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = KMLExporter.export_to_kml(kml_data, filename)
            log_download(
                user=request.user,
                kml_file=kml_file,
                download_type='kml',
                file_path=f"{filename}.kml",
                file_size=len(response.content),
                request=request
            )
            return response
        except Exception as e:
            logger.error(f"Error exporting KML for KML {kml_file.id}: {e}")
            messages.error(request, f'Error creating KML export: {str(e)}')
            return redirect('kml_preview', kml_id=kml_file.id)

@method_decorator(csrf_exempt, name='dispatch')
class KMLAjaxView(LoginRequiredMixin, View):
    """AJAX view for KML data operations"""
    
    def get(self, request, kml_id):
        """Get KML data for AJAX requests"""
        try:
            kml_file = get_object_or_404(KMLFile, id=kml_id, user=request.user)
            
            # Get parameters
            search_query = request.GET.get('search', '')
            sort_by = request.GET.get('sort', 'created_at')
            sort_order = request.GET.get('order', 'asc')
            page = request.GET.get('page', 1)
            
            # Filter data
            kml_data = KMLData.objects.filter(kml_file=kml_file)
            
            if search_query:
                kml_data = kml_data.filter(
                    Q(placemark_name__icontains=search_query) |
                    Q(kitta_number__icontains=search_query) |
                    Q(owner_name__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
            
            # Sort data
            if sort_order == 'desc':
                sort_by = f'-{sort_by}'
            
            kml_data = kml_data.order_by(sort_by)
            
            # Paginate
            paginator = Paginator(kml_data, 20)
            page_obj = paginator.get_page(page)
            
            # Prepare data for JSON response
            data = []
            for item in page_obj:
                data.append({
                    'id': item.id,
                    'placemark_name': item.placemark_name or '',
                    'kitta_number': item.kitta_number or '',
                    'owner_name': item.owner_name or '',
                    'geometry_type': item.geometry_type,
                    'area_hectares': float(item.area_hectares) if item.area_hectares else None,
                    'area_sqm': float(item.area_sqm) if item.area_sqm else None,
                    'description': item.description or '',
                    'coordinates': item.coordinates,
                    'created_at': item.created_at.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'data': data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': page_obj.paginator.num_pages,
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next(),
                    'total_count': page_obj.paginator.count
                }
            })
            
        except Exception as e:
            logger.error(f"Error in KML AJAX view: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class KMLListView(LoginRequiredMixin, View):
    """View for listing user's KML files"""
    
    def get(self, request):
        """Display list of user's KML files"""
        kml_files = KMLFile.objects.filter(user=request.user)
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            kml_files = kml_files.filter(
                Q(original_filename__icontains=search_query) |
                Q(processing_status__icontains=search_query)
            )
        
        # Sorting
        sort_by = request.GET.get('sort', 'uploaded_at')
        sort_order = request.GET.get('order', 'desc')
        
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        
        kml_files = kml_files.order_by(sort_by)
        
        # Pagination
        paginator = Paginator(kml_files, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'sort_by': sort_by.replace('-', ''),
            'sort_order': sort_order,
        }
        
        return render(request, 'userdashboard/kml_list.html', context)

class KMLDeleteView(LoginRequiredMixin, View):
    """View for deleting KML files"""
    
    def post(self, request, kml_id):
        """Delete KML file"""
        try:
            kml_file = get_object_or_404(KMLFile, id=kml_id, user=request.user)
            
            # Delete associated data
            KMLData.objects.filter(kml_file=kml_file).delete()
            DownloadLog.objects.filter(kml_file=kml_file).delete()
            
            # Delete file from storage
            if kml_file.file:
                kml_file.file.delete(save=False)
            
            # Delete KML file record
            kml_file.delete()
            
            messages.success(request, f'KML file "{kml_file.original_filename}" deleted successfully.')
            return redirect('kml_list')
            
        except Exception as e:
            logger.error(f"Error deleting KML file {kml_id}: {e}")
            messages.error(request, 'Error deleting KML file. Please try again.')
            return redirect('kml_list') 

class KMLGeoJSONView(LoginRequiredMixin, View):
    """Return all KML geometries as GeoJSON for Leaflet preview"""
    def get(self, request, kml_id):
        from shapely.geometry import mapping
        import json
        kml_file = get_object_or_404(KMLFile, id=kml_id, user=request.user)
        kml_data = KMLData.objects.filter(kml_file=kml_file)
        features = []
        for item in kml_data:
            try:
                coords = json.loads(item.coordinates)
                if item.geometry_type == 'Point':
                    from shapely.geometry import Point
                    geom = Point(coords[0], coords[1])
                elif item.geometry_type == 'Polygon':
                    from shapely.geometry import Polygon
                    geom = Polygon(coords)
                elif item.geometry_type == 'LineString':
                    from shapely.geometry import LineString
                    geom = LineString(coords)
                else:
                    continue
                features.append({
                    'type': 'Feature',
                    'geometry': mapping(geom),
                    'properties': {
                        'placemark_name': item.placemark_name,
                        'kitta_number': item.kitta_number,
                        'owner_name': item.owner_name,
                        'geometry_type': item.geometry_type,
                        'area_hectares': float(item.area_hectares) if item.area_hectares else None,
                        'area_sqm': float(item.area_sqm) if item.area_sqm else None,
                        'description': item.description,
                        'id': str(item.id)
                    }
                })
            except Exception as e:
                continue
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        return JsonResponse(geojson) 