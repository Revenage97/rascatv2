from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SystemSettings, ActivityLog
import pytz
import logging

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def timezone_settings(request):
    """
    View for managing timezone settings
    """
    # Get or create system settings
    system_settings, created = SystemSettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        timezone = request.POST.get('timezone')
        
        # Validate timezone
        if timezone not in pytz.all_timezones:
            messages.error(request, f'Zona waktu tidak valid: {timezone}')
            return redirect('inventory:timezone_settings')
        
        # Save timezone setting
        system_settings.timezone = timezone
        system_settings.updated_by = request.user
        system_settings.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='update_timezone_settings',
            status='success',
            notes=f'Zona waktu diubah menjadi {timezone}'
        )
        
        messages.success(request, f'Pengaturan zona waktu berhasil disimpan: {timezone}')
        return redirect('inventory:timezone_settings')
    
    context = {
        'current_timezone': system_settings.timezone
    }
    
    return render(request, 'inventory/timezone_settings.html', context)

def get_current_timezone():
    """
    Helper function to get the current system timezone
    """
    try:
        system_settings = SystemSettings.objects.first()
        if system_settings and system_settings.timezone:
            return pytz.timezone(system_settings.timezone)
        return pytz.timezone('Asia/Jakarta')  # Default timezone
    except Exception as e:
        logger.error(f"Error getting timezone: {str(e)}")
        return pytz.timezone('Asia/Jakarta')  # Default timezone
