from django.contrib import admin
from .models import (
    FileUpload, KMLFile, KMLData, FileShare, FileProcessingLog,
    DownloadLog, ContactFormSubmission, SurveyHistoryLog
)

# Register your models here.

@admin.register(ContactFormSubmission)
class ContactFormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'submitted_at', 'user']
    list_filter = ['submitted_at', 'user']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['submitted_at', 'user']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'user')
        }),
        ('Message Details', {
            'fields': ('subject', 'message', 'submitted_at')
        }),
        ('Admin Management', {
            'fields': ('is_resolved', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(SurveyHistoryLog)
class SurveyHistoryLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'file_name', 'record_count', 'user', 'created_at']
    list_filter = ['action_type', 'file_type', 'created_at', 'user']
    search_fields = ['file_name', 'description', 'user__username']
    readonly_fields = ['created_at', 'user']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('action_type', 'user', 'created_at')
        }),
        ('File Information', {
            'fields': ('file_name', 'file_type', 'record_count', 'map_coordinates_count')
        }),
        ('Filter & Export Details', {
            'fields': ('filters_applied', 'description', 'export_file_path'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
