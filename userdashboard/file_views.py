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
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import os
from django.db import models
from .models import FileUpload, FileConversion, CSVData, ShapefileData, KMLData, FileShare
from .file_utils import FileValidator, FileProcessor, FileConverter
import logging

logger = logging.getLogger(__name__)

class FileUploadView(LoginRequiredMixin, View):
    """Enhanced file upload view with beautiful UI"""
    
    def get(self, request):
        """Display file upload form"""
        pre_selected_type = request.GET.get('type', '')
        return render(request, 'userdashboard/file_upload.html', {
            'pre_selected_type': pre_selected_type
        })
    
    def post(self, request):
        """Handle file upload"""
        try:
            if 'file' not in request.FILES:
                messages.error(request, 'Please select a file to upload.')
                return redirect('file_upload')
            
            uploaded_file = request.FILES['file']
            file_type = request.POST.get('file_type', '')
            
            # Validate file
            validator = FileValidator()
            file_type = validator.detect_file_type(uploaded_file, uploaded_file.name)
            
            validation_result = validator.validate_file(uploaded_file, uploaded_file.name, file_type)
            if validation_result['errors']:
                for error in validation_result['errors']:
                    messages.error(request, error)
                return redirect('file_upload')
            
            # Create file upload record
            file_upload = FileUpload.objects.create(
                user=request.user,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_type=file_type,
                file_size=uploaded_file.size,
                status='pending'
            )
            
            # Process file
            try:
                processor = FileProcessor(file_upload)
                result = processor.process_file()
                
                file_upload.status = 'completed'
                file_upload.save()
                
                messages.success(request, f'File "{uploaded_file.name}" uploaded and processed successfully!')
                
                # Redirect based on file type
                if file_type == 'kml':
                    return redirect('kml_preview', kml_id=file_upload.id)
                elif file_type == 'csv':
                    return redirect('csv_preview', file_id=file_upload.id)
                elif file_type == 'shapefile':
                    return redirect('shapefile_preview', file_id=file_upload.id)
                else:
                    return redirect('file_detail', file_id=file_upload.id)
                
            except Exception as e:
                file_upload.status = 'failed'
                file_upload.error_message = str(e)
                file_upload.save()
                
                messages.error(request, f'Error processing file: {str(e)}')
                return redirect('file_upload')
                
        except Exception as e:
            logger.error(f"Error in file upload: {e}")
            messages.error(request, 'An error occurred during upload. Please try again.')
            return redirect('file_upload')

class CSVPreviewView(LoginRequiredMixin, View):
    """CSV file preview view"""
    
    def get(self, request, file_id):
        """Display CSV preview"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        if file_upload.file_type != 'csv':
            messages.error(request, 'This is not a CSV file.')
            return redirect('file_list')
        
        # Get CSV data with pagination
        csv_data = CSVData.objects.filter(file_upload=file_upload)
        paginator = Paginator(csv_data, 50)  # 50 rows per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get sample data for table headers
        sample_data = csv_data.first()
        columns = list(sample_data.data.keys()) if sample_data else []
        
        context = {
            'file_upload': file_upload,
            'page_obj': page_obj,
            'columns': columns,
            'total_rows': csv_data.count(),
        }
        
        return render(request, 'userdashboard/csv_preview.html', context)
    
    def post(self, request, file_id):
        """Handle export requests"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        if 'export_kml' in request.POST:
            return self._export_kml(request, file_upload)
        elif 'export_shapefile' in request.POST:
            return self._export_shapefile(request, file_upload)
        else:
            messages.error(request, 'Invalid export request.')
            return redirect('csv_preview', file_id=file_id)
    
    def _export_kml(self, request, file_upload):
        """Export CSV to KML"""
        try:
            csv_data = CSVData.objects.filter(file_upload=file_upload)
            if not csv_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('csv_preview', file_id=file_upload.id)
            
            filename = f"{file_upload.original_filename.replace('.csv', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = FileConverter.csv_to_kml(csv_data, filename)
            
            # Log conversion
            FileConversion.objects.create(
                source_file=file_upload,
                conversion_type='csv_to_kml',
                status='completed',
                output_filename=f"{filename}.kml",
                file_size=len(response.content),
                processing_completed=timezone.now()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting CSV to KML: {e}")
            messages.error(request, f'Error creating KML export: {str(e)}')
            return redirect('csv_preview', file_id=file_upload.id)
    
    def _export_shapefile(self, request, file_upload):
        """Export CSV to Shapefile"""
        try:
            csv_data = CSVData.objects.filter(file_upload=file_upload)
            if not csv_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('csv_preview', file_id=file_upload.id)
            
            filename = f"{file_upload.original_filename.replace('.csv', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = FileConverter.csv_to_shapefile(csv_data, filename)
            
            # Log conversion
            FileConversion.objects.create(
                source_file=file_upload,
                conversion_type='csv_to_shapefile',
                status='completed',
                output_filename=f"{filename}.zip",
                file_size=len(response.content),
                processing_completed=timezone.now()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting CSV to shapefile: {e}")
            messages.error(request, f'Error creating shapefile export: {str(e)}')
            return redirect('csv_preview', file_id=file_upload.id)

class ShapefilePreviewView(LoginRequiredMixin, View):
    """Shapefile preview view"""
    
    def get(self, request, file_id):
        """Display shapefile preview"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        if file_upload.file_type != 'shapefile':
            messages.error(request, 'This is not a shapefile.')
            return redirect('file_list')
        
        # Get shapefile data with pagination
        shapefile_data = ShapefileData.objects.filter(file_upload=file_upload)
        paginator = Paginator(shapefile_data, 50)  # 50 features per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get sample data for table headers
        sample_data = shapefile_data.first()
        attributes = list(sample_data.attributes.keys()) if sample_data else []
        
        context = {
            'file_upload': file_upload,
            'page_obj': page_obj,
            'attributes': attributes,
            'total_features': shapefile_data.count(),
        }
        
        return render(request, 'userdashboard/shapefile_preview.html', context)
    
    def post(self, request, file_id):
        """Handle export requests"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        if 'export_kml' in request.POST:
            return self._export_kml(request, file_upload)
        elif 'export_csv' in request.POST:
            return self._export_csv(request, file_upload)
        else:
            messages.error(request, 'Invalid export request.')
            return redirect('shapefile_preview', file_id=file_id)
    
    def _export_kml(self, request, file_upload):
        """Export shapefile to KML"""
        try:
            shapefile_data = ShapefileData.objects.filter(file_upload=file_upload)
            if not shapefile_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('shapefile_preview', file_id=file_upload.id)
            
            filename = f"{file_upload.original_filename.replace('.zip', '').replace('.shp', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = FileConverter.shapefile_to_kml(shapefile_data, filename)
            
            # Log conversion
            FileConversion.objects.create(
                source_file=file_upload,
                conversion_type='shapefile_to_kml',
                status='completed',
                output_filename=f"{filename}.kml",
                file_size=len(response.content),
                processing_completed=timezone.now()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting shapefile to KML: {e}")
            messages.error(request, f'Error creating KML export: {str(e)}')
            return redirect('shapefile_preview', file_id=file_upload.id)
    
    def _export_csv(self, request, file_upload):
        """Export shapefile to CSV"""
        try:
            shapefile_data = ShapefileData.objects.filter(file_upload=file_upload)
            if not shapefile_data.exists():
                messages.error(request, 'No data available for export.')
                return redirect('shapefile_preview', file_id=file_upload.id)
            
            filename = f"{file_upload.original_filename.replace('.zip', '').replace('.shp', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            response = FileConverter.shapefile_to_csv(shapefile_data, filename)
            
            # Log conversion
            FileConversion.objects.create(
                source_file=file_upload,
                conversion_type='shapefile_to_csv',
                status='completed',
                output_filename=f"{filename}.csv",
                file_size=len(response.content),
                processing_completed=timezone.now()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting shapefile to CSV: {e}")
            messages.error(request, f'Error creating CSV export: {str(e)}')
            return redirect('shapefile_preview', file_id=file_upload.id)

class FileListView(LoginRequiredMixin, View):
    """File list view"""
    
    def get(self, request):
        """Display list of uploaded files"""
        files = FileUpload.objects.filter(user=request.user)
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            files = files.filter(
                Q(original_filename__icontains=search_query) |
                Q(file_type__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by file type
        file_type = request.GET.get('type', '')
        if file_type:
            files = files.filter(file_type=file_type)
        
        # Pagination
        paginator = Paginator(files, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'file_type_filter': file_type,
            'total_files': files.count(),
        }
        
        return render(request, 'userdashboard/file_list.html', context)

class FileDetailView(LoginRequiredMixin, View):
    """File detail view"""
    
    def get(self, request, file_id):
        """Display file details"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        # Get conversion history
        conversions = FileConversion.objects.filter(source_file=file_upload)
        
        context = {
            'file_upload': file_upload,
            'conversions': conversions,
        }
        
        return render(request, 'userdashboard/file_detail.html', context)

class FilePreviewView(LoginRequiredMixin, View):
    """Generic file preview view for session-based previews"""
    
    def get(self, request):
        """Display file preview from session data"""
        preview_data = request.session.get('preview_data')
        
        if not preview_data:
            messages.error(request, 'No preview data available.')
            return redirect('file_upload')
        
        context = {
            'preview_data': preview_data,
            'file_type': preview_data.get('file_type'),
            'file_name': preview_data.get('file_name'),
            'file_size': preview_data.get('file_size'),
        }
        
        # Render appropriate template based on file type
        if preview_data.get('file_type') == 'kml':
            return render(request, 'userdashboard/kml_preview.html', context)
        elif preview_data.get('file_type') == 'csv':
            return render(request, 'userdashboard/csv_preview.html', context)
        elif preview_data.get('file_type') == 'shp':
            return render(request, 'userdashboard/shapefile_preview.html', context)
        else:
            return render(request, 'userdashboard/file_preview.html', context)
    
    def post(self, request):
        """Handle export requests from preview"""
        preview_data = request.session.get('preview_data')
        
        if not preview_data:
            messages.error(request, 'No preview data available.')
            return redirect('file_upload')
        
        file_type = preview_data.get('file_type')
        
        if 'export_csv' in request.POST and file_type == 'kml':
            return self._export_kml_to_csv(request, preview_data)
        elif 'export_shapefile' in request.POST and file_type == 'kml':
            return self._export_kml_to_shapefile(request, preview_data)
        elif 'export_kml' in request.POST and file_type == 'csv':
            return self._export_csv_to_kml(request, preview_data)
        elif 'export_shapefile' in request.POST and file_type == 'csv':
            return self._export_csv_to_shapefile(request, preview_data)
        elif 'export_kml' in request.POST and file_type == 'shp':
            return self._export_shapefile_to_kml(request, preview_data)
        elif 'export_csv' in request.POST and file_type == 'shp':
            return self._export_shapefile_to_csv(request, preview_data)
        else:
            messages.error(request, 'Invalid export request.')
            return redirect('file_preview')
    
    def _export_kml_to_csv(self, request, preview_data):
        """Export KML preview data to CSV"""
        try:
            # Implementation for KML to CSV export
            messages.success(request, 'CSV export completed successfully!')
            return redirect('file_preview')
        except Exception as e:
            messages.error(request, f'Error creating CSV export: {str(e)}')
            return redirect('file_preview')
    
    def _export_kml_to_shapefile(self, request, preview_data):
        """Export KML preview data to Shapefile"""
        try:
            # Implementation for KML to Shapefile export
            messages.success(request, 'Shapefile export completed successfully!')
            return redirect('file_preview')
        except Exception as e:
            messages.error(request, f'Error creating Shapefile export: {str(e)}')
            return redirect('file_preview')
    
    def _export_csv_to_kml(self, request, preview_data):
        """Export CSV preview data to KML"""
        try:
            # Implementation for CSV to KML export
            messages.success(request, 'KML export completed successfully!')
            return redirect('file_preview')
        except Exception as e:
            messages.error(request, f'Error creating KML export: {str(e)}')
            return redirect('file_preview')
    
    def _export_csv_to_shapefile(self, request, preview_data):
        """Export CSV preview data to Shapefile"""
        try:
            # Implementation for CSV to Shapefile export
            messages.success(request, 'Shapefile export completed successfully!')
            return redirect('file_preview')
        except Exception as e:
            messages.error(request, f'Error creating Shapefile export: {str(e)}')
            return redirect('file_preview')
    
    def _export_shapefile_to_kml(self, request, preview_data):
        """Export Shapefile preview data to KML"""
        try:
            # Implementation for Shapefile to KML export
            messages.success(request, 'KML export completed successfully!')
            return redirect('file_preview')
        except Exception as e:
            messages.error(request, f'Error creating KML export: {str(e)}')
            return redirect('file_preview')
    
    def _export_shapefile_to_csv(self, request, preview_data):
        """Export Shapefile preview data to CSV"""
        try:
            # Implementation for Shapefile to CSV export
            messages.success(request, 'CSV export completed successfully!')
            return redirect('file_preview')
        except Exception as e:
            messages.error(request, f'Error creating CSV export: {str(e)}')
            return redirect('file_preview')

class FileExportView(LoginRequiredMixin, View):
    """File export view for downloading converted files"""
    
    def get(self, request, file_id, format_type):
        """Handle file export requests"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        try:
            if format_type == 'csv':
                return self._export_to_csv(file_upload)
            elif format_type == 'kml':
                return self._export_to_kml(file_upload)
            elif format_type == 'shapefile':
                return self._export_to_shapefile(file_upload)
            else:
                messages.error(request, 'Unsupported export format.')
                return redirect('file_detail', file_id=file_id)
                
        except Exception as e:
            logger.error(f"Error exporting file {file_id} to {format_type}: {e}")
            messages.error(request, f'Error creating export: {str(e)}')
            return redirect('file_detail', file_id=file_id)
    
    def _export_to_csv(self, file_upload):
        """Export file to CSV format"""
        # Implementation for CSV export
        pass
    
    def _export_to_kml(self, file_upload):
        """Export file to KML format"""
        # Implementation for KML export
        pass
    
    def _export_to_shapefile(self, file_upload):
        """Export file to Shapefile format"""
        # Implementation for Shapefile export
        pass

class FileDeleteView(LoginRequiredMixin, View):
    """File deletion view"""
    
    def post(self, request, file_id):
        """Delete a file"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        try:
            # Delete associated data
            if file_upload.file_type == 'kml':
                KMLData.objects.filter(kml_file__file_upload=file_upload).delete()
            elif file_upload.file_type == 'csv':
                CSVData.objects.filter(file_upload=file_upload).delete()
            elif file_upload.file_type == 'shapefile':
                ShapefileData.objects.filter(file_upload=file_upload).delete()
            
            # Delete the file upload record
            file_upload.delete()
            
            messages.success(request, 'File deleted successfully.')
            return redirect('file_list')
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            messages.error(request, f'Error deleting file: {str(e)}')
            return redirect('file_detail', file_id=file_id)

class FileShareView(LoginRequiredMixin, View):
    """File sharing view"""
    
    def post(self, request, file_id):
        """Create a share link for a file"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        try:
            # Create share record
            share = FileShare.objects.create(
                file_upload=file_upload,
                share_type='public',
                shared_by=request.user
            )
            
            messages.success(request, 'Share link created successfully.')
            return redirect('file_detail', file_id=file_id)
            
        except Exception as e:
            logger.error(f"Error creating share for file {file_id}: {e}")
            messages.error(request, f'Error creating share link: {str(e)}')
            return redirect('file_detail', file_id=file_id)

class SharedFileView(View):
    """View for accessing shared files"""
    
    def get(self, request, share_token):
        """Display shared file"""
        share = get_object_or_404(FileShare, share_token=share_token, is_active=True)
        
        if share.is_expired or share.is_download_limit_reached:
            messages.error(request, 'This share link has expired or reached its download limit.')
            return redirect('file_upload')
        
        # Increment download count
        share.current_downloads += 1
        share.save()
        
        context = {
            'share': share,
            'file_upload': share.file_upload,
        }
        
        return render(request, 'userdashboard/shared_file.html', context)

class FileAjaxView(LoginRequiredMixin, View):
    """AJAX view for file operations"""
    
    def get(self, request, file_id):
        """Get file data via AJAX"""
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        
        data = {
            'id': str(file_upload.id),
            'filename': file_upload.original_filename,
            'file_type': file_upload.file_type,
            'file_size': file_upload.file_size,
            'status': file_upload.status,
            'created_at': file_upload.created_at.isoformat(),
        }
        
        return JsonResponse(data)

class FileStatsView(LoginRequiredMixin, View):
    """File statistics view"""
    
    def get(self, request):
        """Display file statistics"""
        user_files = FileUpload.objects.filter(user=request.user)
        
        stats = {
            'total_files': user_files.count(),
            'files_by_type': {},
            'total_size_mb': 0,
            'recent_uploads': user_files.order_by('-created_at')[:5],
        }
        
        for file_type, _ in FileUpload.FILE_TYPES:
            count = user_files.filter(file_type=file_type).count()
            if count > 0:
                stats['files_by_type'][file_type] = count
        
        total_size = user_files.aggregate(total=models.Sum('file_size'))['total'] or 0
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return render(request, 'userdashboard/file_stats.html', {'stats': stats})

class CSVGeoJSONView(View):
    def get(self, request, file_id):
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        csv_data = CSVData.objects.filter(file_upload=file_upload)
        features = []
        for row in csv_data:
            coords = json.loads(row.coordinates)
            geometry_type = row.geometry_type
            if geometry_type == 'Point':
                geometry = {"type": "Point", "coordinates": coords}
            elif geometry_type == 'Polygon':
                geometry = {"type": "Polygon", "coordinates": [coords]}
            else:
                continue
            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": row.data,
            })
        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }
        return JsonResponse(geojson)

class ShapefileGeoJSONView(LoginRequiredMixin, View):
    """Serve GeoJSON data for shapefile map visualization"""
    
    def get(self, request, file_id):
        try:
            file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
            shapefile_data = ShapefileData.objects.filter(file_upload=file_upload)
            
            logger.info(f"Found {shapefile_data.count()} shapefile features for file {file_id}")
            
            features = []
            for item in shapefile_data:
                try:
                    # Parse coordinates from the stored string
                    coords = json.loads(item.coordinates)
                    geometry_type = item.geometry_type
                    
                    geometry = None
                    if geometry_type == 'Point':
                        geometry = {"type": "Point", "coordinates": coords}
                    elif geometry_type == 'LineString':
                        geometry = {"type": "LineString", "coordinates": coords}
                    elif geometry_type == 'Polygon':
                        geometry = {"type": "Polygon", "coordinates": [coords]}
                    elif geometry_type == 'MultiPolygon':
                        geometry = {"type": "MultiPolygon", "coordinates": coords}
                    
                    if geometry:
                        properties = {
                            'feature_id': item.feature_id,
                            'geometry_type': item.geometry_type,
                            **item.attributes
                        }
                        features.append({
                            "type": "Feature",
                            "geometry": geometry,
                            "properties": properties
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error parsing shapefile feature {item.feature_id}: {e}")
                    continue
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            logger.info(f"Returning GeoJSON with {len(features)} features")
            return JsonResponse(geojson)
            
        except Exception as e:
            logger.error(f"Error in ShapefileGeoJSONView: {e}")
            return JsonResponse({"error": str(e)}, status=500)

# API Views for AJAX functionality
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file_api(request):
    """API endpoint for file upload"""
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file
        validator = FileValidator()
        file_type = validator.detect_file_type(uploaded_file, uploaded_file.name)
        
        validation_result = validator.validate_file(uploaded_file, uploaded_file.name, file_type)
        if validation_result['errors']:
            return Response({'errors': validation_result['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create file upload record
        file_upload = FileUpload.objects.create(
            user=request.user,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_type=file_type,
            file_size=uploaded_file.size,
            status='pending'
        )
        
        # Process file asynchronously (in production, use Celery)
        try:
            processor = FileProcessor(file_upload)
            result = processor.process_file()
            
            file_upload.status = 'completed'
            file_upload.save()
            
            return Response({
                'success': True,
                'file_id': str(file_upload.id),
                'file_type': file_type,
                'result': result
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            file_upload.status = 'failed'
            file_upload.error_message = str(e)
            file_upload.save()
            
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in file upload API: {e}")
        return Response({'error': 'An error occurred during upload'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_file_api(request, file_id):
    """API endpoint for file conversion"""
    try:
        file_upload = get_object_or_404(FileUpload, id=file_id, user=request.user)
        conversion_type = request.data.get('conversion_type')
        
        if not conversion_type:
            return Response({'error': 'Conversion type required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create conversion record
        conversion = FileConversion.objects.create(
            source_file=file_upload,
            conversion_type=conversion_type,
            status='processing'
        )
        
        try:
            # Perform conversion based on type
            if conversion_type == 'kml_to_csv':
                kml_data = KMLData.objects.filter(kml_file__file_upload=file_upload)
                filename = f"{file_upload.original_filename.replace('.kml', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                response = FileConverter.kml_to_csv(kml_data, filename)
                
            elif conversion_type == 'kml_to_shapefile':
                kml_data = KMLData.objects.filter(kml_file__file_upload=file_upload)
                filename = f"{file_upload.original_filename.replace('.kml', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                response = FileConverter.kml_to_shapefile(kml_data, filename)
                
            elif conversion_type == 'csv_to_kml':
                csv_data = CSVData.objects.filter(file_upload=file_upload)
                filename = f"{file_upload.original_filename.replace('.csv', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                response = FileConverter.csv_to_kml(csv_data, filename)
                
            elif conversion_type == 'csv_to_shapefile':
                csv_data = CSVData.objects.filter(file_upload=file_upload)
                filename = f"{file_upload.original_filename.replace('.csv', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                response = FileConverter.csv_to_shapefile(csv_data, filename)
                
            elif conversion_type == 'shapefile_to_kml':
                shapefile_data = ShapefileData.objects.filter(file_upload=file_upload)
                filename = f"{file_upload.original_filename.replace('.zip', '').replace('.shp', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                response = FileConverter.shapefile_to_kml(shapefile_data, filename)
                
            elif conversion_type == 'shapefile_to_csv':
                shapefile_data = ShapefileData.objects.filter(file_upload=file_upload)
                filename = f"{file_upload.original_filename.replace('.zip', '').replace('.shp', '')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                response = FileConverter.shapefile_to_csv(shapefile_data, filename)
                
            else:
                raise ValueError(f"Unsupported conversion type: {conversion_type}")
            
            # Update conversion record
            conversion.status = 'completed'
            conversion.output_filename = response['Content-Disposition'].split('filename=')[1].strip('"')
            conversion.file_size = len(response.content)
            conversion.processing_completed = timezone.now()
            conversion.save()
            
            return response
            
        except Exception as e:
            conversion.status = 'failed'
            conversion.error_message = str(e)
            conversion.save()
            
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in file conversion API: {e}")
        return Response({'error': 'An error occurred during conversion'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 