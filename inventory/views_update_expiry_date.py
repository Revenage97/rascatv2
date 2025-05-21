from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import traceback
import requests
from datetime import datetime
from .models import Item, ActivityLog, WebhookSettings

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
            
            # Get webhook settings
            webhook_settings, created = WebhookSettings.objects.get_or_create(pk=1)
            webhook_url = webhook_settings.webhook_data_exp_produk
            
            if not webhook_url:
                logger.error("Webhook URL for Data Exp Produk not configured")
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'}, status=400)
            
            # Get items
            items = Item.objects.filter(id__in=item_ids)
            
            # Send to Telegram
            success_count = 0
            error_count = 0
            error_messages = []
            
            for item in items:
                # Format message
                message = f"📦 Produk Expired:\n"
                message += f"Nama: {item.name}\n"
                
                if item.expiry_date:
                    message += f"Exp: {item.expiry_date.strftime('%Y-%m-%d')}\n"
                else:
                    message += f"Exp: Tidak diatur\n"
                    
                message += f"Stok: {item.current_stock}\n"
                
                # Send to webhook
                try:
                    response = requests.post(
                        webhook_url,
                        json={'text': message, 'parse_mode': 'Markdown'},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        logger.info(f"Successfully sent item {item.id} expiry notification to Telegram")
                        
                        # Log activity
                        ActivityLog.objects.create(
                            user=request.user,
                            action='send_exp_to_telegram',
                            status='success',
                            notes=f'Sent expiry notification for {item.name} (ID: {item.id}) to Telegram'
                        )
                    else:
                        error_count += 1
                        error_message = f"Failed to send item {item.id} to Telegram: {response.status_code} {response.text}"
                        error_messages.append(error_message)
                        logger.error(error_message)
                        
                        # Log activity
                        ActivityLog.objects.create(
                            user=request.user,
                            action='send_exp_to_telegram',
                            status='error',
                            notes=f'Failed to send expiry notification for {item.name} (ID: {item.id}) to Telegram: {response.status_code}'
                        )
                except Exception as e:
                    error_count += 1
                    error_message = f"Error sending item {item.id} to Telegram: {str(e)}"
                    error_messages.append(error_message)
                    logger.error(error_message)
                    logger.error(traceback.format_exc())
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_exp_to_telegram',
                        status='error',
                        notes=f'Error sending expiry notification for {item.name} (ID: {item.id}) to Telegram: {str(e)}'
                    )
            
            # Return response
            if success_count > 0 and error_count == 0:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Successfully sent {success_count} item(s) to Telegram'
                })
            elif success_count > 0 and error_count > 0:
                return JsonResponse({
                    'status': 'partial',
                    'message': f'Sent {success_count} item(s) to Telegram, but failed to send {error_count} item(s)',
                    'errors': error_messages
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to send all {error_count} item(s) to Telegram',
                    'errors': error_messages
                }, status=500)
            
        except Exception as e:
            logger.error(f"Error in send_exp_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
