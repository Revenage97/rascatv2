from django.urls import path
from . import views
from .views_reset_data import reset_exp_data, reset_transfer_data
from .views_reset_all_items import reset_all_items
from .views_save_latest_price import save_latest_price, send_price_to_telegram
from .views_upload_file import upload_file
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
    path('upload/', upload_file, name='upload_file'),
    path('change-password/', views.change_password, name='change_password'),
    path('webhook-settings/', views.webhook_settings, name='webhook_settings'),
    path('kelola-pengguna/', views.kelola_pengguna, name='kelola_pengguna'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    path('api/save-expiry-date/', views.save_expiry_date, name='save_expiry_date'),
    path('api/send-exp-to-telegram/', views.send_exp_to_telegram, name='send_exp_to_telegram'),
    # Reset data endpoints
    path('api/reset-exp-data/', reset_exp_data, name='reset_exp_data'),
    path('api/reset-transfer-data/', reset_transfer_data, name='reset_transfer_data'),
    path('api/reset-all-items/', reset_all_items, name='reset_all_items'),
    # Save latest price endpoint
    path('api/save-latest-price/', save_latest_price, name='save_latest_price'),
    path('api/send-price-to-telegram/', send_price_to_telegram, name='send_price_to_telegram'),
]
