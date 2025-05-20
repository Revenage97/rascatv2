from django.apps import AppConfig
import os
import glob


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    
    def ready(self):
        """
        Create necessary directories for media storage when the app starts
        and clean up existing files in uploads and backups folders
        """
        from django.conf import settings
        
        # Create media directory if it doesn't exist
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Auto-cleanup function to remove all files in uploads and backups folders
        def cleanup_folder(folder_path):
            if os.path.exists(folder_path):
                # Get all files in the folder
                files = glob.glob(os.path.join(folder_path, '*'))
                for file_path in files:
                    # Only remove files, not directories
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            print(f"Deleted file: {file_path}")
                        except Exception as e:
                            print(f"Error deleting {file_path}: {str(e)}")
        
        # Clean up uploads folder
        uploads_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(uploads_path, exist_ok=True)
        cleanup_folder(uploads_path)
        
        # Clean up backups folder
        backups_path = os.path.join(settings.MEDIA_ROOT, 'backups')
        os.makedirs(backups_path, exist_ok=True)
        cleanup_folder(backups_path)
