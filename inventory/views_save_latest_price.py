from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
import json
from .models import Item, ActivityLog

def is_admin(user):
    return user.profile.is_admin

@login_required
@user_passes_test(is_admin)
def save_latest_price(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        latest_price = data.get('latest_price')
        
        # Validate input
        if not item_id:
            return JsonResponse({'status': 'error', 'message': 'Item ID is required'}, status=400)
        
        # Convert empty string to None
        if latest_price == '':
            latest_price = None
        
        # Convert to decimal if not None
        if latest_price is not None:
            try:
                latest_price = float(latest_price)
                if latest_price < 0:
                    return JsonResponse({'status': 'error', 'message': 'Harga tidak boleh negatif'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Harga harus berupa angka'}, status=400)
        
        # Get item and update latest_price
        try:
            item = Item.objects.get(id=item_id)
            item.latest_price = latest_price
            item.save(update_fields=['latest_price'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action=f"update_latest_price_for_{item.code}",
                status='success',
                notes=f"Harga terbaru untuk {item.name} diperbarui menjadi {latest_price}"
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Harga terbaru berhasil disimpan',
                'item_id': item_id,
                'latest_price': latest_price
            })
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item tidak ditemukan'}, status=404)
        except Exception as e:
            # Log error
            ActivityLog.objects.create(
                user=request.user,
                action="update_latest_price_error",
                status='failed',
                notes=f"Error: {str(e)}"
            )
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
