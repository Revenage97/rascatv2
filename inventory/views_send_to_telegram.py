from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging
import requests
import traceback
from .models import Item, WebhookSettings, ActivityLog

# Configure logging
logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def send_to_telegram(request):
    """
    View for sending item data to Telegram via webhook
    Supports both single item and multiple items
    """
    try:
        logger.info("Accessing send_to_telegram view")
        
        if request.method != 'POST':
            logger.warning("Method not allowed: %s", request.method)
            return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
        # Parse request body
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            logger.info(f"Received request to send items to Telegram: {item_ids}")
            
            if not item_ids:
                logger.warning("No item IDs provided")
                return JsonResponse({'status': 'error', 'message': 'No item IDs provided'}, status=400)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
        # Get webhook settings
        webhook_settings, created = WebhookSettings.objects.get_or_create(pk=1)
        webhook_url = webhook_settings.webhook_kelola_stok
        
        if not webhook_url:
            logger.error("Webhook URL not configured")
            return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'}, status=400)
        
        # Get items
        items = Item.objects.filter(id__in=item_ids)
        if not items:
            logger.warning(f"No items found with IDs: {item_ids}")
            return JsonResponse({'status': 'error', 'message': 'No items found'}, status=404)
        
        # Send to Telegram
        success_count = 0
        error_count = 0
        error_messages = []
        
        for item in items:
            # Format message
            message = f"📦 Stok Barang:\n"
            message += f"Kode: {item.code}\n"
            message += f"Nama: {item.name}\n"
            message += f"Kategori: {item.category}\n"
            message += f"Stok: {item.current_stock}\n"
            
            if item.minimum_stock is not None:
                message += f"Stok Minimum: {item.minimum_stock}\n"
            
            if item.selling_price:
                # Format price with thousand separator
                price_str = f"{item.selling_price:,.0f}".replace(",", ".")
                message += f"Harga: Rp {price_str}\n"
            
            # Send to webhook
            try:
                response = requests.post(
                    webhook_url,
                    json={'text': message},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                    logger.info(f"Successfully sent item {item.id} to Telegram")
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_to_telegram',
                        status='success',
                        notes=f'Sent item {item.name} (ID: {item.id}) to Telegram'
                    )
                else:
                    error_count += 1
                    error_message = f"Failed to send item {item.id} to Telegram: {response.status_code} {response.text}"
                    error_messages.append(error_message)
                    logger.error(error_message)
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_to_telegram',
                        status='error',
                        notes=f'Failed to send item {item.name} (ID: {item.id}) to Telegram: {response.status_code}'
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
                    action='send_to_telegram',
                    status='error',
                    notes=f'Error sending item {item.name} (ID: {item.id}) to Telegram: {str(e)}'
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
        logger.error(f"Unexpected error in send_to_telegram view: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=500)
