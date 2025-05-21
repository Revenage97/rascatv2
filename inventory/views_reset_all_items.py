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
    View for resetting only the manual fields (minimum_stock) for all items
    Only accessible by admin users
    """
    if request.method == 'POST':
        try:
            # Count items before reset for logging
            item_count = Item.objects.count()
            
            # Reset only the minimum_stock field, not deleting the items
            Item.objects.all().update(minimum_stock=0)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_minimum_stock',
                status='success',
                notes=f'Reset minimum stock data for {item_count} items'
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': f'Successfully reset minimum stock for {item_count} items',
                'count': item_count
            })
            
        except Exception as e:
            logger.error(f"Error in reset_all_items view: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_minimum_stock',
                status='failed',
                notes=f'Failed to reset minimum stock: {str(e)}'
            )
            
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
