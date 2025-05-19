from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('kelola-stok-barang/', views.kelola_stok_barang, name='kelola_stok_barang'),
    path('kelola-harga/', views.kelola_harga, name='kelola_harga'),
    path('kelola-stok-packing/', views.kelola_stok_packing, name='kelola_stok_packing'),
    path('transfer-stok/', views.transfer_stok, name='transfer_stok'),
    path('upload/', views.upload_file, name='upload_file'),
    path('backup/', views.backup_file, name='backup_file'),
    path('change-password/', views.change_password, name='change_password'),
    path('webhook-settings/', views.webhook_settings, name='webhook_settings'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    path('api/send-to-telegram/', views.send_to_telegram, name='send_to_telegram'),
    path('api/update-min-stock/', views.update_min_stock, name='update_min_stock'),
    path('api/delete-min-stock/', views.delete_min_stock, name='delete_min_stock'),
    path('api/get-item/', views.get_item, name='get_item'),
    path('api/update-item/', views.update_item, name='update_item'),
    path('api/delete-item/', views.delete_item, name='delete_item'),
]
