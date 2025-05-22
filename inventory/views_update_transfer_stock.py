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
def update_transfer_stock(request):
    """
    API endpoint to update transfer stock for an item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            transfer_stock = data.get('transfer_stock')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Update transfer stock
            if transfer_stock is not None:
                try:
                    # Convert to integer
                    transfer_stock = int(transfer_stock)
                    item.transfer_stock = transfer_stock
                    logger.info(f"Updating transfer stock for item {item.id}: {transfer_stock}")
                except ValueError:
                    logger.error(f"Invalid transfer stock format: {transfer_stock}")
                    return JsonResponse({'status': 'error', 'message': 'Invalid transfer stock format'})
            else:
                # Clear transfer stock if empty
                item.transfer_stock = None
                logger.info(f"Clearing transfer stock for item {item.id}")
            
            # Save with transaction
            try:
                item.save(update_fields=['transfer_stock'])
                
                # Verify the save was successful by re-fetching
                refreshed_item = Item.objects.get(id=item_id)
                logger.info(f"Verification - Transfer stock after save: {refreshed_item.transfer_stock}")
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_transfer_stock',
                    status='success',
                    notes=f'Updated transfer stock for {item.name} to {item.transfer_stock}'
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Transfer stock updated successfully',
                    'transfer_stock': refreshed_item.transfer_stock
                })
            except Exception as e:
                logger.error(f"Error saving item: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': f'Error saving: {str(e)}'})
            
        except Item.DoesNotExist:
            logger.error(f"Item not found: {item_id}")
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in update_transfer_stock view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_transfer_stock(request):
    """
    API endpoint to delete transfer stock for an item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Clear transfer stock
            item.transfer_stock = None
            logger.info(f"Deleting transfer stock for item {item.id}")
            
            # Save with transaction
            try:
                item.save(update_fields=['transfer_stock'])
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='delete_transfer_stock',
                    status='success',
                    notes=f'Deleted transfer stock for {item.name}'
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Transfer stock deleted successfully'
                })
            except Exception as e:
                logger.error(f"Error saving item: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': f'Error saving: {str(e)}'})
            
        except Item.DoesNotExist:
            logger.error(f"Item not found: {item_id}")
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in delete_transfer_stock view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def send_transfer_to_telegram(request):
    """
    API endpoint to send transfer notification to Telegram
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get items
            items = Item.objects.filter(id__in=item_ids)
            
            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items found'})
            
            # Get asal and tujuan from localStorage (passed in request)
            asal = data.get('asal', 'Tidak Ditentukan')
            tujuan = data.get('tujuan', 'Tidak Ditentukan')
            
            # Format message in plain text (not JSON)
            message = f"🚚 Transfer Stok:\n"
            message += f"Asal: {asal}\n"
            message += f"Tujuan: {tujuan}\n\n"
            
            # Add items
            for item in items:
                if item.transfer_stock:
                    message += f"- {item.name} ({item.code}): {item.transfer_stock} Pcs\n"
            
            # Add footer note
            message += "\nTanpa konfirmasi - Cek Harga Dasar"
            
            # Get webhook settings
            from .models import WebhookSettings
            webhook_settings, created = WebhookSettings.objects.get_or_create(pk=1)
            webhook_url = webhook_settings.webhook_transfer_stok
            
            if not webhook_url:
                logger.error("Webhook URL for transfer stok not configured")
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Send to webhook as plain text
            import requests
            try:
                # Send as JSON with text field, not as plain text
                response = requests.post(
                    webhook_url,
                    json={'text': message},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent transfer notification to webhook")
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_transfer_to_telegram',
                        status='success',
                        notes=f'Sent transfer notification for {len(items)} items to Telegram'
                    )
                    
                    return JsonResponse({'status': 'success', 'message': 'Notification sent to Telegram'})
                else:
                    error_message = f"Failed to send transfer notification: {response.status_code} {response.text}"
                    logger.error(error_message)
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_transfer_to_telegram',
                        status='error',
                        notes=f'Failed to send transfer notification: {response.status_code}'
                    )
                    
                    return JsonResponse({'status': 'error', 'message': error_message})
            except Exception as e:
                error_message = f"Error sending transfer notification: {str(e)}"
                logger.error(error_message)
                logger.error(traceback.format_exc())
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_transfer_to_telegram',
                    status='error',
                    notes=f'Error sending transfer notification: {str(e)}'
                )
                
                return JsonResponse({'status': 'error', 'message': error_message})
            
        except Exception as e:
            logger.error(f"Error in send_transfer_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
