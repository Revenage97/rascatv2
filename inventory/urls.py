from django.urls import path
from . import views, views_reset_data, views_reset_all_items
from django.views.generic import RedirectView

app_name = 'inventory'
urlpatterns = [
    # Tambahkan path untuk root URL yang redirect ke dashboard
    path('', RedirectView.as_view(pattern_name='inventory:dashboard'), name='root'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('forecasting/', views.forecasting, name='forecasting'),
    path('otomatisasi/', views.otomatisasi, name='otomatisasi'),
    path('kelola-stok-barang/', views.kelola_stok_barang, name='kelola_stok_barang'),
    path('kelola-harga/', views.kelola_harga, name='kelola_harga'),
    path('kelola-stok-packing/', views.kelola_stok_packing, name='kelola_stok_packing'),
    path('transfer-stok/', views.transfer_stok, name='transfer_stok'),
    path('data-exp-produk/', views.data_exp_produk, name='data_exp_produk'),
    path('upload/', views.upload_file, name='upload_file'),
    path('upload-transfer/', views.upload_transfer_file, name='upload_transfer_file'),
    path('upload-exp-produk/', views.upload_exp_produk_file, name='upload_exp_produk_file'),
    path('change-password/', views.change_password, name='change_password'),
    path('webhook-settings/', views.webhook_settings, name='webhook_settings'),
    path('kelola-pengguna/', views.kelola_pengguna, name='kelola_pengguna'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    # path('api/send-to-telegram/', views.send_to_telegram, name='send_to_telegram'),  # Commented out as function doesn't exist
    # path('api/update-min-stock/', views.update_min_stock, name='update_min_stock'),  # Commented out as function doesn't exist
    # path('api/delete-min-stock/', views.delete_min_stock, name='delete_min_stock'),  # Commented out as function doesn't exist
    # path('api/get-item/', views.get_item, name='get_item'),  # Commented out as function doesn't exist
    # path('api/update-item/', views.update_item, name='update_item'),  # Commented out as function doesn't exist
    # path('api/delete-item/', views.delete_item, name='delete_item'),  # Commented out as function doesn't exist
    # path('api/save-transfer/', views.save_transfer, name='save_transfer'),  # Commented out as function doesn't exist
    path('api/save-expiry-date/', views.save_expiry_date, name='save_expiry_date'),
    path('api/send-exp-to-telegram/', views.send_exp_to_telegram, name='send_exp_to_telegram'),
    # Reset data endpoints
    path('api/reset-exp-data/', views_reset_data.reset_exp_data, name='reset_exp_data'),
    path('api/reset-transfer-data/', views_reset_data.reset_transfer_data, name='reset_transfer_data'),
    path('api/reset-all-items/', views_reset_all_items.reset_all_items, name='reset_all_items'),
]
