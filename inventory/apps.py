from django.apps import AppConfig
import os


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    
    def ready(self):
        """
        Create necessary directories for media storage when the app starts
        """
        from django.conf import settings
        
        # Create upload and backup directories if they don't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.BACKUP_DIR, exist_ok=True)
