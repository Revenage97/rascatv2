from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
import logging
from .models import PackingItem, ActivityLog, WebhookSettings
import requests

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def kelola_stok_packing(request):
    """
    View for managing packing items (Kelola Stok Packing)
    """
    # Get query parameters
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    filter_param = request.GET.get('filter', '')
    
    # Base queryset
    items = PackingItem.objects.all()
    
    # Apply search query if provided
    if query:
        items = items.filter(
            Q(code__icontains=query) | 
            Q(name__icontains=query) | 
            Q(category__icontains=query)
        )
    
    # Apply filters
    if filter_param == 'low_stock':
        items = items.filter(current_stock__lt=models.F('minimum_stock'))
    
    # Apply sorting
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
    else:
        # Default sorting by code
        items = items.order_by('code')
    
    context = {
        'items': items,
        'query': query,
        'sort': sort,
        'filter': filter_param,
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
                    if min_stock < 0:
                        return JsonResponse({'status': 'error', 'message': 'Minimum stock cannot be negative'})
                    
                    item.minimum_stock = min_stock
                    item.save(update_fields=['minimum_stock'])
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='update_packing_min_stock',
                        status='success',
                        notes=f'Updated minimum stock for {item.name} to {min_stock}'
                    )
                    
                    return JsonResponse({'status': 'success', 'message': 'Minimum stock updated successfully'})
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid minimum stock value'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Minimum stock is required'})
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in update_packing_min_stock view: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_packing_min_stock(request):
    """
    API endpoint to delete (reset to 0) minimum stock for a packing item
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = PackingItem.objects.get(id=item_id)
            
            # Reset minimum stock to 0
            item.minimum_stock = 0
            item.save(update_fields=['minimum_stock'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_packing_min_stock',
                status='success',
                notes=f'Reset minimum stock for {item.name} to 0'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Minimum stock reset successfully'})
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in delete_packing_min_stock view: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def send_packing_to_telegram(request):
    """
    API endpoint to send packing item notification to Telegram
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
            
            webhook_url = webhook_settings.webhook_kelola_stok_packing
            if not webhook_url:
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Get items
            items = PackingItem.objects.filter(id__in=item_ids)
            
            # Prepare message
            message = f"📦 Informasi Stok Packing:\n\n"
            
            for item in items:
                message += f"*{item.name}*\n"
                message += f"Kode: {item.code}\n"
                message += f"Kategori: {item.category}\n"
                message += f"Stok Saat Ini: {item.current_stock}\n"
                
                if item.minimum_stock > 0:
                    message += f"Stok Minimum: {item.minimum_stock}\n"
                    
                    if item.current_stock < item.minimum_stock:
                        message += f"⚠️ *STOK DI BAWAH MINIMUM!*\n"
                
                message += "\n"
            
            # Send to webhook
            response = requests.post(
                webhook_url,
                json={'text': message, 'parse_mode': 'Markdown'},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_packing_to_telegram',
                    status='success',
                    notes=f'Sent packing item notification for {len(items)} items to Telegram'
                )
                
                return JsonResponse({'status': 'success', 'message': 'Notification sent to Telegram'})
            else:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_packing_to_telegram',
                    status='failed',
                    notes=f'Failed to send packing item notification to Telegram: {response.text}'
                )
                
                return JsonResponse({'status': 'error', 'message': f'Failed to send notification: {response.text}'})
            
        except Exception as e:
            logger.error(f"Error in send_packing_to_telegram view: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def reset_all_packing_items(request):
    """
    API endpoint to reset all packing items (admin only)
    """
    if request.method == 'POST':
        try:
            # Check if user is admin
            if not request.user.profile.is_admin:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized. Admin access required.'})
            
            # Delete all packing items
            count = PackingItem.objects.count()
            PackingItem.objects.all().delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_all_packing_items',
                status='success',
                notes=f'Reset all packing items ({count} items deleted)'
            )
            
            return JsonResponse({'status': 'success', 'message': f'All packing items have been reset ({count} items deleted)'})
            
        except Exception as e:
            logger.error(f"Error in reset_all_packing_items view: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
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
            minimum_stock = data.get('minimum_stock', 0)
            
            # Validate required fields
            if not code or not name or not category or current_stock is None:
                return JsonResponse({'status': 'error', 'message': 'All fields are required'})
            
            # Check if code already exists
            if PackingItem.objects.filter(code=code).exists():
                return JsonResponse({'status': 'error', 'message': 'Item with this code already exists'})
            
            # Create new item
            item = PackingItem.objects.create(
                code=code,
                name=name,
                category=category,
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
                'message': 'Item created successfully',
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
            minimum_stock = data.get('minimum_stock', 0)
            
            # Validate required fields
            if not item_id or not code or not name or not category or current_stock is None:
                return JsonResponse({'status': 'error', 'message': 'All fields are required'})
            
            # Get item
            item = PackingItem.objects.get(id=item_id)
            
            # Check if code already exists (excluding current item)
            if PackingItem.objects.filter(code=code).exclude(id=item_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Item with this code already exists'})
            
            # Update item
            item.code = code
            item.name = name
            item.category = category
            item.current_stock = current_stock
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
                'message': 'Item updated successfully',
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
            
            return JsonResponse({'status': 'success', 'message': 'Item deleted successfully'})
            
        except PackingItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in delete_packing_item view: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
