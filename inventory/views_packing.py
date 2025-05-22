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
from .utils import is_admin
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
    API endpoint to send packing item notification to Telegram
    """
    # Enhanced logging for debugging user role issues
    logger.info(f"Accessing send_packing_to_telegram as user: {request.user.username}")
    
    # Explicitly check and log staff gudang status
    try:
        is_staff = request.user.profile.is_staff_gudang
        is_admin_user = is_admin(request.user)
        logger.info(f"User {request.user.username} roles: staff_gudang={is_staff}, admin={is_admin_user}")
    except Exception as e:
        logger.error(f"Error checking roles for {request.user.username}: {str(e)}")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            payment_method = data.get('payment_method')
            
            logger.info(f"Telegram request data: item_ids={item_ids}, payment_method={payment_method}")
            
            # Validate payment method only for admin users
            if is_admin(request.user) and not payment_method:
                logger.info(f"Admin user {request.user.username} missing payment method")
                return JsonResponse({'status': 'error', 'message': 'Metode pembayaran diperlukan'})
            
            # For staff gudang, use default payment method
            if not is_admin(request.user) or is_staff_gudang(request.user):
                payment_method = "DEFAULT"
                logger.info(f"Using DEFAULT payment method for user {request.user.username}")
            
            # Handle both single item_id and array of item_ids
            if not item_ids:
                item_id = data.get('item_id')
                if item_id:
                    item_ids = [item_id]
                else:
                    return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Ensure item_ids is always a list
            if not isinstance(item_ids, list):
                item_ids = [item_ids]
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get webhook URL
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings:
                return JsonResponse({'status': 'error', 'message': 'Webhook settings not found'})
            
            webhook_url = webhook_settings.webhook_kelola_stok_packing
            if not webhook_url:
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Get current time in selected timezone using the utility functions
            from inventory.views_timezone import format_datetime
            current_time = format_datetime()
            
            # Format first line with Request Stock and current time
            message = f"Request Stock ; {current_time}"
            
            # Add each item to the message (only name and quantity, no code or category)
            items_list = []
            for item_id in item_ids:
                try:
                    item = PackingItem.objects.get(id=item_id)
                    # Only include name and quantity, not code
                    items_list.append(f"{item.name} - {item.current_stock} Pcs")
                except PackingItem.DoesNotExist:
                    logger.error(f"Item with ID {item_id} not found")
            
            # Add items to message as second line
            if items_list:
                message += f"\n{items_list[0]}"  # First item
                # Add additional items if any
                for item in items_list[1:]:
                    message += f"\n{item}"
            
            # Add footer as third line
            message += "\nTanpa konfirmasi"
            
            # Send to webhook as plain text (no Markdown)
            response = requests.post(
                webhook_url,
                json={'text': message},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_packing_to_telegram',
                    status='success',
                    notes=f'Sent packing notification with {len(items_list)} items to Telegram'
                )
                return JsonResponse({'status': 'success', 'message': 'Notifikasi berhasil dikirim ke Telegram'})
            else:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_packing_to_telegram',
                    status='failed',
                    notes=f'Failed to send packing notification to Telegram: {response.text}'
                )
                return JsonResponse({'status': 'error', 'message': f'Gagal mengirim notifikasi: {response.text}'})
            
        except Exception as e:
            logger.error(f"Error in send_packing_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

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
@user_passes_test(is_admin)
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
