from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
import requests
import logging
import traceback
from .models import PackingItem, WebhookSettings, ActivityLog
from .utils import is_admin, is_staff_gudang
from .views_timezone import get_localized_time, format_datetime

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def kelola_stok_packing(request):
    """
    View for Kelola Stok Packing page - displays packing items with their stock
    """
    # Enhanced logging for debugging user role issues
    logger.info(f"Accessing kelola_stok_packing view as user: {request.user.username}")
    
    # Explicitly check and log staff gudang status
    is_staff = False
    try:
        is_staff = request.user.profile.is_staff_gudang
        logger.info(f"User {request.user.username} staff_gudang status: {is_staff}")
    except Exception as e:
        logger.error(f"Error checking staff_gudang for {request.user.username}: {str(e)}")
    
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    filter_option = request.GET.get('filter', '')
    
    items = PackingItem.objects.all()
    
    # Search functionality
    if query:
        items = items.filter(
            Q(name__icontains=query) | 
            Q(code__icontains=query) | 
            Q(category__icontains=query)
        )
    
    # Sorting functionality
    if sort == 'name':
        items = items.order_by('name')
    elif sort == 'name_desc':
        items = items.order_by('-name')
    elif sort == 'category':
        items = items.order_by('category')
    elif sort == 'category_desc':
        items = items.order_by('-category')
    elif sort == 'stock_asc':
        items = items.order_by('current_stock')
    elif sort == 'stock_desc':
        items = items.order_by('-current_stock')
    
    # Filtering functionality
    if filter_option == 'low_stock':
        items = [item for item in items if item.minimum_stock and item.current_stock < item.minimum_stock]
    
    # Explicitly set staff_gudang status in context
    is_admin_user = is_admin(request.user)
    is_staff_gudang_user = is_staff_gudang(request.user)
    
    logger.info(f"Setting context for {request.user.username}: is_admin={is_admin_user}, is_staff_gudang={is_staff_gudang_user}")
    
    context = {
        'items': items,
        'query': query,
        'is_admin': is_admin_user,
        'is_staff_gudang': is_staff_gudang_user,
    }
    
    return render(request, 'inventory/kelola_stok_packing.html', context)

@login_required
@csrf_exempt
def update_packing_min_stock(request):
    """
    API endpoint to update minimum stock for a packing item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            min_stock = data.get('min_stock')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = PackingItem.objects.get(id=item_id)
            
            # Update minimum stock
            if min_stock is not None:
                try:
                    min_stock = int(min_stock)
                    item.minimum_stock = min_stock
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid minimum stock value'})
            else:
                # Set minimum stock to 0 if empty or null (not NULL)
                item.minimum_stock = 0
            
            item.save(update_fields=['minimum_stock'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_packing_min_stock',
                status='success',
                notes=f'Updated minimum stock for {item.name} to {min_stock}'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Minimum stock updated successfully'})
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in update_packing_min_stock view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_packing_min_stock(request):
    """
    API endpoint to delete minimum stock for a packing item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = PackingItem.objects.get(id=item_id)
            
            # Clear minimum stock (set to 0, not NULL)
            item.minimum_stock = 0
            item.save(update_fields=['minimum_stock'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_packing_min_stock',
                status='success',
                notes=f'Deleted minimum stock for {item.name}'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Minimum stock deleted successfully'})
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in delete_packing_min_stock view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def send_packing_to_telegram(request):
    """
    API endpoint to send pre-formatted packing notification text to Telegram webhook
    """
    logger.info(f"Accessing send_packing_to_telegram as user: {request.user.username}")
    
    if request.method == 'POST':
        try:
            # Read the plain text message directly from the request body
            message_text = request.body.decode('utf-8')
            logger.info(f"Received plain text message for Telegram: \n{message_text}")

            if not message_text:
                return JsonResponse({'status': 'error', 'message': 'Pesan kosong diterima'})

            # Get webhook URL for Kelola Stok Packing
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings:
                logger.error("Webhook settings not found")
                return JsonResponse({'status': 'error', 'message': 'Pengaturan webhook tidak ditemukan'})
            
            webhook_url = webhook_settings.webhook_kelola_stok_packing
            if not webhook_url:
                logger.error("Webhook URL for Kelola Stok Packing not configured")
                return JsonResponse({'status': 'error', 'message': 'URL webhook Telegram untuk Kelola Stok Packing belum diatur'})
            
            # Send the received plain text message to the webhook as JSON with a 'text' field
            response = requests.post(
                webhook_url,
                json={'text': message_text}, # Send as JSON with 'text' field
                headers={'Content-Type': 'application/json'}, # Set content type to JSON
                timeout=10 # Add a timeout
            )
            
            # Check response status code, but don't assume JSON response from webhook
            if response.status_code == 200:
                logger.info(f"Successfully sent packing notification to webhook for user {request.user.username}. Webhook response status: {response.status_code}")
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_packing_to_telegram',
                    status='success',
                    notes=f'Sent packing notification text to Telegram webhook.'
                )
                # Return JSON success to frontend, regardless of webhook response body
                return JsonResponse({'status': 'success', 'message': 'Notifikasi berhasil dikirim ke Telegram'})
            else:
                # Log error with webhook response text (which might not be JSON)
                logger.error(f"Failed to send packing notification to webhook. Status: {response.status_code}, Response: {response.text}")
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_packing_to_telegram',
                    status='failed',
                    notes=f'Failed to send packing notification to Telegram webhook: {response.status_code} - {response.text}'
                )
                # Return JSON error to frontend
                return JsonResponse({'status': 'error', 'message': f'Gagal mengirim notifikasi: {response.status_code} - {response.text}'})
            
        except Exception as e:
            logger.error(f"Error in send_packing_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='send_packing_to_telegram',
                status='failed',
                notes=f'Internal server error: {str(e)}'
            )
            return JsonResponse({'status': 'error', 'message': f'Terjadi kesalahan internal: {str(e)}'})
    
    logger.warning(f"Invalid request method ({request.method}) for send_packing_to_telegram")
    return JsonResponse({'status': 'error', 'message': 'Metode request tidak valid'})

@login_required
@user_passes_test(is_admin)
@csrf_exempt
def reset_all_packing_items(request):
    """
    API endpoint to reset all packing items
    """
    if request.method == 'POST':
        try:
            # Delete all packing items
            count = PackingItem.objects.all().count()
            PackingItem.objects.all().delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_all_packing_items',
                status='success',
                notes=f'Reset all packing items ({count} items deleted)'
            )
            
            return JsonResponse({'status': 'success', 'message': f'All packing items reset successfully ({count} items deleted)'})
            
        except Exception as e:
            logger.error(f"Error in reset_all_packing_items view: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_all_packing_items',
                status='failed',
                notes=f'Failed to reset all packing items: {str(e)}'
            )
            
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
# @user_passes_test(is_admin) # Removed admin check to allow staff gudang access
@csrf_exempt
def create_packing_item(request):
    """
    API endpoint to create a new packing item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            name = data.get('name')
            category = data.get('category')
            current_stock = data.get('current_stock')
            minimum_stock = data.get('minimum_stock')
            
            # Validate required fields
            if not code or not name or current_stock is None:
                return JsonResponse({'status': 'error', 'message': 'Code, name, and current stock are required'})
            
            # Create new item
            item = PackingItem.objects.create(
                code=code,
                name=name,
                category=category or '',
                current_stock=current_stock,
                minimum_stock=minimum_stock
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='create_packing_item',
                status='success',
                notes=f'Created new packing item: {item.name}'
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Packing item created successfully',
                'item': {
                    'id': item.id,
                    'code': item.code,
                    'name': item.name,
                    'category': item.category,
                    'current_stock': item.current_stock,
                    'minimum_stock': item.minimum_stock
                }
            })
            
        except Exception as e:
            logger.error(f"Error in create_packing_item view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def update_packing_item(request):
    """
    API endpoint to update an existing packing item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            code = data.get('code')
            name = data.get('name')
            category = data.get('category')
            current_stock = data.get('current_stock')
            minimum_stock = data.get('minimum_stock')
            
            # Validate required fields
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Get item
            item = PackingItem.objects.get(id=item_id)
            
            # Update fields
            if code is not None:
                item.code = code
            if name is not None:
                item.name = name
            if category is not None:
                item.category = category
            if current_stock is not None:
                item.current_stock = current_stock
            if minimum_stock is not None:
                item.minimum_stock = minimum_stock
            
            item.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_packing_item',
                status='success',
                notes=f'Updated packing item: {item.name}'
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Packing item updated successfully',
                'item': {
                    'id': item.id,
                    'code': item.code,
                    'name': item.name,
                    'category': item.category,
                    'current_stock': item.current_stock,
                    'minimum_stock': item.minimum_stock
                }
            })
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in update_packing_item view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_packing_item(request):
    """
    API endpoint to delete a packing item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Get item
            item = PackingItem.objects.get(id=item_id)
            item_name = item.name
            
            # Delete item
            item.delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_packing_item',
                status='success',
                notes=f'Deleted packing item: {item_name}'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Packing item deleted successfully'})
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in delete_packing_item view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
