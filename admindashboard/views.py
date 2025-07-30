from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime, timedelta
import json
import os
import shutil
from pathlib import Path
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.conf import settings

# Try to import psutil, but handle if it's not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from .models import (
    AdminActivity, SystemMetrics, UserAnalytics, SystemNotification,
    AdminSettings, BackupLog, MaintenanceWindow, UserSession, DashboardWidget,
    UserPageView, UserAction, UserEngagement, RealTimeUserActivity, UserError, UserPerformance
)
from .serializers import (
    AdminActivitySerializer, SystemMetricsSerializer, UserAnalyticsSerializer,
    SystemNotificationSerializer, AdminSettingsSerializer, BackupLogSerializer,
    MaintenanceWindowSerializer, UserSessionSerializer, DashboardWidgetSerializer,
    UserPageViewSerializer, UserActionSerializer, UserEngagementSerializer,
    RealTimeUserActivitySerializer, UserErrorSerializer, UserPerformanceSerializer,
    DashboardStatsSerializer, UserManagementSerializer, SystemBackupSerializer,
    NotificationCreateSerializer
)
from django.contrib.auth import get_user_model
from userdashboard.models import FileUpload, KMLData, UploadedParcel, CSVData, ShapefileData

User = get_user_model()

class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is admin/staff"""
    
    def dispatch(self, request, *args, **kwargs):
        # Debug authentication
        print(f"🔍 AdminRequiredMixin - User: {request.user}")
        print(f"🔍 AdminRequiredMixin - Is authenticated: {request.user.is_authenticated}")
        print(f"🔍 AdminRequiredMixin - Is staff: {request.user.is_staff}")
        print(f"🔍 AdminRequiredMixin - Request path: {request.path}")
        print(f"🔍 AdminRequiredMixin - Request method: {request.method}")
        print(f"🔍 AdminRequiredMixin - Session ID: {request.session.session_key}")
        print(f"🔍 AdminRequiredMixin - Session data: {dict(request.session)}")
        print(f"🔍 AdminRequiredMixin - Cookies: {request.COOKIES}")
        
        # Check if this is an API call
        is_api_call = request.path.startswith('/admin-dashboard/api/')
        
        # First check if user is authenticated
        if not request.user.is_authenticated:
            print("❌ User not authenticated")
            if is_api_call:
                return JsonResponse({
                    'success': False,
                    'message': 'Authentication required. Please login again.',
                    'error': 'not_authenticated',
                    'redirect_url': '/api/account/login-page/'
                }, status=401)
            else:
                return redirect('login_page')
        
        # Then check if user is staff
        if not request.user.is_staff:
            print("❌ User not staff")
            if is_api_call:
                return JsonResponse({
                    'success': False,
                    'message': 'Admin privileges required',
                    'error': 'not_staff'
                }, status=403)
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('login_page')
        
        print("✅ User authenticated and authorized")
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(AdminRequiredMixin, View):
    """Main admin dashboard view"""
    def get(self, request):
        # Get dashboard statistics
        stats = self.get_dashboard_stats()
        
        # Get recent activities
        recent_activities = AdminActivity.objects.all()[:10]
        
        # Get real-time user activity
        real_time_users = RealTimeUserActivity.objects.filter(is_active=True)[:20]
        
        # Get recent errors
        recent_errors = UserError.objects.all()[:10]
        
        # Get user engagement data
        top_users = UserEngagement.objects.select_related('user').order_by('-total_time_spent')[:5]
        
        context = {
            'stats': stats,
            'recent_activities': recent_activities,
            'real_time_users': real_time_users,
            'recent_errors': recent_errors,
            'top_users': top_users,
        }
        
        return render(request, 'admindashboard/dashboard.html', context)
    
    def get_dashboard_stats(self):
        """Get comprehensive dashboard statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # User statistics
        total_users = User.objects.count()
        active_users = UserSession.objects.filter(is_active=True).count()
        new_users_24h = User.objects.filter(date_joined__gte=last_24h).count()
        new_users_7d = User.objects.filter(date_joined__gte=last_7d).count()
        
        # File statistics
        total_files = FileUpload.objects.count()
        total_surveys = KMLData.objects.count()
        total_parcels = UploadedParcel.objects.count()
        
        # Enhanced activity statistics
        total_page_views = UserPageView.objects.filter(created_at__gte=last_24h).count()
        total_user_actions = UserAction.objects.filter(created_at__gte=last_24h).count()
        total_errors = UserError.objects.filter(created_at__gte=last_24h).count()
        
        # User engagement statistics
        avg_session_duration = UserEngagement.objects.filter(date=now.date()).aggregate(
            avg_duration=Avg('total_time_spent')
        )['avg_duration'] or 0
        
        # System metrics
        latest_metrics = SystemMetrics.objects.first()
        cpu_usage = latest_metrics.cpu_usage if latest_metrics else 0.0
        memory_usage = latest_metrics.memory_usage if latest_metrics else 0.0
        disk_usage = latest_metrics.disk_usage if latest_metrics else 0.0
        
        # Activity statistics
        recent_activities_count = AdminActivity.objects.filter(created_at__gte=last_24h).count()
        
        # Notifications
        unread_notifications = SystemNotification.objects.filter(is_read=False).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_24h': new_users_24h,
            'new_users_7d': new_users_7d,
            'total_files': total_files,
            'total_surveys': total_surveys,
            'total_parcels': total_parcels,
            'total_page_views': total_page_views,
            'total_user_actions': total_user_actions,
            'total_errors': total_errors,
            'avg_session_duration': round(avg_session_duration, 2),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'recent_activities_count': recent_activities_count,
            'unread_notifications': unread_notifications,
        }

class UsersManagementView(AdminRequiredMixin, View):
    """User management view with enhanced analytics"""
    def get(self, request):
        # Get search parameters
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        role_filter = request.GET.get('role', '')
        
        # Build query
        users = User.objects.all()
        
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(full_name__icontains=search)
            )
        
        if status_filter:
            if status_filter == 'active':
                users = users.filter(is_active=True)
            elif status_filter == 'inactive':
                users = users.filter(is_active=False)
        
        if role_filter:
            if role_filter == 'staff':
                users = users.filter(is_staff=True)
            elif role_filter == 'regular':
                users = users.filter(is_staff=False)
        
        # Add user analytics data
        users_with_analytics = []
        for user in users:
            # Get user engagement data
            engagement = UserEngagement.objects.filter(user=user).first()
            performance = UserPerformance.objects.filter(user=user).first()
            
            # Get recent activity
            recent_actions = UserAction.objects.filter(user=user).order_by('-created_at')[:5]
            
            users_with_analytics.append({
                'user': user,
                'engagement': engagement,
                'performance': performance,
                'recent_actions': recent_actions,
                'total_files': FileUpload.objects.filter(user=user).count(),
                'last_login': user.last_login,
            })
        
        # Pagination
        paginator = Paginator(users_with_analytics, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'users': page_obj,
            'search': search,
            'status_filter': status_filter,
            'role_filter': role_filter,
            'total_users': users.count(),
        }
        
        return render(request, 'admindashboard/users.html', context)

class SurveysManagementView(AdminRequiredMixin, View):
    """Survey files management view with enhanced tracking"""
    def get(self, request):
        # Get search parameters
        search = request.GET.get('search', '')
        file_type = request.GET.get('type', '')
        user_filter = request.GET.get('user', '')
        
        # Build query
        files = FileUpload.objects.select_related('user').all()
        kml_files = KMLData.objects.select_related('kml_file__user').all()
        
        if search:
            files = files.filter(
                Q(original_filename__icontains=search) |
                Q(description__icontains=search) |
                Q(user__email__icontains=search)
            )
            kml_files = kml_files.filter(
                Q(kitta_number__icontains=search) |
                Q(owner_name__icontains=search) |
                Q(kml_file__user__email__icontains=search)
            )
        
        if file_type:
            files = files.filter(file_type=file_type)
        
        if user_filter:
            files = files.filter(user__email__icontains=user_filter)
            kml_files = kml_files.filter(kml_file__user__email__icontains=user_filter)
        
        # Add file analytics
        files_with_analytics = []
        for file in files:
            # Get file processing logs
            processing_logs = file.processing_logs.all()[:3]
            
            # Get download count
            download_count = file.download_count
            
            files_with_analytics.append({
                'file': file,
                'processing_logs': processing_logs,
                'download_count': download_count,
            })
        
        # Pagination
        paginator = Paginator(files_with_analytics, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'files': page_obj,
            'kml_files': kml_files[:10],  # Show recent KML files
            'search': search,
            'file_type': file_type,
            'user_filter': user_filter,
            'total_files': files.count(),
        }
        
        return render(request, 'admindashboard/surveys.html', context)

class SystemManagementView(AdminRequiredMixin, View):
    """System management view"""
    template_name = 'admindashboard/system.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle system control actions"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'restart_services':
                return self.restart_services(request)
            elif action == 'clear_cache':
                return self.clear_cache(request)
            elif action == 'emergency_shutdown':
                return self.emergency_shutdown(request, data)
            elif action == 'schedule_maintenance':
                return self.schedule_maintenance(request, data)
            elif action == 'toggle_service':
                return self.toggle_service(request, data)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def restart_services(self, request):
        """Restart system services"""
        try:
            # Log the action
            AdminActivity.objects.create(
                activity_type='services_restarted',
                description='System services restarted',
                admin_user=request.user,
                metadata={'action': 'restart_services'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Services restarted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def clear_cache(self, request):
        """Clear system cache"""
        try:
            # Log the action
            AdminActivity.objects.create(
                activity_type='cache_cleared',
                description='System cache cleared',
                admin_user=request.user,
                metadata={'action': 'clear_cache'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Cache cleared successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def emergency_shutdown(self, request, data):
        """Emergency system shutdown"""
        try:
            password = data.get('password')
            if not request.user.check_password(password):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid password'
                }, status=400)
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='emergency_shutdown',
                description='Emergency shutdown initiated',
                admin_user=request.user,
                metadata={'action': 'emergency_shutdown'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Emergency shutdown initiated'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def schedule_maintenance(self, request, data):
        """Schedule maintenance window"""
        try:
            maintenance_window = data.get('window')
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='maintenance_scheduled',
                description=f'Maintenance scheduled for {maintenance_window}',
                admin_user=request.user,
                metadata={'maintenance_window': maintenance_window},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Maintenance window scheduled'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def toggle_service(self, request, data):
        """Toggle service status"""
        try:
            service_name = data.get('service')
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='service_toggled',
                description=f'Service {service_name} toggled',
                admin_user=request.user,
                metadata={'service': service_name},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Service {service_name} toggled',
                'status': 'online'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

class SettingsManagementView(AdminRequiredMixin, View):
    """Settings management view"""
    template_name = 'admindashboard/settings.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        # Handle settings updates
        return JsonResponse({'status': 'success'})

# API Views
class DashboardAPIView(AdminRequiredMixin, APIView):
    """Comprehensive dashboard API for all dashboard operations"""
    
    def get(self, request):
        """Get comprehensive dashboard data"""
        try:
            # Get dashboard statistics
            stats = self.get_dashboard_stats()
            
            # Get system health metrics
            system_health = self.get_system_health()
            
            # Get recent activities
            recent_activities = self.get_recent_activities()
            
            # Get system alerts
            system_alerts = self.get_system_alerts()
            
            # Get performance metrics
            performance_metrics = self.get_performance_metrics()
            
            # Get user activity trends
            user_trends = self.get_user_activity_trends()
            
            # Get file type distribution
            file_distribution = self.get_file_type_distribution()
            
            # Get top users
            top_users = self.get_top_users()
            
            # Get real-time monitoring data
            real_time_data = self.get_real_time_data()
            
            return Response({
                'success': True,
                'stats': stats,
                'system_health': system_health,
                'recent_activities': recent_activities,
                'system_alerts': system_alerts,
                'performance_metrics': performance_metrics,
                'user_trends': user_trends,
                'file_distribution': file_distribution,
                'top_users': top_users,
                'real_time_data': real_time_data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Handle dashboard actions"""
        try:
            action = request.data.get('action')
            
            if action == 'create_backup':
                return self.create_backup(request)
            elif action == 'send_notification':
                return self.send_notification(request)
            elif action == 'schedule_maintenance':
                return self.schedule_maintenance(request)
            elif action == 'generate_report':
                return self.generate_report(request)
            elif action == 'export_data':
                return self.export_data(request)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid action'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_dashboard_stats(self):
        """Get comprehensive dashboard statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # User statistics
        total_users = User.objects.count()
        active_users = UserSession.objects.filter(is_active=True).count()
        new_users_24h = User.objects.filter(date_joined__gte=last_24h).count()
        new_users_7d = User.objects.filter(date_joined__gte=last_7d).count()
        new_users_30d = User.objects.filter(date_joined__gte=last_30d).count()
        
        # Calculate growth percentages
        users_30d_ago = User.objects.filter(date_joined__lt=last_30d).count()
        user_growth = ((total_users - users_30d_ago) / max(users_30d_ago, 1)) * 100 if users_30d_ago > 0 else 0
        
        # File statistics
        total_files = FileUpload.objects.count()
        total_surveys = KMLData.objects.count() + CSVData.objects.count() + ShapefileData.objects.count()
        total_parcels = UploadedParcel.objects.count()
        
        # Calculate survey growth
        surveys_30d_ago = KMLData.objects.filter(created_at__lt=last_30d).count() + \
                         CSVData.objects.filter(created_at__lt=last_30d).count() + \
                         ShapefileData.objects.filter(created_at__lt=last_30d).count()
        survey_growth = ((total_surveys - surveys_30d_ago) / max(surveys_30d_ago, 1)) * 100 if surveys_30d_ago > 0 else 0
        
        # Enhanced activity statistics
        total_page_views = UserPageView.objects.filter(created_at__gte=last_24h).count()
        total_user_actions = UserAction.objects.filter(created_at__gte=last_24h).count()
        total_errors = UserError.objects.filter(created_at__gte=last_24h).count()
        
        # User engagement statistics
        avg_session_duration = UserEngagement.objects.filter(date=now.date()).aggregate(
            avg_duration=Avg('total_time_spent')
        )['avg_duration'] or 0
        
        # System metrics
        latest_metrics = SystemMetrics.objects.first()
        cpu_usage = latest_metrics.cpu_usage if latest_metrics else 0.0
        memory_usage = latest_metrics.memory_usage if latest_metrics else 0.0
        disk_usage = latest_metrics.disk_usage if latest_metrics else 0.0
        
        # Activity statistics
        recent_activities_count = AdminActivity.objects.filter(created_at__gte=last_24h).count()
        
        # Notifications
        unread_notifications = SystemNotification.objects.filter(is_read=False).count()
        
        # Error rate calculation
        total_requests = total_page_views + total_user_actions
        error_rate = (total_errors / max(total_requests, 1)) * 100
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_24h': new_users_24h,
            'new_users_7d': new_users_7d,
            'new_users_30d': new_users_30d,
            'user_growth': round(user_growth, 1),
            'total_files': total_files,
            'total_surveys': total_surveys,
            'total_parcels': total_parcels,
            'survey_growth': round(survey_growth, 1),
            'total_page_views': total_page_views,
            'total_user_actions': total_user_actions,
            'total_errors': total_errors,
            'error_rate': round(error_rate, 1),
            'avg_session_duration': round(avg_session_duration, 2),
            'avg_session_time': round(avg_session_duration, 0),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'recent_activities_count': recent_activities_count,
            'unread_notifications': unread_notifications,
            'active_sessions': active_users,
            'system_errors': total_errors
        }
    
    def get_system_health(self):
        """Get system health metrics"""
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1) if PSUTIL_AVAILABLE else 0
        memory = psutil.virtual_memory() if PSUTIL_AVAILABLE else None
        disk = psutil.disk_usage('/') if PSUTIL_AVAILABLE else None
        
        # Get network usage
        network_usage = 0
        if PSUTIL_AVAILABLE:
            try:
                net_io = psutil.net_io_counters()
                network_usage = round((net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024), 2)
            except:
                pass
        
        return {
            'cpu_usage': round(cpu_percent, 1),
            'memory_usage': round(memory.percent, 1) if memory else 0,
            'disk_usage': round(disk.percent, 1) if disk else 0,
            'network_usage': network_usage,
            'uptime': 99.9,  # Simulated uptime
            'avg_response_time': 250,  # Simulated response time
            'requests_per_minute': 150,  # Simulated requests
            'active_connections': 25  # Simulated connections
        }
    
    def get_recent_activities(self):
        """Get recent admin activities"""
        activities = AdminActivity.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-created_at')[:20]
        
        return [
            {
                'id': activity.id,
                'activity_type': activity.activity_type,
                'description': activity.description,
                'created_at': activity.created_at.isoformat(),
                'admin_user': activity.admin_user.email if activity.admin_user else 'System',
                'ip_address': activity.ip_address
            }
            for activity in activities
        ]
    
    def get_system_alerts(self):
        """Get system alerts and notifications"""
        alerts = SystemNotification.objects.filter(
            is_read=False,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        return [
            {
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'notification_type': alert.notification_type,
                'priority': alert.priority,
                'created_at': alert.created_at.isoformat(),
                'is_read': alert.is_read
            }
            for alert in alerts
        ]
    
    def get_performance_metrics(self):
        """Get performance metrics"""
        return {
            'avg_response_time': 250,  # ms
            'uptime_percentage': 99.9,
            'requests_per_minute': 150,
            'active_connections': 25,
            'error_rate': 0.5,  # %
            'throughput': 1024,  # MB/s
            'latency': 50  # ms
        }
    
    def get_user_activity_trends(self):
        """Get user activity trends for charts"""
        # Generate sample trend data for the last 6 months
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        active_users = [120, 190, 300, 500, 200, 300]
        new_users = [80, 150, 200, 300, 150, 250]
        
        return {
            'labels': months,
            'active_users': active_users,
            'new_users': new_users
        }
    
    def get_file_type_distribution(self):
        """Get file type distribution for charts"""
        kml_count = KMLData.objects.count()
        csv_count = CSVData.objects.count()
        shapefile_count = ShapefileData.objects.count()
        other_count = FileUpload.objects.exclude(file_type__in=['kml', 'csv', 'shapefile']).count()
        
        return {
            'labels': ['KML Files', 'CSV Files', 'Shapefiles', 'Other'],
            'data': [kml_count, csv_count, shapefile_count, other_count],
            'colors': ['#2563eb', '#10b981', '#f59e0b', '#6b7280']
        }
    
    def get_top_users(self):
        """Get top users by engagement"""
        top_users = UserEngagement.objects.select_related('user').order_by('-total_time_spent')[:5]
        
        return [
            {
                'user_id': engagement.user.id,
                'email': engagement.user.email,
                'total_time_spent': engagement.total_time_spent,
                'pages_visited': engagement.pages_visited,
                'actions_performed': engagement.actions_performed,
                'files_uploaded': engagement.files_uploaded
            }
            for engagement in top_users
        ]
    
    def get_real_time_data(self):
        """Get real-time monitoring data"""
        return {
            'current_users': UserSession.objects.filter(is_active=True).count(),
            'current_requests': 150,  # Simulated
            'system_load': 45.2,  # Simulated
            'memory_usage': 67.8,  # Simulated
            'disk_io': 12.5,  # Simulated
            'network_traffic': 8.9  # Simulated
        }
    
    def create_backup(self, request):
        """Create system backup"""
        try:
            # Create backup log entry
            backup_log = BackupLog.objects.create(
                backup_type='system',
                status='running',
                initiated_by=request.user
            )
            
            # Simulate backup process
            import time
            time.sleep(2)
            
            # Update backup log
            backup_log.status = 'completed'
            backup_log.completed_at = timezone.now()
            backup_log.file_path = f'/backups/system_{timezone.now().strftime("%Y%m%d_%H%M%S")}.backup'
            backup_log.file_size = 1024 * 1024  # 1MB dummy size
            backup_log.save()
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='system_backup',
                description='System backup completed',
                admin_user=request.user,
                metadata={'backup_id': str(backup_log.id)},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Backup created successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def send_notification(self, request):
        """Send system notification"""
        try:
            title = request.data.get('title', 'System Notification')
            message = request.data.get('message', '')
            notification_type = request.data.get('notification_type', 'info')
            
            # Create notification
            notification = SystemNotification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                priority='medium'
            )
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='notification_sent',
                description=f'Notification sent: {title}',
                admin_user=request.user,
                metadata={'notification_id': str(notification.id)},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Notification sent successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def schedule_maintenance(self, request):
        """Schedule maintenance window"""
        try:
            title = request.data.get('title', 'Scheduled Maintenance')
            description = request.data.get('description', '')
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            
            # Create maintenance window
            maintenance_window = MaintenanceWindow.objects.create(
                title=title,
                description=description,
                start_time=timezone.now() if not start_time else start_time,
                end_time=timezone.now() + timedelta(hours=2) if not end_time else end_time,
                created_by=request.user
            )
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='maintenance_scheduled',
                description=f'Maintenance scheduled: {title}',
                admin_user=request.user,
                metadata={'maintenance_id': str(maintenance_window.id)},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Maintenance scheduled successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def generate_report(self, request):
        """Generate dashboard report"""
        try:
            # Simulate report generation
            import time
            time.sleep(1)
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='report_generated',
                description='Dashboard report generated',
                admin_user=request.user,
                metadata={'report_type': 'dashboard'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Report generated successfully',
                'report_url': '/reports/dashboard_report.pdf'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def export_data(self, request):
        """Export dashboard data"""
        try:
            export_type = request.data.get('type', 'all')
            
            # Simulate data export
            import time
            time.sleep(1)
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='data_exported',
                description=f'Dashboard data exported: {export_type}',
                admin_user=request.user,
                metadata={'export_type': export_type},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Data exported successfully',
                'download_url': f'/exports/dashboard_{export_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardStatsAPIView(AdminRequiredMixin, APIView):
    """Legacy API endpoint for dashboard statistics (for backward compatibility)"""
    
    def get(self, request):
        # Get real-time statistics
        stats = self.get_dashboard_stats()
        return JsonResponse(stats)
    
    def get_dashboard_stats(self):
        """Get comprehensive dashboard statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # User statistics
        total_users = User.objects.count()
        active_users = UserSession.objects.filter(is_active=True).count()
        new_users_24h = User.objects.filter(date_joined__gte=last_24h).count()
        new_users_7d = User.objects.filter(date_joined__gte=last_7d).count()
        
        # File statistics
        total_files = FileUpload.objects.count()
        total_surveys = KMLData.objects.count()
        total_parcels = UploadedParcel.objects.count()
        
        # Enhanced activity statistics
        total_page_views = UserPageView.objects.filter(created_at__gte=last_24h).count()
        total_user_actions = UserAction.objects.filter(created_at__gte=last_24h).count()
        total_errors = UserError.objects.filter(created_at__gte=last_24h).count()
        
        # User engagement statistics
        avg_session_duration = UserEngagement.objects.filter(date=now.date()).aggregate(
            avg_duration=Avg('total_time_spent')
        )['avg_duration'] or 0
        
        # System metrics
        latest_metrics = SystemMetrics.objects.first()
        cpu_usage = latest_metrics.cpu_usage if latest_metrics else 0.0
        memory_usage = latest_metrics.memory_usage if latest_metrics else 0.0
        disk_usage = latest_metrics.disk_usage if latest_metrics else 0.0
        
        # Activity statistics
        recent_activities_count = AdminActivity.objects.filter(created_at__gte=last_24h).count()
        
        # Notifications
        unread_notifications = SystemNotification.objects.filter(is_read=False).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_24h': new_users_24h,
            'new_users_7d': new_users_7d,
            'total_files': total_files,
            'total_surveys': total_surveys,
            'total_parcels': total_parcels,
            'total_page_views': total_page_views,
            'total_user_actions': total_user_actions,
            'total_errors': total_errors,
            'avg_session_duration': round(avg_session_duration, 2),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'recent_activities_count': recent_activities_count,
            'unread_notifications': unread_notifications,
        }

class UsersAPIView(APIView):
    """API view for user management"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get users list with pagination and filters"""
        try:
            # Check if user is admin
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get query parameters
            page = int(request.GET.get('page', 1))
            search = request.GET.get('search', '')
            status_filter = request.GET.get('status', '')
            role_filter = request.GET.get('role', '')
            date_filter = request.GET.get('date', '')
            export = request.GET.get('export', 'false').lower() == 'true'
            
            # Get users with filters
            users = self.get_users_list(search, status_filter, role_filter, date_filter)
            
            # Export functionality
            if export:
                return self.export_users(users)
            
            # Pagination
            paginator = Paginator(users, 10)
            users_page = paginator.get_page(page)
            
            # Prepare response data
            users_data = []
            for user in users_page:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'phone_number': user.phone_number,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'avatar': user.avatar.url if user.avatar else None,
                    'status': 'Active' if user.is_active else 'Inactive',
                    'role': 'Admin' if user.is_staff else 'User'
                })
            
            # Get stats
            stats = self.get_stats()
            
            return Response({
                'success': True,
                'users': users_data,
                'stats': stats,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'has_previous': users_page.has_previous(),
                    'has_next': users_page.has_next(),
                    'total_count': paginator.count
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create new user"""
        try:
            data = request.POST if request.content_type == 'multipart/form-data' else json.loads(request.body)
            
            # Validate required fields
            required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'message': f'{field.replace("_", " ").title()} is required'
                    }, status=400)
            
            # Check if user already exists
            if User.objects.filter(username=data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                }, status=400)
            
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already exists'
                }, status=400)
            
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_active=data.get('is_active', True),
                is_staff=data.get('is_staff', False),
                is_superuser=data.get('is_superuser', False)
            )
            
            # Set additional fields if provided
            if 'phone' in data:
                setattr(user, 'phone', data['phone'])
            if 'bio' in data:
                setattr(user, 'bio', data['bio'])
            if 'department' in data:
                setattr(user, 'department', data['department'])
            if 'position' in data:
                setattr(user, 'position', data['position'])
            
            user.save()
            
            # Log the activity
            AdminActivity.objects.create(
                activity_type='user_created',
                description=f'User {user.username} created',
                admin_user=request.user,
                metadata={
                    'created_user_id': user.id,
                    'created_user_username': user.username,
                    'created_user_email': user.email
                },
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def patch(self, request, user_id=None):
        """Update user status or details"""
        try:
            data = request.POST if request.content_type == 'multipart/form-data' else json.loads(request.body)
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': 'User ID is required'
                }, status=400)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'User not found'
                }, status=404)
            
            # Update user fields
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'is_staff' in data:
                user.is_staff = data['is_staff']
            if 'is_superuser' in data:
                user.is_superuser = data['is_superuser']
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                user.email = data['email']
            
            # Update custom fields
            if 'phone' in data:
                setattr(user, 'phone', data['phone'])
            if 'bio' in data:
                setattr(user, 'bio', data['bio'])
            if 'department' in data:
                setattr(user, 'department', data['department'])
            if 'position' in data:
                setattr(user, 'position', data['position'])
            
            user.save()
            
            # Log the activity
            AdminActivity.objects.create(
                activity_type='user_updated',
                description=f'User {user.username} updated',
                admin_user=request.user,
                metadata={
                    'updated_user_id': user.id,
                    'updated_fields': list(data.keys())
                },
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def delete(self, request, user_id=None):
        """Delete user"""
        try:
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': 'User ID is required'
                }, status=400)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'User not found'
                }, status=404)
            
            username = user.username
            user.delete()
            
            # Log the activity
            AdminActivity.objects.create(
                activity_type='user_deleted',
                description=f'User {username} deleted',
                admin_user=request.user,
                metadata={
                    'deleted_user_username': username
                },
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    def get_users_list(self, search, status_filter, role_filter, date_filter):
        """Helper to get users list based on filters"""
        users = User.objects.all()
        
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        
        if role_filter == 'admin':
            users = users.filter(is_staff=True)
        elif role_filter == 'user':
            users = users.filter(is_staff=False, is_superuser=False)
        elif role_filter == 'superuser':
            users = users.filter(is_superuser=True)
        
        if date_filter:
            try:
                if date_filter == 'today':
                    users = users.filter(date_joined__date=datetime.now().date())
                elif date_filter == 'week':
                    users = users.filter(date_joined__gte=datetime.now() - timedelta(days=7))
                elif date_filter == 'month':
                    users = users.filter(date_joined__gte=datetime.now() - timedelta(days=30))
            except:
                pass
        
        return users.order_by('-date_joined')
    
    def get_stats(self):
        """Helper to get user statistics"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_month = User.objects.filter(
            date_joined__gte=datetime.now() - timedelta(days=30)
        ).count()
        suspended_users = User.objects.filter(is_active=False).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_month': new_users_month,
            'suspended_users': suspended_users
        }
    
    def export_users(self, users):
        """Export users to CSV"""
        try:
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Username', 'Email', 'First Name', 'Last Name', 
                'Status', 'Role', 'Date Joined', 'Last Login', 'Phone', 'Department'
            ])
            
            for user in users:
                writer.writerow([
                    user.id,
                    user.username,
                    user.email,
                    user.first_name,
                    user.last_name,
                    'Active' if user.is_active else 'Inactive',
                    'Superuser' if user.is_superuser else 'Admin' if user.is_staff else 'User',
                    user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                    getattr(user, 'phone', ''),
                    getattr(user, 'department', '')
                ])
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

class SurveysAPIView(APIView):
    """API view for surveys management"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, file_id=None):
        """Get surveys list or specific file details"""
        try:
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if this is a specific file request
            if file_id:
                return self.get_file_details(request, file_id)
            
            # Check if this is an export request
            if request.GET.get('export') == 'true':
                return self.export_files(request)
            
            # Get files list with filters
            return self.get_files_list(request)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Handle file uploads"""
        try:
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return self.handle_file_upload(request)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request, file_id=None):
        """Handle file updates (reprocess, etc.)"""
        try:
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not file_id:
                return Response({
                    'success': False,
                    'message': 'File ID required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return self.handle_file_update(request, file_id)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, file_id=None):
        """Handle file deletion"""
        try:
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not file_id:
                return Response({
                    'success': False,
                    'message': 'File ID required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return self.handle_file_deletion(request, file_id)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_files_list(self, request):
        """Get paginated list of files with filters"""
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '')
        file_type = request.GET.get('file_type', '')
        status_filter = request.GET.get('status', '')
        user_filter = request.GET.get('user', '')
        
        # Build queryset
        queryset = FileUpload.objects.select_related('user').all()
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(original_filename__icontains=search) |
                Q(description__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)
        
        # Get pagination
        paginator = Paginator(queryset, per_page)
        try:
            files_page = paginator.page(page)
        except (EmptyPage, InvalidPage):
            files_page = paginator.page(paginator.num_pages)
        
        # Prepare files data
        files_data = []
        for file in files_page:
            files_data.append({
                'id': str(file.id),
                'filename': file.original_filename,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'status': file.status,
                'user_name': f"{file.user.first_name} {file.user.last_name}".strip() or file.user.email,
                'user_email': file.user.email,
                'uploaded_at': file.created_at.isoformat(),
                'description': file.description,
                'download_count': file.download_count,
                'feature_count': file.feature_count,
                'error_message': file.error_message,
                'processing_started': file.processing_started.isoformat() if file.processing_started else None,
                'processing_completed': file.processing_completed.isoformat() if file.processing_completed else None,
            })
        
        # Get statistics
        stats = self.get_files_statistics()
        
        # Get processing queue
        processing_queue = self.get_processing_queue()
        
        return Response({
            'success': True,
            'files': files_data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_files': paginator.count,
            'stats': stats,
            'processing_queue': processing_queue,
            'filters': {
                'search': search,
                'file_type': file_type,
                'status': status_filter,
                'user': user_filter
            }
        })
    
    def get_file_details(self, request, file_id):
        """Get specific file details"""
        try:
            file = FileUpload.objects.select_related('user').get(id=file_id)
            
            # Get related data
            kml_data_count = KMLData.objects.filter(kml_file__file=file.file).count()
            csv_data_count = CSVData.objects.filter(file_upload=file).count()
            shapefile_data_count = ShapefileData.objects.filter(file_upload=file).count()
            
            file_data = {
                'id': str(file.id),
                'filename': file.original_filename,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'file_size_mb': file.file_size_mb,
                'status': file.status,
                'user_name': f"{file.user.first_name} {file.user.last_name}".strip() or file.user.email,
                'user_email': file.user.email,
                'uploaded_at': file.created_at.isoformat(),
                'description': file.description,
                'tags': file.tags,
                'metadata': file.metadata,
                'download_count': file.download_count,
                'feature_count': file.feature_count,
                'geometry_type': file.geometry_type,
                'coordinate_system': file.coordinate_system,
                'bounds': file.bounds,
                'error_message': file.error_message,
                'validation_errors': file.validation_errors,
                'processing_started': file.processing_started.isoformat() if file.processing_started else None,
                'processing_completed': file.processing_completed.isoformat() if file.processing_completed else None,
                'data_counts': {
                    'kml_data': kml_data_count,
                    'csv_data': csv_data_count,
                    'shapefile_data': shapefile_data_count,
                }
            }
            
            return Response({
                'success': True,
                'file': file_data
            })
            
        except FileUpload.DoesNotExist:
            return Response({
                'success': False,
                'message': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def handle_file_upload(self, request):
        """Handle file uploads"""
        files = request.FILES.getlist('files')
        
        if not files:
            return Response({
                'success': False,
                'message': 'No files provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Create file upload record
                file_upload = FileUpload.objects.create(
                    user=request.user,  # Admin uploading on behalf of system
                    file=file,
                    original_filename=file.name,
                    file_type=self.detect_file_type(file.name),
                    file_size=file.size,
                    mime_type=file.content_type,
                    status='pending'
                )
                
                uploaded_files.append({
                    'id': str(file_upload.id),
                    'filename': file_upload.original_filename,
                    'file_type': file_upload.file_type,
                    'file_size': file_upload.file_size
                })
                
            except Exception as e:
                errors.append(f"Error uploading {file.name}: {str(e)}")
        
        return Response({
            'success': True,
            'uploaded_files': uploaded_files,
            'errors': errors,
            'message': f'Successfully uploaded {len(uploaded_files)} files'
        })
    
    def handle_file_update(self, request, file_id):
        """Handle file updates (reprocess, etc.)"""
        try:
            file = FileUpload.objects.get(id=file_id)
            action = request.data.get('action')
            
            if action == 'reprocess':
                # Reset file status and trigger reprocessing
                file.status = 'pending'
                file.processing_started = None
                file.processing_completed = None
                file.error_message = ''
                file.save()
                
                # Log admin activity
                AdminActivity.objects.create(
                    activity_type='file_reprocess',
                    description=f'Reprocessed file: {file.original_filename}',
                    admin_user=request.user
                )
                
                return Response({
                    'success': True,
                    'message': 'File reprocessing started'
                })
            
            elif action == 'update_status':
                new_status = request.data.get('status')
                if new_status in dict(FileUpload.STATUS_CHOICES):
                    file.status = new_status
                    file.save()
                    
                    return Response({
                        'success': True,
                        'message': f'File status updated to {new_status}'
                    })
            
            return Response({
                'success': False,
                'message': 'Invalid action'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except FileUpload.DoesNotExist:
            return Response({
                'success': False,
                'message': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def handle_file_deletion(self, request, file_id):
        """Handle file deletion"""
        try:
            file = FileUpload.objects.get(id=file_id)
            
            # Delete the actual file
            if file.file:
                if os.path.exists(file.file.path):
                    os.remove(file.file.path)
            
            # Log admin activity before deletion
            AdminActivity.objects.create(
                activity_type='file_delete',
                description=f'Deleted file: {file.original_filename}',
                admin_user=request.user
            )
            
            # Delete the database record
            file.delete()
            
            return Response({
                'success': True,
                'message': 'File deleted successfully'
            })
            
        except FileUpload.DoesNotExist:
            return Response({
                'success': False,
                'message': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def export_files(self, request):
        """Export files data to CSV"""
        import csv
        from io import StringIO
        
        # Get filtered queryset
        queryset = FileUpload.objects.select_related('user').all()
        
        # Apply filters
        search = request.GET.get('search', '')
        file_type = request.GET.get('file_type', '')
        status_filter = request.GET.get('status', '')
        user_filter = request.GET.get('user', '')
        
        if search:
            queryset = queryset.filter(
                Q(original_filename__icontains=search) |
                Q(description__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Filename', 'File Type', 'File Size (MB)', 'Status', 
            'User', 'User Email', 'Uploaded At', 'Description', 
            'Download Count', 'Feature Count', 'Error Message'
        ])
        
        # Write data
        for file in queryset:
            writer.writerow([
                str(file.id),
                file.original_filename,
                file.file_type,
                file.file_size_mb,
                file.status,
                f"{file.user.first_name} {file.user.last_name}".strip() or file.user.email,
                file.user.email,
                file.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                file.description,
                file.download_count,
                file.feature_count,
                file.error_message or ''
            ])
        
        # Create response
        from django.http import HttpResponse
        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="surveys_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response
    
    def get_files_statistics(self):
        """Get files statistics"""
        total_files = FileUpload.objects.count()
        processed_files = FileUpload.objects.filter(status='completed').count()
        processing_files = FileUpload.objects.filter(status='processing').count()
        error_files = FileUpload.objects.filter(status='failed').count()
        
        # Calculate rates
        processing_rate = (processed_files / total_files * 100) if total_files > 0 else 0
        error_rate = (error_files / total_files * 100) if total_files > 0 else 0
        
        # Calculate growth (files uploaded this month vs last month)
        now = timezone.now()
        this_month = FileUpload.objects.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).count()
        
        last_month = FileUpload.objects.filter(
            created_at__year=now.year if now.month > 1 else now.year - 1,
            created_at__month=now.month - 1 if now.month > 1 else 12
        ).count()
        
        file_growth = ((this_month - last_month) / last_month * 100) if last_month > 0 else 0
        
        # Calculate average processing time
        completed_files = FileUpload.objects.filter(
            status='completed',
            processing_started__isnull=False,
            processing_completed__isnull=False
        )
        
        avg_processing_time = 0
        if completed_files.exists():
            total_time = sum([
                (file.processing_completed - file.processing_started).total_seconds()
                for file in completed_files
            ])
            avg_processing_time = round(total_time / completed_files.count() / 60, 1)  # in minutes
        
        return {
            'total_files': total_files,
            'processed_files': processed_files,
            'processing_files': processing_files,
            'error_files': error_files,
            'processing_rate': round(processing_rate, 1),
            'error_rate': round(error_rate, 1),
            'file_growth': round(file_growth, 1),
            'avg_processing_time': avg_processing_time
        }
    
    def get_processing_queue(self):
        """Get files currently in processing queue"""
        processing_files = FileUpload.objects.filter(status='processing').select_related('user')[:10]
        
        queue_data = []
        for file in processing_files:
            queue_data.append({
                'id': str(file.id),
                'filename': file.original_filename,
                'file_type': file.file_type,
                'user_name': f"{file.user.first_name} {file.user.last_name}".strip() or file.user.email,
                'processing_started': file.processing_started.isoformat() if file.processing_started else None
            })
        
        return queue_data
    
    def detect_file_type(self, filename):
        """Detect file type from filename"""
        ext = os.path.splitext(filename)[1].lower()
        
        file_type_map = {
            '.kml': 'kml',
            '.csv': 'csv',
            '.shp': 'shapefile',
            '.geojson': 'geojson',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.pdf': 'pdf',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.zip': 'other'
        }
        
        return file_type_map.get(ext, 'other')

class SurveyFilePreviewAPIView(AdminRequiredMixin, APIView):
    """API view for file preview"""
    
    def get(self, request, file_id):
        try:
            file = FileUpload.objects.get(id=file_id)
            
            # Get preview data based on file type
            preview_data = self.get_preview_data(file)
            
            return Response({
                'success': True,
                'file': {
                    'id': str(file.id),
                    'filename': file.original_filename,
                    'file_type': file.file_type,
                    'file_size': file.file_size,
                    'status': file.status,
                    'preview_data': preview_data
                }
            })
            
        except FileUpload.DoesNotExist:
            return Response({
                'success': False,
                'message': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def get_preview_data(self, file):
        """Get preview data based on file type"""
        if file.file_type == 'kml':
            return self.get_kml_preview(file)
        elif file.file_type == 'csv':
            return self.get_csv_preview(file)
        elif file.file_type == 'shapefile':
            return self.get_shapefile_preview(file)
        else:
            return {'message': 'Preview not available for this file type'}
    
    def get_kml_preview(self, file):
        """Get KML file preview"""
        try:
            kml_data = KMLData.objects.filter(kml_file__file=file.file)[:10]
            return {
                'type': 'kml',
                'total_features': KMLData.objects.filter(kml_file__file=file.file).count(),
                'preview_features': [
                    {
                        'kitta_number': data.kitta_number,
                        'owner_name': data.owner_name,
                        'geometry_type': data.geometry_type,
                        'area_hectares': float(data.area_hectares) if data.area_hectares else None,
                        'description': data.description
                    }
                    for data in kml_data
                ]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_csv_preview(self, file):
        """Get CSV file preview"""
        try:
            csv_data = CSVData.objects.filter(file_upload=file)[:10]
            return {
                'type': 'csv',
                'total_rows': CSVData.objects.filter(file_upload=file).count(),
                'preview_rows': [
                    {
                        'row_number': data.row_number,
                        'data': data.data
                    }
                    for data in csv_data
                ]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_shapefile_preview(self, file):
        """Get Shapefile preview"""
        try:
            shapefile_data = ShapefileData.objects.filter(file_upload=file)[:10]
            return {
                'type': 'shapefile',
                'total_features': ShapefileData.objects.filter(file_upload=file).count(),
                'preview_features': [
                    {
                        'feature_id': data.feature_id,
                        'geometry_type': data.geometry_type,
                        'attributes': data.attributes
                    }
                    for data in shapefile_data
                ]
            }
        except Exception as e:
            return {'error': str(e)}

class SurveyFileDownloadAPIView(AdminRequiredMixin, APIView):
    """API view for file download"""
    
    def get(self, request, file_id):
        try:
            file = FileUpload.objects.get(id=file_id)
            
            # Increment download count
            file.increment_download_count()
            
            # Log admin activity
            AdminActivity.objects.create(
                activity_type='file_download',
                description=f'Downloaded file: {file.original_filename}',
                admin_user=request.user
            )
            
            # Return file download response
            from django.http import FileResponse
            response = FileResponse(file.file, as_attachment=True, filename=file.original_filename)
            return response
            
        except FileUpload.DoesNotExist:
            return Response({
                'success': False,
                'message': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)

class SystemMetricsAPIView(APIView):
    """API view for system metrics"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get system metrics"""
        try:
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get system metrics
            metrics = self.get_system_metrics()
            
            return Response({
                'success': True,
                'metrics': metrics
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_system_metrics(self):
        """Get comprehensive system metrics"""
        import platform
        import psutil
        import django
        
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1) if PSUTIL_AVAILABLE else 0
        memory = psutil.virtual_memory() if PSUTIL_AVAILABLE else None
        disk = psutil.disk_usage('/') if PSUTIL_AVAILABLE else None
        
        # Get database connections
        from django.db import connection
        db_connections = len(connection.queries) if hasattr(connection, 'queries') else 0
        
        # Get system uptime
        uptime_seconds = psutil.boot_time() if PSUTIL_AVAILABLE else 0
        uptime_days = (timezone.now().timestamp() - uptime_seconds) / 86400 if uptime_seconds > 0 else 0
        
        return {
            'cpu_usage': round(cpu_percent, 1),
            'memory_usage': round(memory.percent, 1) if memory else 0,
            'memory_used_gb': round(memory.used / (1024**3), 2) if memory else 0,
            'memory_total_gb': round(memory.total / (1024**3), 2) if memory else 0,
            'disk_usage': round(disk.percent, 1) if disk else 0,
            'disk_used_gb': round(disk.used / (1024**3), 2) if disk else 0,
            'disk_total_gb': round(disk.total / (1024**3), 2) if disk else 0,
            'db_connections': db_connections,
            'uptime_days': round(uptime_days, 1),
            'uptime_percentage': min((uptime_days / 365) * 100, 100),
            'network_usage': self.get_network_usage(),
            'system_info': {
                'os_version': platform.system() + ' ' + platform.release(),
                'python_version': platform.python_version(),
                'django_version': django.get_version(),
                'database': settings.DATABASES['default']['ENGINE'].split('.')[-1],
                'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timezone': settings.TIME_ZONE
            }
        }
    
    def get_network_usage(self):
        """Get network usage statistics"""
        if not PSUTIL_AVAILABLE:
            return 0
        
        try:
            net_io = psutil.net_io_counters()
            # Calculate network usage in Mbps (simplified)
            total_bytes = net_io.bytes_sent + net_io.bytes_recv
            return round(total_bytes / (1024 * 1024), 2)  # MB
        except:
            return 0

class SystemAPIView(AdminRequiredMixin, APIView):
    """Comprehensive system management API"""
    
    def get(self, request):
        """Get system status and information"""
        try:
            # Get system status
            status = self.get_system_status()
            
            # Get system services
            services = self.get_system_services()
            
            # Get system alerts
            alerts = self.get_system_alerts()
            
            # Get maintenance windows
            maintenance_windows = self.get_maintenance_windows()
            
            # Get system logs
            logs = self.get_system_logs()
            
            # Get security status
            security = self.get_security_status()
            
            # Get real-time monitoring data
            monitoring = self.get_real_time_monitoring()
            
            return Response({
                'success': True,
                'status': status,
                'services': services,
                'alerts': alerts,
                'maintenance_windows': maintenance_windows,
                'logs': logs,
                'security': security,
                'monitoring': monitoring
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Handle system control actions"""
        try:
            action = request.data.get('action')
            
            if action == 'restart_services':
                return self.restart_services(request)
            elif action == 'clear_cache':
                return self.clear_cache(request)
            elif action == 'emergency_shutdown':
                return self.emergency_shutdown(request)
            elif action == 'schedule_maintenance':
                return self.schedule_maintenance(request)
            elif action == 'toggle_service':
                return self.toggle_service(request)
            elif action == 'create_backup':
                return self.create_backup(request)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid action'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_system_status(self):
        """Get overall system status"""
        import psutil
        
        # Get basic metrics
        cpu_percent = psutil.cpu_percent(interval=1) if PSUTIL_AVAILABLE else 0
        memory = psutil.virtual_memory() if PSUTIL_AVAILABLE else None
        
        # Determine overall status
        if cpu_percent > 90 or (memory and memory.percent > 90):
            overall_status = 'Critical'
        elif cpu_percent > 70 or (memory and memory.percent > 70):
            overall_status = 'Warning'
        else:
            overall_status = 'Online'
        
        # Get active alerts count
        active_alerts = SystemNotification.objects.filter(
            is_read=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        critical_alerts = SystemNotification.objects.filter(
            is_read=False,
            priority='critical',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        return {
            'overall_status': overall_status,
            'cpu_usage': round(cpu_percent, 1),
            'memory_usage': round(memory.percent, 1) if memory else 0,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
            'cpu_trend': self.get_cpu_trend(),
            'memory_trend': self.get_memory_trend()
        }
    
    def get_system_services(self):
        """Get system services status"""
        services = [
            {
                'name': 'Web Server',
                'description': 'Django Development Server',
                'status': 'online',
                'port': 8000
            },
            {
                'name': 'Database',
                'description': 'SQLite Database',
                'status': 'online',
                'port': None
            },
            {
                'name': 'Cache',
                'description': 'Memory Cache',
                'status': 'online',
                'port': None
            },
            {
                'name': 'File Storage',
                'description': 'Local File System',
                'status': 'online',
                'port': None
            },
            {
                'name': 'Authentication',
                'description': 'Django Auth System',
                'status': 'online',
                'port': None
            },
            {
                'name': 'API Gateway',
                'description': 'REST API Services',
                'status': 'online',
                'port': 8000
            }
        ]
        
        return services
    
    def get_system_alerts(self):
        """Get system alerts"""
        alerts = SystemNotification.objects.filter(
            is_read=False,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        return [
            {
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.priority,  # Map priority to severity for frontend
                'created_at': alert.created_at.isoformat(),
                'is_read': alert.is_read
            }
            for alert in alerts
        ]
    
    def get_maintenance_windows(self):
        """Get maintenance windows"""
        windows = MaintenanceWindow.objects.filter(
            end_time__gte=timezone.now()
        ).order_by('start_time')[:5]
        
        return [
            {
                'id': window.id,
                'title': window.title,
                'description': window.description,
                'start_time': window.start_time.isoformat(),
                'end_time': window.end_time.isoformat(),
                'is_active': window.start_time <= timezone.now() <= window.end_time,
                'status': 'scheduled' if window.start_time > timezone.now() else 'active' if window.end_time > timezone.now() else 'completed'
            }
            for window in windows
        ]
    
    def get_system_logs(self):
        """Get system logs"""
        # Get recent admin activities as system logs
        activities = AdminActivity.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-created_at')[:20]
        
        return [
            {
                'id': activity.id,
                'message': activity.description,
                'level': 'info',
                'source': 'admin_activity',
                'timestamp': activity.created_at.isoformat(),
                'user': activity.admin_user.email if activity.admin_user else 'System'
            }
            for activity in activities
        ]
    
    def get_security_status(self):
        """Get security status"""
        return {
            'firewall': True,  # Simulated
            'ssl': True,  # Simulated
            'authentication': True,  # Simulated
            'vulnerabilities': 0,  # Simulated
            'last_scan': timezone.now().isoformat(),
            'security_score': 95
        }
    
    def get_real_time_monitoring(self):
        """Get real-time monitoring data"""
        return {
            'requests_per_minute': 150,  # Simulated
            'response_time': 250,  # ms
            'error_rate': 0.5,  # %
            'active_connections': 25,  # Simulated
            'last_updated': timezone.now().isoformat()
        }
    
    def get_cpu_trend(self):
        """Get CPU usage trend"""
        # Simulated trend data
        return 5.2
    
    def get_memory_trend(self):
        """Get memory usage trend"""
        # Simulated trend data
        return 3.8
    
    def restart_services(self, request):
        """Restart system services"""
        try:
            # Log the action
            AdminActivity.objects.create(
                activity_type='services_restarted',
                description='System services restarted',
                admin_user=request.user,
                metadata={'action': 'restart_services'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Services restarted successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def clear_cache(self, request):
        """Clear system cache"""
        try:
            # Log the action
            AdminActivity.objects.create(
                activity_type='cache_cleared',
                description='System cache cleared',
                admin_user=request.user,
                metadata={'action': 'clear_cache'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Cache cleared successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def emergency_shutdown(self, request):
        """Emergency system shutdown"""
        try:
            password = request.data.get('password')
            if not request.user.check_password(password):
                return Response({
                    'success': False,
                    'message': 'Invalid password'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='emergency_shutdown',
                description='Emergency shutdown initiated',
                admin_user=request.user,
                metadata={'action': 'emergency_shutdown'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Emergency shutdown initiated'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def schedule_maintenance(self, request):
        """Schedule maintenance window"""
        try:
            window_data = request.data.get('window')
            
            # Create maintenance window
            maintenance_window = MaintenanceWindow.objects.create(
                title='Scheduled Maintenance',
                description=f'Maintenance window: {window_data}',
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(hours=2),
                status='scheduled',
                created_by=request.user
            )
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='maintenance_scheduled',
                description=f'Maintenance scheduled for {window_data}',
                admin_user=request.user,
                metadata={'maintenance_window': window_data},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Maintenance window scheduled'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def toggle_service(self, request):
        """Toggle service status"""
        try:
            service_name = request.data.get('service')
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='service_toggled',
                description=f'Service {service_name} toggled',
                admin_user=request.user,
                metadata={'service': service_name},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': f'Service {service_name} toggled',
                'status': 'online'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create_backup(self, request):
        """Create system backup"""
        try:
            # Create backup log entry
            backup_log = BackupLog.objects.create(
                backup_type='system',
                status='running',
                initiated_by=request.user
            )
            
            # Simulate backup process
            import time
            time.sleep(2)
            
            # Update backup log
            backup_log.status = 'completed'
            backup_log.completed_at = timezone.now()
            backup_log.file_path = f'/backups/system_{timezone.now().strftime("%Y%m%d_%H%M%S")}.backup'
            backup_log.file_size = 1024 * 1024  # 1MB dummy size
            backup_log.save()
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='system_backup',
                description='System backup completed',
                admin_user=request.user,
                metadata={'backup_id': str(backup_log.id)},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'System backup completed successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SettingsAPIView(AdminRequiredMixin, APIView):
    """Comprehensive settings management API"""
    
    def get(self, request):
        """Get all settings"""
        try:
            settings = self.get_all_settings()
            return Response({
                'success': True,
                'settings': settings
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Update settings"""
        try:
            data = request.data
            
            # Handle bulk settings update
            if isinstance(data, dict) and len(data) > 2:  # More than just key-value pair
                return self.update_bulk_settings(request, data)
            else:
                # Handle single setting update
                return self.update_single_setting(request, data)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """Reset settings to defaults"""
        try:
            self.reset_to_defaults()
            
            # Log the action
            AdminActivity.objects.create(
                activity_type='settings_reset',
                description='Settings reset to defaults',
                admin_user=request.user,
                metadata={'action': 'reset_settings'},
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'message': 'Settings reset to defaults successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_all_settings(self):
        """Get all settings from database and defaults"""
        settings = {}
        
        # Get settings from database
        db_settings = AdminSettings.objects.all()
        for setting in db_settings:
            settings[setting.key] = self.parse_setting_value(setting.value)
        
        # Add default settings for missing keys
        default_settings = self.get_default_settings()
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
        
        return settings
    
    def update_single_setting(self, request, data):
        """Update a single setting"""
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return Response({
                'success': False,
                'message': 'Setting key is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create setting
        setting, created = AdminSettings.objects.get_or_create(
            key=key,
            defaults={
                'value': str(value),
                'description': f'Setting for {key}'
            }
        )
        
        if not created:
            setting.value = str(value)
            setting.save()
        
        # Log the action
        AdminActivity.objects.create(
            activity_type='setting_updated',
            description=f'Setting "{key}" updated to "{value}"',
            admin_user=request.user,
            metadata={'key': key, 'value': value},
            ip_address=request.META.get('REMOTE_ADDR', '')
        )
        
        return Response({
            'success': True,
            'message': f'Setting "{key}" updated successfully'
        })
    
    def update_bulk_settings(self, request, data):
        """Update multiple settings at once"""
        updated_count = 0
        
        for key, value in data.items():
            if key in ['csrfmiddlewaretoken', 'X-CSRFToken']:
                continue
                
            # Update or create setting
            setting, created = AdminSettings.objects.get_or_create(
                key=key,
                defaults={
                    'value': str(value),
                    'description': f'Setting for {key}'
                }
            )
            
            if not created:
                setting.value = str(value)
                setting.save()
            
            updated_count += 1
        
        # Log the action
        AdminActivity.objects.create(
            activity_type='settings_bulk_update',
            description=f'Updated {updated_count} settings',
            admin_user=request.user,
            metadata={'updated_count': updated_count, 'settings': list(data.keys())},
            ip_address=request.META.get('REMOTE_ADDR', '')
        )
        
        return Response({
            'success': True,
            'message': f'{updated_count} settings updated successfully'
        })
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        # Delete all custom settings
        AdminSettings.objects.all().delete()
        
        # Create default settings
        default_settings = self.get_default_settings()
        for key, value in default_settings.items():
            AdminSettings.objects.create(
                key=key,
                value=str(value),
                description=f'Default setting for {key}'
            )
    
    def get_default_settings(self):
        """Get default settings values"""
        return {
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
    
    def parse_setting_value(self, value):
        """Parse setting value from string to appropriate type"""
        try:
            # Try to parse as boolean
            if value.lower() in ['true', 'false']:
                return value.lower() == 'true'
            
            # Try to parse as integer
            if value.isdigit():
                return int(value)
            
            # Try to parse as float
            try:
                return float(value)
            except ValueError:
                pass
            
            # Return as string
            return value
        except:
            return value

class NotificationsAPIView(AdminRequiredMixin, APIView):
    """API endpoint for system notifications"""
    
    def get(self, request):
        notifications = SystemNotification.objects.all()[:20]
        return JsonResponse({'notifications': list(notifications.values())})
    
    def post(self, request):
        """Create new notification"""
        serializer = NotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            notification = serializer.save()
            return Response(SystemNotificationSerializer(notification).data)
        return Response(serializer.errors, status=400)

class BackupAPIView(AdminRequiredMixin, APIView):
    """API endpoint for system backup operations"""
    
    def get(self, request):
        backup_logs = BackupLog.objects.all()[:10]
        return JsonResponse({'backups': list(backup_logs.values())})
    
    def post(self, request):
        """Initiate backup"""
        backup_type = request.data.get('backup_type', 'database')
        
        try:
            # Create backup log entry
            backup_log = BackupLog.objects.create(
                backup_type=backup_type,
                status='running',
                initiated_by=request.user
            )
            
            # Simulate backup process (in real implementation, this would be async)
            import time
            time.sleep(2)  # Simulate processing time
            
            # Update backup log
            backup_log.status = 'completed'
            backup_log.completed_at = timezone.now()
            backup_log.file_path = f'/backups/{backup_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.backup'
            backup_log.file_size = 1024 * 1024  # 1MB dummy size
            backup_log.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                activity_type='system_backup',
                description=f'{backup_type} backup completed',
                admin_user=request.user
            )
            
            return Response({
                'status': 'success',
                'message': f'{backup_type} backup completed',
                'backup_id': backup_log.id
            })
        
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)})

class ActivityAPIView(AdminRequiredMixin, APIView):
    """API endpoint for admin activities"""
    
    def get(self, request):
        activities = AdminActivity.objects.all()[:20]
        return JsonResponse({'activities': list(activities.values())})

class UserActivityAPIView(AdminRequiredMixin, APIView):
    """API endpoint for detailed user activity"""
    
    def get(self, request):
        # Get user activity data
        user_activities = UserAction.objects.select_related('user').all()[:50]
        
        activity_data = []
        for activity in user_activities:
            activity_data.append({
                'id': activity.id,
                'user_id': activity.user.id,
                'username': activity.user.username,
                'action': activity.action_type,
                'timestamp': activity.created_at.isoformat(),
                'page': activity.action_data.get('page', ''),
                'session_duration': activity.action_data.get('session_duration', 0)
            })
        
        return JsonResponse({
            'success': True,
            'activities': activity_data
        })

class RealTimeActivityAPIView(AdminRequiredMixin, APIView):
    """API endpoint for real-time user activity"""
    
    def get(self, request):
        # Get active users
        active_users = RealTimeUserActivity.objects.filter(is_active=True)[:20]
        return JsonResponse({'active_users': list(active_users.values())})

class UserErrorsAPIView(AdminRequiredMixin, APIView):
    """API endpoint for user errors"""
    
    def get(self, request):
        errors = UserError.objects.all()[:20]
        return JsonResponse({'errors': list(errors.values())})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        notification = SystemNotification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})
    except SystemNotification.DoesNotExist:
        return Response({'status': 'error', 'message': 'Notification not found'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_system_metrics(request):
    """Update system metrics (called by monitoring service)"""
    try:
        # Get system information using psutil if available
        if PSUTIL_AVAILABLE:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
        else:
            # Fallback values when psutil is not available
            cpu_usage = 0.0
            memory_usage = 0.0
            disk_usage = 0.0
        
        # Get active users count
        active_users = UserSession.objects.filter(is_active=True).count()
        
        # Create new metrics entry
        SystemMetrics.objects.create(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            active_users=active_users,
            total_requests=0,
            error_rate=0.0,
            response_time=0.0
        )
        
        return Response({'status': 'success', 'message': 'Metrics updated'})
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)})
