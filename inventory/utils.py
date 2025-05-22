from django.utils.timezone import now
import pytz

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
