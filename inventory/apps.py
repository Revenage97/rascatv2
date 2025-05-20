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
        
        # Create media directory if it doesn't exist
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
