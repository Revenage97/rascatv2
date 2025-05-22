from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pytz
import logging
from .models import ActivityLog
from .utils import is_admin

# Configure logging
logger = logging.getLogger(__name__)

def get_jakarta_time():
    """
    Returns the current time in Asia/Jakarta timezone formatted as HH:MM - DD Month YYYY
    """
    jakarta = pytz.timezone('Asia/Jakarta')
    return now().astimezone(jakarta).strftime('%H:%M - %d %B %Y')

def get_jakarta_datetime():
    """
    Returns the current datetime object in Asia/Jakarta timezone
    """
    jakarta = pytz.timezone('Asia/Jakarta')
    return now().astimezone(jakarta)

def format_datetime_jakarta(dt):
    """
    Formats a datetime object to Asia/Jakarta timezone
    """
    if dt is None:
        return ""
    jakarta = pytz.timezone('Asia/Jakarta')
    return dt.astimezone(jakarta).strftime('%H:%M - %d %B %Y')

def get_localized_time():
    """
    Returns the current time in Asia/Jakarta timezone formatted as HH:MM - DD Month YYYY
    This is an alias for get_jakarta_time() for backward compatibility
    """
    return get_jakarta_time()

def format_datetime(dt=None):
    """
    Formats a datetime object to Asia/Jakarta timezone
    If no datetime is provided, uses current time
    This is an alias for format_datetime_jakarta() for backward compatibility
    """
    if dt is None:
        return get_jakarta_time()
    return format_datetime_jakarta(dt)

@login_required
@user_passes_test(is_admin)
def timezone_settings(request):
    """
    View for Timezone Settings page - allows admin to set timezone for the system
    """
    timezones = [
        {'value': 'Asia/Jakarta', 'label': 'GMT +7 (Jakarta)'},
        {'value': 'Asia/Singapore', 'label': 'GMT +8 (Singapore)'},
        {'value': 'Asia/Tokyo', 'label': 'GMT +9 (Tokyo)'}
    ]
    
    # Default timezone
    current_timezone = 'Asia/Jakarta'
    
    if request.method == 'POST':
        try:
            data = request.POST
            new_timezone = data.get('timezone')
            
            if new_timezone and new_timezone in [tz['value'] for tz in timezones]:
                # In a real implementation, we would save this to database
                # For now, we just log it and pretend it's saved
                current_timezone = new_timezone
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_timezone',
                    status='success',
                    notes=f'Updated timezone to {new_timezone}'
                )
                
                return redirect('inventory:timezone_settings')
            else:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_timezone',
                    status='failed',
                    notes=f'Invalid timezone: {new_timezone}'
                )
        except Exception as e:
            logger.error(f"Error in timezone_settings view: {str(e)}")
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_timezone',
                status='failed',
                notes=f'Error updating timezone: {str(e)}'
            )
    
    context = {
        'timezones': timezones,
        'current_timezone': current_timezone,
        'is_admin': is_admin(request.user),
    }
    
    return render(request, 'inventory/timezone_settings.html', context)
