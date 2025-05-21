from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import traceback
from datetime import datetime
from .models import Item, ActivityLog

# Configure logging
logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def save_expiry_date(request):
    """
    API endpoint to save expiry date for an item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            expiry_date = data.get('expiry_date')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Update expiry date
            if expiry_date:
                try:
                    # Parse date string to date object
                    expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                    item.expiry_date = expiry_date_obj
                    logger.info(f"Saving expiry date for item {item.id}: {expiry_date}")
                except ValueError:
                    logger.error(f"Invalid date format: {expiry_date}")
                    return JsonResponse({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'})
            else:
                # Clear expiry date if empty
                item.expiry_date = None
                logger.info(f"Clearing expiry date for item {item.id}")
            
            # Save with transaction
            try:
                item.save(update_fields=['expiry_date'])
                
                # Verify the save was successful by re-fetching
                refreshed_item = Item.objects.get(id=item_id)
                logger.info(f"Verification - Expiry date after save: {refreshed_item.expiry_date}")
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_expiry_date',
                    status='success',
                    notes=f'Updated expiry date for {item.name} to {item.expiry_date}'
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Expiry date updated successfully',
                    'expiry_date': expiry_date
                })
            except Exception as e:
                logger.error(f"Error saving item: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': f'Error saving: {str(e)}'})
            
        except Item.DoesNotExist:
            logger.error(f"Item not found: {item_id}")
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in save_expiry_date view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def send_exp_to_telegram(request):
    """
    API endpoint to send expiry notification to Telegram
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get items
            items = Item.objects.filter(id__in=item_ids)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='send_exp_to_telegram',
                status='success',
                notes=f'Sent expiry notification for {len(items)} items to Telegram'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Notification sent to Telegram'})
            
        except Exception as e:
            logger.error(f"Error in send_exp_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
