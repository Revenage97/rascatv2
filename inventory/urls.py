from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    path('backup/', views.backup_file, name='backup_file'),
    path('download-backup/', views.download_backup, name='download_backup'),
    path('download-file/<int:history_id>/', views.download_file, name='download_file'),
    path('change-password/', views.change_password, name='change_password'),
    path('webhook-settings/', views.webhook_settings, name='webhook_settings'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    path('send-to-telegram/', views.send_to_telegram, name='send_to_telegram'),
    path('update-min-stock/', views.update_min_stock, name='update_min_stock'),
]
