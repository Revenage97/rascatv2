from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import traceback
from .models import Item, ActivityLog

# Configure logging
logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def update_min_stock(request):
    """
    API endpoint to update minimum stock for an item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            min_stock = data.get('min_stock')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Update minimum stock
            if min_stock is not None:
                try:
                    # Convert to integer
                    min_stock = int(min_stock)
                    item.minimum_stock = min_stock
                    logger.info(f"Updating minimum stock for item {item.id}: {min_stock}")
                except ValueError:
                    logger.error(f"Invalid minimum stock format: {min_stock}")
                    return JsonResponse({'status': 'error', 'message': 'Invalid minimum stock format'})
            else:
                # Clear minimum stock if empty
                item.minimum_stock = None
                logger.info(f"Clearing minimum stock for item {item.id}")
            
            # Save with transaction
            try:
                item.save(update_fields=['minimum_stock'])
                
                # Verify the save was successful by re-fetching
                refreshed_item = Item.objects.get(id=item_id)
                logger.info(f"Verification - Minimum stock after save: {refreshed_item.minimum_stock}")
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_min_stock',
                    status='success',
                    notes=f'Updated minimum stock for {item.name} to {item.minimum_stock}'
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Minimum stock updated successfully',
                    'min_stock': refreshed_item.minimum_stock
                })
            except Exception as e:
                logger.error(f"Error saving item: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': f'Error saving: {str(e)}'})
            
        except Item.DoesNotExist:
            logger.error(f"Item not found: {item_id}")
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in update_min_stock view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_min_stock(request):
    """
    API endpoint to delete minimum stock for an item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Clear minimum stock
            item.minimum_stock = None
            logger.info(f"Deleting minimum stock for item {item.id}")
            
            # Save with transaction
            try:
                item.save(update_fields=['minimum_stock'])
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='delete_min_stock',
                    status='success',
                    notes=f'Deleted minimum stock for {item.name}'
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Minimum stock deleted successfully'
                })
            except Exception as e:
                logger.error(f"Error saving item: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': f'Error saving: {str(e)}'})
            
        except Item.DoesNotExist:
            logger.error(f"Item not found: {item_id}")
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in delete_min_stock view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
