from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from .models import Item, ActivityLog
import logging
import traceback

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.profile.is_admin

@login_required
@user_passes_test(is_admin)
@csrf_exempt
def reset_all_items(request):
    """
    View for deleting all items from the database
    Only accessible by admin users
    """
    if request.method == 'POST':
        try:
            # Count items before deletion for logging
            item_count = Item.objects.count()
            
            # Delete all items
            Item.objects.all().delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_all_items',
                status='success',
                notes=f'Reset all items data ({item_count} items deleted)'
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': f'Successfully deleted all {item_count} items',
                'count': item_count
            })
            
        except Exception as e:
            logger.error(f"Error in reset_all_items view: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_all_items',
                status='failed',
                notes=f'Failed to reset all items: {str(e)}'
            )
            
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
