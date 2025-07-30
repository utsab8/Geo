from django.urls import path
from .views import (
    UserDashboardView, UploadsView, MySurveyView, HistoryView, HelpView, ProfileView,
    SurveyReportView, SurveyReportAPIView, SurveyExportView, HistoryAPIView, ProfileAPIView,
    test_css_view, css_test_view, create_sample_history_data
)
from .kml_views import (
    KMLUploadView, KMLPreviewView, KMLAjaxView, KMLListView, KMLDeleteView, KMLGeoJSONView
)
from .file_views import (
    FileUploadView, FileListView, FileDetailView, FilePreviewView,
    FileExportView, FileDeleteView, FileShareView, SharedFileView, FileAjaxView, FileStatsView,
    CSVPreviewView, ShapefilePreviewView, CSVGeoJSONView, ShapefileGeoJSONView
)
from . import views, file_views, kml_views

urlpatterns = [
    path('', UserDashboardView.as_view(), name='user_dashboard'),
    path('uploads/', UploadsView.as_view(), name='uploads'),
    path('file-preview/', FilePreviewView.as_view(), name='file_preview'),
    path('csv-preview/<uuid:file_id>/', CSVPreviewView.as_view(), name='csv_preview'),
    path('shapefile-preview/<uuid:file_id>/', ShapefilePreviewView.as_view(), name='shapefile_preview'),

    # KML routes
    path('kml/upload/', KMLUploadView.as_view(), name='kml_upload'),
    path('kml/list/', KMLListView.as_view(), name='kml_list'),
    path('kml/preview/<uuid:kml_id>/', KMLPreviewView.as_view(), name='kml_preview'),
    path('kml/ajax/<uuid:kml_id>/', KMLAjaxView.as_view(), name='kml_ajax'),
    path('kml/delete/<uuid:kml_id>/', KMLDeleteView.as_view(), name='kml_delete'),
    path('kml/geojson/<uuid:kml_id>/', KMLGeoJSONView.as_view(), name='kml_geojson'),

    # Comprehensive file upload routes
    path('files/upload/', FileUploadView.as_view(), name='file_upload'),
    path('files/list/', FileListView.as_view(), name='file_list'),
    path('files/<uuid:file_id>/', FileDetailView.as_view(), name='file_detail'),
    path('files/<uuid:file_id>/preview/', FilePreviewView.as_view(), name='file_preview_new'),
    path('files/<uuid:file_id>/export/<str:format_type>/', FileExportView.as_view(), name='file_export'),
    path('files/<uuid:file_id>/delete/', FileDeleteView.as_view(), name='file_delete'),
    path('files/<uuid:file_id>/share/', FileShareView.as_view(), name='file_share'),
    path('files/<uuid:file_id>/ajax/', FileAjaxView.as_view(), name='file_ajax'),
    path('files/stats/', FileStatsView.as_view(), name='file_stats'),
    
    # Shared file access
    path('shared/<uuid:share_token>/', SharedFileView.as_view(), name='shared_file'),

    path('my-survey/', MySurveyView.as_view(), name='my_survey'),
    path('survey-report/', SurveyReportView.as_view(), name='survey_report'),
    path('survey-report/api/', SurveyReportAPIView.as_view(), name='survey_report_api'),
    path('survey-report/data/', SurveyReportAPIView.as_view(), name='survey_report_data'),
    path('survey-report/reprocess/', SurveyReportAPIView.as_view(), name='survey_report_reprocess'),
    path('survey-report/export/', SurveyExportView.as_view(), name='survey_export'),
    path('history/', HistoryView.as_view(), name='history'),
    path('history/api/', HistoryAPIView.as_view(), name='history_api'),
    path('history/create-sample-data/', create_sample_history_data, name='create_sample_data'),
    path('history/test/', create_sample_history_data, name='test_history'),
    path('help/', HelpView.as_view(), name='help'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/api/', ProfileAPIView.as_view(), name='profile_api'),
    path('test-css/', test_css_view, name='test_css'),
    path('css-test/', css_test_view, name='css_test'),
]

urlpatterns += [
    path('csv/geojson/<uuid:file_id>/', CSVGeoJSONView.as_view(), name='csv_geojson'),
    path('shapefile/geojson/<uuid:file_id>/', ShapefileGeoJSONView.as_view(), name='shapefile_geojson'),
] 