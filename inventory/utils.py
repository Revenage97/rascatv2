from django.utils.timezone import now
import pytz
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Role checking functions
def is_admin(user):
    """
    Check if user has admin role
    """
    try:
        return user.profile.is_admin
    except:
        return False

def is_staff_gudang(user):
    """
    Check if user has staff_gudang role
    """
    try:
        # Add logging to debug role checking
        logger.info(f"Checking staff_gudang role for user {user.username}: {user.profile.is_staff_gudang}")
        return user.profile.is_staff_gudang
    except Exception as e:
        logger.error(f"Error checking staff_gudang role: {str(e)}")
        return False

def is_manajer(user):
    """
    Check if user has manajer role
    """
    try:
        return user.profile.is_manajer
    except:
        return False

# Timezone helper functions
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
