from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    UserSession, AdminActivity, UserPageView, UserAction, 
    UserEngagement, RealTimeUserActivity, UserError
)
import json

User = get_user_model()

class AdminDashboardMiddleware:
    """Middleware to track user sessions and activities for admin dashboard"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Track user session if user is authenticated
        if request.user.is_authenticated:
            self.track_user_session(request)
        
        return response
    
    def track_user_session(self, request):
        """Track user session for analytics"""
        try:
            # Get or create user session
            session_key = request.session.session_key
            if session_key:
                session, created = UserSession.objects.get_or_create(
                    session_key=session_key,
                    defaults={
                        'user': request.user,
                        'ip_address': self.get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'is_active': True
                    }
                )
                
                # Update existing session if not created
                if not created:
                    session.is_active = True
                    session.save()
        except Exception as e:
            # Log error but don't break the request
            print(f"Error tracking user session: {e}")
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AdminActivityMiddleware:
    """Middleware to track admin activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Track admin activities
        if request.user.is_authenticated and request.user.is_staff:
            self.track_admin_activity(request, response)
        
        return response
    
    def track_admin_activity(self, request, response):
        """Track admin activities"""
        try:
            # Only track admin dashboard activities
            if '/admin-dashboard/' in request.path:
                activity_type = self.determine_activity_type(request)
                if activity_type:
                    AdminActivity.objects.create(
                        activity_type=activity_type,
                        description=self.get_activity_description(request, activity_type),
                        admin_user=request.user,
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'method': request.method,
                            'path': request.path,
                            'status_code': response.status_code
                        }
                    )
        except Exception as e:
            # Log error but don't break the request
            print(f"Error tracking admin activity: {e}")
    
    def determine_activity_type(self, request):
        """Determine activity type based on request"""
        path = request.path
        method = request.method
        
        if '/users/' in path and method == 'POST':
            return 'user_updated'
        elif '/backup/' in path and method == 'POST':
            return 'system_backup'
        elif '/settings/' in path and method == 'POST':
            return 'system_maintenance'
        elif '/notifications/' in path and method == 'POST':
            return 'system_maintenance'
        
        return None
    
    def get_activity_description(self, request, activity_type):
        """Get activity description"""
        descriptions = {
            'user_updated': 'User management action performed',
            'system_backup': 'System backup initiated',
            'system_maintenance': 'System settings updated',
        }
        return descriptions.get(activity_type, 'Admin activity performed')
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserActivityTrackingMiddleware:
    """Enhanced middleware to track all user activity"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Track page view before processing
        if request.user.is_authenticated:
            self.track_page_view(request)
        
        # Process request
        response = self.get_response(request)
        
        # Track real-time activity after processing
        if request.user.is_authenticated:
            self.track_real_time_activity(request, response)
        
        return response
    
    def track_page_view(self, request):
        """Track every page view"""
        try:
            if request.user.is_authenticated:
                UserPageView.objects.create(
                    user=request.user,
                    page_url=request.path,
                    page_name=self.get_page_name(request.path),
                    session_key=request.session.session_key or '',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    referrer=request.META.get('HTTP_REFERER', '')
                )
        except Exception as e:
            print(f"Error tracking page view: {e}")
    
    def track_real_time_activity(self, request, response):
        """Track real-time user activity"""
        try:
            if request.user.is_authenticated:
                # Update or create real-time activity
                activity, created = RealTimeUserActivity.objects.get_or_create(
                    user=request.user,
                    session_key=request.session.session_key or '',
                    defaults={
                        'current_page': request.path,
                        'current_action': self.get_current_action(request),
                        'ip_address': self.get_client_ip(request),
                        'is_active': True
                    }
                )
                
                if not created:
                    activity.current_page = request.path
                    activity.current_action = self.get_current_action(request)
                    activity.is_active = True
                    activity.save()
        except Exception as e:
            print(f"Error tracking real-time activity: {e}")
    
    def get_page_name(self, path):
        """Get human-readable page name"""
        page_names = {
            '/': 'Home',
            '/dashboard/': 'Dashboard',
            '/uploads/': 'File Uploads',
            '/profile/': 'Profile',
            '/admin-dashboard/': 'Admin Dashboard',
            '/admin-dashboard/users/': 'User Management',
            '/admin-dashboard/surveys/': 'Survey Management',
            '/admin-dashboard/system/': 'System Management',
            '/admin-dashboard/settings/': 'Settings',
            '/admin-dashboard/profile/': 'Admin Profile',
        }
        return page_names.get(path, 'Unknown Page')
    
    def get_current_action(self, request):
        """Get current user action"""
        method = request.method
        path = request.path
        
        if method == 'POST':
            if 'upload' in path:
                return 'File Upload'
            elif 'download' in path:
                return 'File Download'
            elif 'delete' in path:
                return 'File Delete'
            elif 'export' in path:
                return 'Export'
            else:
                return 'Form Submission'
        elif method == 'GET':
            if 'preview' in path:
                return 'Preview'
            elif 'search' in path:
                return 'Search'
            else:
                return 'Page View'
        
        return 'Unknown Action'
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserActionTrackingMiddleware:
    """Middleware to track specific user actions"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Track user actions after processing
        if request.user.is_authenticated:
            self.track_user_action(request, response)
        
        return response
    
    def track_user_action(self, request, response):
        """Track specific user actions"""
        try:
            action_type = self.determine_action_type(request)
            if action_type:
                action_data = self.get_action_data(request, response)
                
                UserAction.objects.create(
                    user=request.user,
                    action_type=action_type,
                    action_data=action_data,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    session_key=request.session.session_key or ''
                )
        except Exception as e:
            print(f"Error tracking user action: {e}")
    
    def determine_action_type(self, request):
        """Determine action type based on request"""
        method = request.method
        path = request.path
        
        if method == 'POST':
            if 'upload' in path:
                return 'file_upload'
            elif 'download' in path:
                return 'file_download'
            elif 'delete' in path:
                return 'file_delete'
            elif 'share' in path:
                return 'file_share'
            elif 'profile' in path:
                return 'profile_update'
            elif 'password' in path:
                return 'password_change'
            elif 'export' in path:
                return 'export'
            elif 'contact' in path:
                return 'contact_form'
        
        elif method == 'GET':
            if 'search' in path:
                return 'search'
            elif 'preview' in path:
                return 'preview'
        
        return None
    
    def get_action_data(self, request, response):
        """Get action-specific data"""
        data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'timestamp': timezone.now().isoformat()
        }
        
        # Add form data for POST requests
        if request.method == 'POST':
            data['form_data'] = dict(request.POST)
        
        # Add query parameters for GET requests
        if request.method == 'GET':
            data['query_params'] = dict(request.GET)
        
        return data
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserErrorTrackingMiddleware:
    """Middleware to track user-facing errors"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Track errors after processing
        if response.status_code >= 400:
            self.track_error(request, response)
        
        return response
    
    def track_error(self, request, response):
        """Track user-facing errors"""
        try:
            error_type = self.determine_error_type(response.status_code, request.path)
            
            UserError.objects.create(
                user=request.user if request.user.is_authenticated else None,
                error_type=error_type,
                error_message=f"HTTP {response.status_code}",
                error_details={
                    'status_code': response.status_code,
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'form_data': dict(request.POST) if request.method == 'POST' else {}
                },
                page_url=request.path,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error tracking user error: {e}")
    
    def determine_error_type(self, status_code, path):
        """Determine error type based on status code and path"""
        if status_code == 404:
            return 'system_error'
        elif status_code == 403:
            return 'permission_error'
        elif status_code == 401:
            return 'authentication_error'
        elif status_code == 500:
            return 'system_error'
        elif 'upload' in path:
            return 'file_upload_error'
        elif 'export' in path:
            return 'export_error'
        else:
            return 'system_error'
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 