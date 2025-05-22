from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SystemSettings, ActivityLog
import pytz
from django.utils import timezone
import logging
from datetime import datetime

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
        timezone_str = request.POST.get('timezone')
        
        # Validate timezone
        if timezone_str not in pytz.all_timezones:
            messages.error(request, f'Zona waktu tidak valid: {timezone_str}')
            return redirect('inventory:timezone_settings')
        
        # Save timezone setting
        system_settings.timezone = timezone_str
        system_settings.updated_by = request.user
        system_settings.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='update_timezone_settings',
            status='success',
            notes=f'Zona waktu diubah menjadi {timezone_str}'
        )
        
        messages.success(request, f'Pengaturan zona waktu berhasil disimpan: {timezone_str}')
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

def get_localized_time(dt=None):
    """
    Helper function to get the current time in the system timezone
    If dt is provided, it will be converted to the system timezone
    If dt is not provided, current time will be used
    Returns a timezone-aware datetime object
    """
    try:
        # Get the current timezone
        current_tz = get_current_timezone()
        
        # If no datetime is provided, use current time
        if dt is None:
            # Use timezone.now() which returns UTC time
            dt = timezone.now()
        
        # If the datetime is naive (no timezone info), assume it's in UTC
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
            
        # Convert to the current timezone
        return dt.astimezone(current_tz)
    except Exception as e:
        logger.error(f"Error localizing time: {str(e)}")
        # Return original datetime or current time as fallback
        return dt if dt else timezone.now()

def format_datetime(dt=None, format_str="%H:%M - %d %b %Y"):
    """
    Format a datetime object according to the specified format
    If dt is not provided, current localized time will be used
    Returns a formatted string
    """
    try:
        # Get localized time if dt is not provided
        if dt is None:
            dt = get_localized_time()
        else:
            # Ensure the datetime is localized
            dt = get_localized_time(dt)
            
        # Format the datetime
        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting datetime: {str(e)}")
        # Return current time as fallback
        return timezone.now().strftime(format_str)
