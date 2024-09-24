"""
Definition of urls for RedmineTicketManager.
"""

from django.urls import path
from app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('link/<str:redmine_url>/', views.link, name='link'),
    path('download/<str:download_uuid>/', views.download, name='download'),
    path(
        'download_file/<str:download_uuid>/',
        views.download_file,
        name='download_file'
    ),
    path(
        'start_development/',
        views.StartDevelopmentView.as_view(),
        name='start_development'
    ),
    path(
        'add_issue/',
        views.AddIssueView.as_view(),
        name='add_issue'
    ),
    path(
        'list_developments/',
        views.list_developments,
        name='list_developments'
    ),
    path(
        'export_checklist/',
        views.ExportChecklistView.as_view(),
        name='export_checklist'
    ),
    path(
        'export_codereview_result/',
        views.ExportCodeReviewResultView.as_view(),
        name='export_codereview_result'
    )
]
