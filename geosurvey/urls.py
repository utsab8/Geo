"""
URL configuration for geosurvey project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

def custom_logout(request):
    """Custom logout view that handles both GET and POST requests"""
    logout(request)
    return HttpResponseRedirect('/api/account/login-page/')

urlpatterns = [
    # Root URL redirects to login page
    path('', lambda request: redirect('/api/account/login-page/'), name='root'),
    
    # Authentication routes
    path('login/', lambda request: redirect('/api/account/login-page/'), name='login_redirect'),
    path('signup/', lambda request: redirect('/api/account/signup-page/'), name='signup_redirect'),
    path('logout/', custom_logout, name='logout'),
    
    # Django admin and authentication
    path('accounts/login/', lambda request: redirect('/api/account/login-page/')),  # Fix for LoginRequiredMixin default
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/account/', include('account.urls')),
    
    # User dashboard (after login)
    path('dashboard/', include('userdashboard.urls')),
    
    # Admin dashboard (for admin users)
    path('admin-dashboard/', include('admindashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
