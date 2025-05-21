from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import requests
import traceback
from .models import Item, ActivityLog, WebhookSettings

# Configure logging
logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def save_latest_price(request):
    """
    API endpoint to save latest price for an item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            latest_price = data.get('latest_price')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Update latest price
            if latest_price:
                try:
                    # Convert to float to validate, then to int to remove decimals
                    latest_price = float(latest_price)
                    item.latest_price = int(latest_price)
                    logger.info(f"Saving latest price for item {item.id}: {item.latest_price}")
                except ValueError:
                    logger.error(f"Invalid price format: {latest_price}")
                    return JsonResponse({'status': 'error', 'message': 'Invalid price format'})
            else:
                # Set latest price to 0 if empty to avoid NULL constraint issues
                item.latest_price = 0
                logger.info(f"Setting latest price to 0 for item {item.id}")
            
            # Save with transaction
            try:
                item.save(update_fields=['latest_price'])
                
                # Verify the save was successful by re-fetching
                refreshed_item = Item.objects.get(id=item_id)
                logger.info(f"Verification - Latest price after save: {refreshed_item.latest_price}")
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_latest_price',
                    status='success',
                    notes=f'Updated latest price for {item.name} to {item.latest_price}'
                )
                
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Latest price updated successfully',
                    'latest_price': str(refreshed_item.latest_price) if refreshed_item.latest_price is not None else ""
                })
            except Exception as e:
                logger.error(f"Error saving item: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': f'Error saving: {str(e)}'})
            
        except Item.DoesNotExist:
            logger.error(f"Item not found: {item_id}")
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in save_latest_price view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def send_price_to_telegram(request):
    """
    API endpoint to send price notification to Telegram
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get webhook settings
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings:
                return JsonResponse({'status': 'error', 'message': 'Webhook settings not found'})
            
            webhook_url = webhook_settings.webhook_kelola_harga
            if not webhook_url:
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Get items
            items = Item.objects.filter(id__in=item_ids)
            
            # Prepare message
            message = f"💰 Daftar Harga Produk:\n\n"
            
            for item in items:
                message += f"*{item.name}*\n"
                message += f"Kode: {item.code}\n"
                message += f"Kategori: {item.category}\n"
                
                # Use Harga Terbaru if available, otherwise fallback to Harga Saat Ini
                if item.latest_price is not None:
                    message += f"Harga: Rp {int(item.latest_price):,}\n"
                    logger.info(f"Using latest_price for item {item.id}: {item.latest_price}")
                else:
                    message += f"Harga: Rp {int(item.selling_price):,}\n"
                    logger.info(f"Using selling_price for item {item.id}: {item.selling_price}")
                
                message += "\n"
            
            # Send to webhook
            logger.info(f"Sending to webhook: {webhook_url}")
            response = requests.post(
                webhook_url,
                json={'text': message, 'parse_mode': 'Markdown'},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_price_to_telegram',
                    status='success',
                    notes=f'Sent price notification for {len(items)} items to Telegram'
                )
                
                return JsonResponse({'status': 'success', 'message': 'Notification sent to Telegram'})
            else:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_price_to_telegram',
                    status='failed',
                    notes=f'Failed to send price notification to Telegram: {response.text}'
                )
                
                return JsonResponse({'status': 'error', 'message': f'Failed to send notification: {response.text}'})
            
        except Exception as e:
            logger.error(f"Error in send_price_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
