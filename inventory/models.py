from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff_gudang', 'Staff Gudang'),
        ('manajer', 'Manajer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, verbose_name="Nama Lengkap")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff_gudang', verbose_name="Role/Akses")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_staff_gudang(self):
        return self.role == 'staff_gudang'
    
    @property
    def is_manajer(self):
        return self.role == 'manajer'

class Item(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Kode Barang")
    name = models.CharField(max_length=255, verbose_name="Nama Barang")
    category = models.CharField(max_length=100, verbose_name="Kategori")
    current_stock = models.IntegerField(default=0, verbose_name="Stok Saat Ini")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Harga Jual")
    latest_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Harga Terbaru")
    minimum_stock = models.IntegerField(default=0, verbose_name="Stok Minimum")
    transfer_stock = models.IntegerField(default=0, null=True, blank=True, verbose_name="Stok Transfer")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Expired")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']
        verbose_name = "Item"
        verbose_name_plural = "Items"


class PackingItem(models.Model):
    """
    Model for Kelola Stok Packing items, independent from regular inventory items.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name="Kode Barang")
    name = models.CharField(max_length=255, verbose_name="Nama Barang")
    category = models.CharField(max_length=100, verbose_name="Kategori")
    current_stock = models.IntegerField(default=0, verbose_name="Stok Saat Ini")
    minimum_stock = models.IntegerField(default=0, verbose_name="Stok Minimum")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']
        verbose_name = "Packing Item"
        verbose_name_plural = "Packing Items"


class WebhookSettings(models.Model):
    telegram_webhook_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Webhook Telegram")
    webhook_kelola_stok = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Webhook Telegram - Kelola Stok")
    webhook_transfer_stok = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Webhook Telegram - Transfer Stok")
    webhook_data_exp_produk = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Webhook Telegram - Data Exp Produk")
    webhook_kelola_harga = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Webhook Telegram - Kelola Harga")
    webhook_kelola_stok_packing = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Webhook Telegram - Kelola Stok Packing")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Webhook Settings (Last updated: {self.updated_at})"

    class Meta:
        verbose_name = "Webhook Setting"
        verbose_name_plural = "Webhook Settings"


class SystemSettings(models.Model):
    """
    Model for storing system-wide settings like timezone
    """
    timezone = models.CharField(max_length=50, default="Asia/Jakarta", verbose_name="Zona Waktu")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"System Settings (Last updated: {self.updated_at})"

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"


class ActivityLog(models.Model):
    STATUS_CHOICES = (
        ('success', 'Berhasil'),
        ('failed', 'Gagal'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="User")
    action = models.CharField(max_length=255, verbose_name="Aksi")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success', verbose_name="Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Waktu")

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.action} - {self.status}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"


class UploadHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="User")
    filename = models.CharField(max_length=255, verbose_name="Nama File")
    file_path = models.CharField(max_length=500, verbose_name="Path File")
    file_size = models.IntegerField(default=0, verbose_name="Ukuran File (bytes)")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Upload")
    success_count = models.IntegerField(default=0, verbose_name="Jumlah Item Berhasil")
    error_count = models.IntegerField(default=0, verbose_name="Jumlah Item Gagal")
    
    def __str__(self):
        return f"{self.filename} - {self.upload_date}"
    
    def get_file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Upload History"
        verbose_name_plural = "Upload Histories"



class CancelledOrder(models.Model):
    """
    Model to store cancelled order details.
    """
    order_number = models.CharField(max_length=100, verbose_name="Nomor Pesanan")
    order_date = models.DateField(verbose_name="Tanggal Pemesanan")
    cancellation_date = models.DateField(verbose_name="Tanggal Pembatalan")
    product_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Produk") # Optional
    quantity = models.PositiveIntegerField(verbose_name="Jumlah")
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="Alasan Pembatalan")
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="User Input") # Track who added it

    def __str__(self):
        return f"Cancelled Order: {self.order_number} - {self.product_name or 'N/A'}"

    class Meta:
        ordering = [
            '-cancellation_date', 
            '-created_at'
        ] # Default order: newest cancellation first
        verbose_name = "Pesanan Dibatalkan"
        verbose_name_plural = "Pesanan Dibatalkan"

