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
from userdashboard.models import FileUpload, KMLData, UploadedParcel

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
class DashboardStatsAPIView(AdminRequiredMixin, APIView):
    """API endpoint for dashboard statistics"""
    
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
    
    def get(self, request):
        """Get surveys list"""
        try:
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'message': 'Admin privileges required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Implementation for getting surveys
            return Response({
                'success': True,
                'surveys': []
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            
            # Implementation for getting system metrics
            return Response({
                'success': True,
                'metrics': {}
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
