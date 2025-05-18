from django.contrib import admin
from .models import Item, WebhookSettings, ActivityLog

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'current_stock', 'selling_price', 'minimum_stock')
    search_fields = ('code', 'name', 'category')
    list_filter = ('category',)

@admin.register(WebhookSettings)
class WebhookSettingsAdmin(admin.ModelAdmin):
    list_display = ('telegram_webhook_url', 'updated_at', 'updated_by')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'status', 'timestamp')
    list_filter = ('user', 'status', 'timestamp')
    search_fields = ('action', 'notes')
