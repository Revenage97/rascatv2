from django.urls import path
from . import views
from .views_reset_data import reset_exp_data, reset_transfer_data
from .views_reset_all_items import reset_all_items
from .views_save_latest_price import save_latest_price, send_price_to_telegram
from .views_upload_file import upload_file
from .views_update_min_stock import update_min_stock, delete_min_stock
from .views_update_transfer_stock import update_transfer_stock, delete_transfer_stock, send_transfer_to_telegram
from .views_update_expiry_date import save_expiry_date, send_exp_to_telegram
from .views_send_to_telegram import send_to_telegram
from .views_timezone import timezone_settings
from .views_packing import (
    kelola_stok_packing, update_packing_min_stock, delete_packing_min_stock,
    send_packing_to_telegram, reset_all_packing_items, create_packing_item,
    update_packing_item, delete_packing_item
)
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
    path('kelola-stok-packing/', kelola_stok_packing, name='kelola_stok_packing'),
    path('pesanan-dibatalkan/', views.pesanan_dibatalkan, name='pesanan_dibatalkan'), # Added new route
    path('transfer-stok/', views.transfer_stok, name='transfer_stok'),
    path('data-exp-produk/', views.data_exp_produk, name='data_exp_produk'),
    path('upload/', upload_file, name='upload_file'),
    path('change-password/', views.change_password, name='change_password'),
    path('webhook-settings/', views.webhook_settings, name='webhook_settings'),
    path('timezone-settings/', timezone_settings, name='timezone_settings'),
    path('kelola-pengguna/', views.kelola_pengguna, name='kelola_pengguna'),
    path("edit-user/<int:user_id>/", views.edit_pengguna, name="edit_user"),
    path("delete-user/<int:user_id>/", views.delete_pengguna, name="delete_user"),
    path("send-cancelled-order-telegram/<int:order_id>/", views.send_cancelled_order_telegram, name="send_cancelled_order_telegram"), # Added URL for sending cancelled order to Telegram
    path("activity-logs/", views.activity_logs, name="activity_logs"),
    
    # API endpoints for expiry date
    path('api/save-expiry-date/', save_expiry_date, name='save_expiry_date'),
    path('api/delete-expiry-date/', save_expiry_date, name='delete_expiry_date'),  # Reusing same view with different param
    path('api/send-exp-to-telegram/', send_exp_to_telegram, name='send_exp_to_telegram'),
    
    # API endpoints for minimum stock
    path('api/update-min-stock/', update_min_stock, name='update_min_stock'),
    path('api/delete-min-stock/', delete_min_stock, name='delete_min_stock'),
    
    # API endpoints for transfer stock
    path('api/update-transfer-stock/', update_transfer_stock, name='update_transfer_stock'),
    path('api/delete-transfer-stock/', delete_transfer_stock, name='delete_transfer_stock'),
    path('api/send-transfer-to-telegram/', send_transfer_to_telegram, name='send_transfer_to_telegram'),
    
    # Reset data endpoints
    path('api/reset-exp-data/', reset_exp_data, name='reset_exp_data'),
    path('api/reset-transfer-data/', reset_transfer_data, name='reset_transfer_data'),
    path('api/reset-all-items/', reset_all_items, name='reset_all_items'),
       # API endpoints for latest price
    path('api/save-latest-price/', save_latest_price, name='save_latest_price'),
    path('api/delete-latest-price/', save_latest_price, name='delete_latest_price'),  # Reusing same view with different param
    path('api/send-price-to-telegram/', send_price_to_telegram, name='send_price_to_telegram'),   
    # Dashboard send to telegram endpoint
    path('api/send-to-telegram/', send_to_telegram, name='send_to_telegram'),
    
    # Packing item endpoints
    path('api/update-packing-min-stock/', update_packing_min_stock, name='update_packing_min_stock'),
    path('api/delete-packing-min-stock/', delete_packing_min_stock, name='delete_packing_min_stock'),
    path('api/send-packing-to-telegram/', send_packing_to_telegram, name='send_packing_to_telegram'),
    path('api/reset-all-packing-items/', reset_all_packing_items, name='reset_all_packing_items'),
    path('api/create-packing-item/', create_packing_item, name='create_packing_item'),
    path('api/update-packing-item/', update_packing_item, name='update_packing_item'),
    path('api/delete-packing-item/', delete_packing_item, name='delete_packing_item'),
]

