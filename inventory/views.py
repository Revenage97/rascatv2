from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction, models
from django.db.models import Q
from django.utils import timezone
import json
import pandas as pd
import os
import logging
import traceback
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Item, WebhookSettings, ActivityLog, UploadHistory, UserProfile
from .forms import ExcelUploadForm, WebhookSettingsForm, LoginForm, UserRegistrationForm, UserEditForm

# Configure logging
logger = logging.getLogger(__name__)

# Import upload_exp_produk_file view
from .views_upload_exp_produk import upload_exp_produk_file

# Existing views
@login_required
def dashboard(request):
    # Redirect to kelola_stok_barang view
    return redirect('inventory:kelola_stok_barang')

# Helper function to check if user is admin
def is_admin(user):
    try:
        return user.profile.is_admin
    except (UserProfile.DoesNotExist, AttributeError):
        return False

# Forecasting view
@login_required
def forecasting(request):
    """
    View for forecasting page - currently displays a placeholder message
    """
    return render(request, 'inventory/forecasting.html')

# Otomatisasi view
@login_required
def otomatisasi(request):
    """
    View for otomatisasi page - currently displays a placeholder message
    """
    return render(request, 'inventory/otomatisasi.html')

@login_required
def data_exp_produk(request):
    """
    View for Data Exp Produk page - displays products with their expiry dates
    """
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    
    items = Item.objects.all()
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
    
    # Sorting functionality
    if sort == 'exp_asc':
        # Sort by expiry date (nulls last)
        items = items.order_by(models.F('expiry_date').asc(nulls_last=True))
    elif sort == 'exp_desc':
        # Sort by expiry date (nulls first)
        items = items.order_by(models.F('expiry_date').desc(nulls_first=True))
    
    # Get today's date for comparison
    today = timezone.now().date()
    
    # Calculate date 6 months from today for color coding
    from dateutil.relativedelta import relativedelta
    six_months_future = today + relativedelta(months=6)
    
    context = {
        'items': items,
        'query': query,
        'today': today,
        'six_months_future': six_months_future,
    }
    
    return render(request, 'inventory/data_exp_produk.html', context)

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
                    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                    item.expiry_date = expiry_date
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid date format'})
            else:
                # Clear expiry date if empty
                item.expiry_date = None
            
            item.save(update_fields=['expiry_date'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_expiry_date',
                status='success',
                notes=f'Updated expiry date for {item.name} to {expiry_date}'
            )
            
            return JsonResponse({'status': 'success', 'message': 'Expiry date updated successfully'})
            
        except Item.DoesNotExist:
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
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            item = Item.objects.get(id=item_id)
            
            # Get webhook URL
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings:
                return JsonResponse({'status': 'error', 'message': 'Webhook settings not found'})
            
            webhook_url = webhook_settings.webhook_data_exp_produk
            if not webhook_url:
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Format expiry date
            expiry_date = item.expiry_date.strftime('%d-%m-%Y') if item.expiry_date else 'Tidak diatur'
            
            # Prepare message
            message = f"📦 Produk Expired:\n"
            message += f"Nama: {item.name}\n"
            message += f"Exp: {expiry_date}\n"
            message += f"Stok: {item.current_stock}\n"
            
            # Send to webhook
            import requests
            response = requests.post(
                webhook_url,
                json={'text': message, 'parse_mode': 'Markdown'},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_exp_to_telegram',
                    status='success',
                    notes=f'Sent expiry notification for {item.name} to Telegram'
                )
                
                return JsonResponse({'status': 'success', 'message': 'Notification sent to Telegram'})
            else:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_exp_to_telegram',
                    status='failed',
                    notes=f'Failed to send expiry notification for {item.name} to Telegram: {response.text}'
                )
                
                return JsonResponse({'status': 'error', 'message': f'Failed to send notification: {response.text}'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            logger.error(f"Error in send_exp_to_telegram view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# New views for submenu pages
@login_required
@user_passes_test(is_admin)
def kelola_pengguna(request):
    """
    View for managing users - allows admin to create, edit, and delete users
    """
    users = User.objects.all().select_related('profile')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = form.save()
                    
                    # Create user profile
                    UserProfile.objects.create(
                        user=user,
                        full_name=form.cleaned_data['full_name'],
                        role=form.cleaned_data['role']
                    )
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='create_user',
                        status='success',
                        notes=f'User {user.username} created with role {form.cleaned_data["role"]}'
                    )
                    
                    messages.success(request, f'User {user.username} berhasil dibuat')
                    return redirect('inventory:kelola_pengguna')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = UserRegistrationForm()
    
    context = {
        'users': users,
        'form': form
    }
    
    return render(request, 'inventory/kelola_pengguna.html', context)

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    """
    View for editing an existing user
    """
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user
                    user = form.save()
                    
                    # Update or create user profile
                    profile, created = UserProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'full_name': form.cleaned_data['full_name'],
                            'role': form.cleaned_data['role']
                        }
                    )
                    
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='edit_user',
                        status='success',
                        notes=f'User {user.username} updated'
                    )
                    
                    messages.success(request, f'User {user.username} berhasil diperbarui')
                    return redirect('inventory:kelola_pengguna')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = UserEditForm(instance=user_obj)
    
    context = {
        'form': form,
        'user_obj': user_obj
    }
    
    return render(request, 'inventory/edit_user.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """
    View for deleting a user
    """
    user_obj = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if user_obj == request.user:
        messages.error(request, 'Anda tidak dapat menghapus akun Anda sendiri')
        return redirect('inventory:kelola_pengguna')
    
    if request.method == 'POST':
        try:
            username = user_obj.username
            user_obj.delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_user',
                status='success',
                notes=f'User {username} deleted'
            )
            
            messages.success(request, f'User {username} berhasil dihapus')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('inventory:kelola_pengguna')
    
    context = {
        'user_obj': user_obj
    }
    
    return render(request, 'inventory/delete_user.html', context)

@login_required
def kelola_stok_barang(request):
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    filter_option = request.GET.get('filter', '')
    
    items = Item.objects.all()
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
    
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
    elif sort == 'price_asc':
        items = items.order_by('selling_price')
    elif sort == 'price_desc':
        items = items.order_by('-selling_price')
    
    # Filtering functionality
    if filter_option == 'low_stock':
        items = [item for item in items if item.minimum_stock and item.current_stock < item.minimum_stock]
    
    context = {
        'items': items,
        'query': query,
    }
    
    return render(request, 'inventory/kelola_stok_barang.html', context)

@login_required
def kelola_harga(request):
    return render(request, 'inventory/kelola_harga.html')

@login_required
def kelola_stok_packing(request):
    return render(request, 'inventory/kelola_stok_packing.html')

@login_required
def transfer_stok(request):
    try:
        logger.info("Accessing transfer_stok view")
        query = request.GET.get('query', '')
        sort = request.GET.get('sort', '')
        filter_option = request.GET.get('filter', '')
        
        items = Item.objects.all()
        logger.info(f"Retrieved {items.count()} items from database")
        
        # Search functionality
        if query:
            items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
        
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
        elif sort == 'price_asc':
            items = items.order_by('selling_price')
        elif sort == 'price_desc':
            items = items.order_by('-selling_price')
        
        # Filtering functionality
        if filter_option == 'low_stock':
            items = [item for item in items if item.minimum_stock and item.current_stock < item.minimum_stock]
        
        # Convert items to list for manipulation
        items_list = []
        for item in items:
            # Convert Decimal to float for intcomma filter compatibility
            selling_price = float(item.selling_price) if item.selling_price else 0
            
            item_dict = {
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'category': item.category,
                'current_stock': item.current_stock,
                'selling_price': selling_price,  # Convert to float for template
                'minimum_stock': item.minimum_stock
            }
            items_list.append(item_dict)
        
        context = {
            'items': items_list,
            'query': query,
        }
        
        logger.info("Rendering transfer_stok template")
        return render(request, 'inventory/transfer_stok.html', context)
    except Exception as e:
        logger.error(f"Error in transfer_stok view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, f"Error: {str(e)}")
        return redirect('inventory:dashboard')

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save the uploaded file
                excel_file = request.FILES['excel_file']
                file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', excel_file.name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb+') as destination:
                    for chunk in excel_file.chunks():
                        destination.write(chunk)
                
                # Process the Excel file
                df = pd.read_excel(file_path, engine='openpyxl')
                
                # Skip the first row (header) and second row (usually contains instructions)
                df = df.iloc[2:]
                
                # Reset index after skipping rows
                df = df.reset_index(drop=True)
                
                # Map DataFrame columns to model fields
                with transaction.atomic():
                    for _, row in df.iterrows():
                        # Extract data from row
                        code = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else None
                        name = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else None
                        category = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else None
                        current_stock = int(row.iloc[3]) if not pd.isna(row.iloc[3]) else 0
                        selling_price = float(row.iloc[4]) if not pd.isna(row.iloc[4]) else 0
                        
                        # Skip rows with empty code or name
                        if not code or not name:
                            continue
                        
                        # Update or create item
                        item, created = Item.objects.update_or_create(
                            code=code,
                            defaults={
                                'name': name,
                                'category': category,
                                'current_stock': current_stock,
                                'selling_price': selling_price,
                            }
                        )
                
                # Record upload history
                UploadHistory.objects.create(
                    user=request.user,
                    filename=excel_file.name,
                    file_path=file_path,
                    file_size=excel_file.size,
                    success_count=df.shape[0]
                )
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload_file',
                    status='success',
                    notes=f'Uploaded file: {excel_file.name}'
                )
                
                messages.success(request, 'File berhasil diupload dan data telah diperbarui.')
                return redirect('inventory:dashboard')
                
            except Exception as e:
                # Log error
                logger.error(f"Error processing Excel file: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Record upload history with error
                UploadHistory.objects.create(
                    user=request.user,
                    filename=excel_file.name if 'excel_file' in request.FILES else 'Unknown',
                    file_path=file_path if 'file_path' in locals() else 'Unknown',
                    file_size=excel_file.size if 'excel_file' in request.FILES else 0,
                    error_count=1
                )
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload_file',
                    status='failed',
                    notes=f'Failed to upload file: {str(e)}'
                )
                
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ExcelUploadForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'inventory/upload_file.html', context)

@login_required
def upload_transfer_file(request):
    if request.method == 'POST':
        try:
            # Save the uploaded file
            excel_file = request.FILES['transfer_file']
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', excel_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            
            # Process the Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Skip the first row (header) and second row (usually contains instructions)
            df = df.iloc[2:]
            
            # Reset index after skipping rows
            df = df.reset_index(drop=True)
            
            # Map DataFrame columns to model fields
            with transaction.atomic():
                for _, row in df.iterrows():
                    # Extract data from row
                    code = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else None
                    name = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else None
                    current_stock = int(row.iloc[2]) if not pd.isna(row.iloc[2]) else 0
                    
                    # Skip rows with empty code or name
                    if not code or not name:
                        continue
                    
                    # Update or create item
                    item, created = Item.objects.update_or_create(
                        code=code,
                        defaults={
                            'name': name,
                            'current_stock': current_stock,
                        }
                    )
            
            # Record upload history
            UploadHistory.objects.create(
                user=request.user,
                filename=excel_file.name,
                file_path=file_path,
                file_size=excel_file.size,
                success_count=df.shape[0]
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='upload_transfer_file',
                status='success',
                notes=f'Uploaded transfer file: {excel_file.name}'
            )
            
            messages.success(request, 'File transfer berhasil diupload dan data telah diperbarui.')
            return redirect('inventory:transfer_stok')
            
        except Exception as e:
            # Log error
            logger.error(f"Error processing Excel file: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Record upload history with error
            UploadHistory.objects.create(
                user=request.user,
                filename=excel_file.name if 'excel_file' in locals() else 'Unknown',
                file_path=file_path if 'file_path' in locals() else 'Unknown',
                file_size=excel_file.size if 'excel_file' in locals() else 0,
                error_count=1
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='upload_transfer_file',
                status='failed',
                notes=f'Failed to upload transfer file: {str(e)}'
            )
            
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('inventory:upload_file')

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate input
        if not old_password or not new_password or not confirm_password:
            messages.error(request, 'Semua field harus diisi')
            return redirect('inventory:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Password baru dan konfirmasi password tidak cocok')
            return redirect('inventory:change_password')
        
        # Check old password
        user = request.user
        if not user.check_password(old_password):
            messages.error(request, 'Password lama tidak valid')
            return redirect('inventory:change_password')
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, user)
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='change_password',
            status='success',
            notes='Password changed successfully'
        )
        
        messages.success(request, 'Password berhasil diubah')
        return redirect('inventory:dashboard')
    
    return render(request, 'inventory/change_password.html')

@login_required
def activity_logs(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')
    
    context = {
        'logs': logs
    }
    
    return render(request, 'inventory/activity_logs.html', context)

@login_required
@user_passes_test(is_admin)
def webhook_settings(request):
    webhook_settings = WebhookSettings.objects.first()
    
    if not webhook_settings:
        webhook_settings = WebhookSettings.objects.create()
    
    if request.method == 'POST':
        form = WebhookSettingsForm(request.POST, instance=webhook_settings)
        if form.is_valid():
            try:
                webhook = form.save(commit=False)
                webhook.updated_by = request.user
                webhook.save()
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_webhook_settings',
                    status='success',
                    notes='Webhook settings updated'
                )
                
                messages.success(request, 'Webhook settings berhasil diperbarui')
                return redirect('inventory:webhook_settings')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = WebhookSettingsForm(instance=webhook_settings)
    
    context = {
        'form': form,
        'webhook_settings': webhook_settings
    }
    
    return render(request, 'inventory/webhook_settings.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inventory:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Log activity
                ActivityLog.objects.create(
                    user=user,
                    action='login',
                    status='success',
                    notes='User logged in'
                )
                
                # Get next URL from query parameters
                next_url = request.GET.get('next', '')
                
                # Sanitize next URL to prevent redirect loops
                if next_url and len(next_url) <= 100 and 'login' not in next_url:
                    return redirect(next_url)
                else:
                    return redirect('inventory:kelola_stok_barang')
            else:
                messages.error(request, 'Username atau password salah')
    else:
        form = LoginForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'inventory/login.html', context)

@login_required
def logout_view(request):
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        status='success',
        notes='User logged out'
    )
    
    logout(request)
    return redirect('inventory:login')

@login_required
def backup_history(request):
    return render(request, 'inventory/backup_history.html')
