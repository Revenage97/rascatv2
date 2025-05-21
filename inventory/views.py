from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
import json
import pandas as pd
import os
import logging
import traceback
from datetime import datetime
from .models import Item, WebhookSettings, ActivityLog, UploadHistory, UserProfile
from .forms import ExcelUploadForm, WebhookSettingsForm, LoginForm, UserRegistrationForm, UserEditForm

# Configure logging
logger = logging.getLogger(__name__)

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

@login_required
def data_exp_produk(request):
    """
    View for Data Exp Produk page - currently displays a placeholder message
    """
    return render(request, 'inventory/data_exp_produk.html')

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
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('inventory:kelola_stok_barang')

# Existing views below
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                ActivityLog.objects.create(
                    user=user,
                    action='login',
                    status='success',
                    notes=f'User {username} logged in'
                )
                return redirect('inventory:dashboard')
            else:
                messages.error(request, 'Username atau password salah')
    else:
        form = LoginForm()
    
    return render(request, 'inventory/login.html', {'form': form})

@login_required
def logout_view(request):
    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        notes=f'User {request.user.username} logged out'
    )
    logout(request)
    return redirect('inventory:login')

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['excel_file']
                
                # Check file extension
                if not file.name.endswith('.xlsx'):
                    messages.error(request, 'File harus berformat Excel (.xlsx)')
                    return redirect('inventory:upload_file')
                
                # Process Excel file
                df = pd.read_excel(file)
                
                # Check required columns
                required_columns = ['Kode', 'Nama Barang', 'Kategori', 'Total Stok', 'Harga Jual']
                for col in required_columns:
                    if col not in df.columns:
                        messages.error(request, f'Kolom {col} tidak ditemukan dalam file')
                        return redirect('inventory:upload_file')
                
                # Process data
                updated_count = 0
                created_count = 0
                
                for _, row in df.iterrows():
                    code = str(row['Kode'])
                    name = row['Nama Barang']
                    category = row['Kategori']
                    stock = row['Total Stok']
                    price = row['Harga Jual']
                    
                    # Skip empty rows
                    if pd.isna(code) or pd.isna(name):
                        continue
                    
                    # Convert to proper types
                    code = str(code).strip()
                    name = str(name).strip()
                    category = str(category).strip() if not pd.isna(category) else ''
                    stock = int(stock) if not pd.isna(stock) else 0
                    price = float(price) if not pd.isna(price) else 0
                    
                    # Update or create item
                    item, created = Item.objects.update_or_create(
                        code=code,
                        defaults={
                            'name': name,
                            'category': category,
                            'current_stock': stock,
                            'selling_price': price,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                # Save file to MEDIA_ROOT
                upload_dir = settings.MEDIA_ROOT
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                file_name = f"kelola_stok_{timestamp}_{file.name}"
                file_path = os.path.join(upload_dir, file_name)
                
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Save file metadata to database
                upload_history = UploadHistory.objects.create(
                    user=request.user,
                    filename=file_name,
                    file_path=file_path,
                    file_size=file.size,
                    success_count=created_count,
                    error_count=0
                )
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload_file',
                    notes=f'Uploaded file untuk Kelola Stok Barang: {file.name}, Created: {created_count}, Updated: {updated_count}'
                )
                
                messages.success(request, f'File berhasil diupload ke Kelola Stok Barang. {created_count} item baru ditambahkan, {updated_count} item diperbarui.')
                return redirect('inventory:kelola_stok_barang')
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return redirect('inventory:upload_file')
    else:
        form = ExcelUploadForm()
    
    return render(request, 'inventory/upload_file.html', {'form': form})

@login_required
def upload_transfer_file(request):
    if request.method == 'POST':
        try:
            logger.info("Processing upload_transfer_file request")
            file = request.FILES.get('transfer_file')
            
            if not file:
                logger.error("No file found in request")
                messages.error(request, 'File tidak ditemukan')
                return redirect('inventory:transfer_stok')
            
            # Check file extension
            if not file.name.endswith(('.xlsx', '.xls')):
                logger.error(f"Invalid file format: {file.name}")
                messages.error(request, 'File harus berformat Excel (.xlsx atau .xls)')
                return redirect('inventory:transfer_stok')
            
            # Process Excel file
            df = pd.read_excel(file)
            
            # Check required columns
            required_columns = ['Kode', 'Nama Barang', 'Stok Transfer']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Required column {col} not found in file")
                    messages.error(request, f'Kolom {col} tidak ditemukan dalam file')
                    return redirect('inventory:transfer_stok')
            
            # Process data
            updated_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                code = str(row['Kode'])
                name = row['Nama Barang']
                min_stock = row['Stok Transfer']
                
                # Skip empty rows
                if pd.isna(code) or pd.isna(name) or pd.isna(min_stock):
                    continue
                
                # Convert to proper types
                code = str(code).strip()
                name = str(name).strip()
                min_stock = int(min_stock) if not pd.isna(min_stock) else 0
                
                try:
                    # Update item
                    item = Item.objects.get(code=code)
                    item.minimum_stock = min_stock
                    item.save(update_fields=['minimum_stock'])
                    updated_count += 1
                except Item.DoesNotExist:
                    logger.error(f"Item with code {code} not found")
                    error_count += 1
                except Exception as e:
                    logger.error(f"Error updating item {code}: {str(e)}")
                    error_count += 1
            
            # Save file to MEDIA_ROOT
            upload_dir = settings.MEDIA_ROOT
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            file_name = f"transfer_stok_{timestamp}_{file.name}"
            file_path = os.path.join(upload_dir, file_name)
            
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Save file metadata to database
            upload_history = UploadHistory.objects.create(
                user=request.user,
                filename=file_name,
                file_path=file_path,
                file_size=file.size,
                success_count=updated_count,
                error_count=error_count
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='upload_transfer_file',
                notes=f'Uploaded file untuk Transfer Stok: {file.name}, Updated: {updated_count}, Errors: {error_count}'
            )
            
            if error_count > 0:
                messages.warning(request, f'File berhasil diupload ke Transfer Stok. {updated_count} item diperbarui, {error_count} item gagal diperbarui.')
            else:
                messages.success(request, f'File berhasil diupload ke Transfer Stok. {updated_count} item diperbarui.')
            
            return redirect('inventory:transfer_stok')
                
        except Exception as e:
            logger.error(f"Error in upload_transfer_file view: {str(e)}")
            logger.error(traceback.format_exc())
            messages.error(request, f'Error: {str(e)}')
            return redirect('inventory:transfer_stok')
    
    return redirect('inventory:transfer_stok')

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            messages.error(request, 'Semua field harus diisi')
            return redirect('inventory:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Password baru dan konfirmasi password tidak sama')
            return redirect('inventory:change_password')
        
        user = request.user
        if not user.check_password(old_password):
            messages.error(request, 'Password lama salah')
            return redirect('inventory:change_password')
        
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)  # Keep user logged in
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='change_password',
            notes=f'User {user.username} changed password'
        )
        
        messages.success(request, 'Password berhasil diubah')
        return redirect('inventory:dashboard')
    
    return render(request, 'inventory/change_password.html')

@login_required
def webhook_settings(request):
    webhook_type = request.GET.get('type', None)
    
    try:
        settings_obj, created = WebhookSettings.objects.get_or_create(id=1)
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('inventory:dashboard')
    
    if request.method == 'POST':
        if webhook_type == 'kelola_stok':
            webhook_url = request.POST.get('webhook_kelola_stok', '')
            settings_obj.webhook_kelola_stok = webhook_url
            settings_obj.save(update_fields=['webhook_kelola_stok'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_webhook_settings',
                notes=f'Updated webhook settings for Kelola Stok: {webhook_url}'
            )
            
            messages.success(request, 'Webhook Kelola Stok berhasil disimpan', extra_tags='kelola_stok')
        elif webhook_type == 'transfer_stok':
            webhook_url = request.POST.get('webhook_transfer_stok', '')
            settings_obj.webhook_transfer_stok = webhook_url
            settings_obj.save(update_fields=['webhook_transfer_stok'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_webhook_settings',
                notes=f'Updated webhook settings for Transfer Stok: {webhook_url}'
            )
            
            messages.success(request, 'Webhook Transfer Stok berhasil disimpan', extra_tags='transfer_stok')
        else:
            form = WebhookSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_webhook_settings',
                    notes=f'Updated all webhook settings'
                )
                
                messages.success(request, 'Webhook settings berhasil disimpan')
            else:
                messages.error(request, 'Error: ' + str(form.errors))
        
        return redirect('inventory:webhook_settings')
    else:
        form = WebhookSettingsForm(instance=settings_obj)
    
    context = {
        'form': form,
        'settings': settings_obj
    }
    
    return render(request, 'inventory/webhook_settings.html', context)

@login_required
def activity_logs(request):
    # Get logs from the last 7 days
    logs = ActivityLog.objects.all().order_by('-timestamp')[:100]
    uploads = UploadHistory.objects.all().order_by('-upload_date')[:20]
    
    context = {
        'logs': logs,
        'uploads': uploads
    }
    
    return render(request, 'inventory/activity_logs.html', context)

@login_required
@csrf_exempt
def send_to_telegram(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            source = data.get('source', 'unknown')
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get webhook URL based on source
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings:
                return JsonResponse({'status': 'error', 'message': 'Webhook settings not found'})
            
            if source == 'kelola_stok':
                webhook_url = webhook_settings.webhook_kelola_stok
            elif source == 'transfer_stok':
                webhook_url = webhook_settings.webhook_transfer_stok
            else:
                webhook_url = None
            
            if not webhook_url:
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Get items
            items = Item.objects.filter(id__in=item_ids)
            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items found'})
            
            # Prepare message
            message = f"*Notifikasi {'Kelola Stok' if source == 'kelola_stok' else 'Transfer Stok'}*\n\n"
            
            for item in items:
                message += f"*{item.name}*\n"
                message += f"Kode: {item.code}\n"
                message += f"Kategori: {item.category}\n"
                message += f"Stok Saat Ini: {item.current_stock}\n"
                
                if source == 'transfer_stok' and item.minimum_stock:
                    message += f"Stok Transfer: {item.minimum_stock}\n"
                
                message += "\n"
            
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
                    action=f'send_to_telegram_{source}',
                    status='success',
                    notes=f'Sent {len(items)} items to Telegram'
                )
                
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': f'Webhook error: {response.text}'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def update_min_stock(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            min_stock = data.get('min_stock', 0)
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Update item
            item = Item.objects.get(id=item_id)
            item.minimum_stock = min_stock
            item.save(update_fields=['minimum_stock'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_min_stock',
                status='success',
                notes=f'Updated minimum stock for {item.name} to {min_stock}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_min_stock(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Update item
            item = Item.objects.get(id=item_id)
            item.minimum_stock = None
            item.save(update_fields=['minimum_stock'])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_min_stock',
                status='success',
                notes=f'Deleted minimum stock for {item.name}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def get_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Get item
            item = Item.objects.get(id=item_id)
            
            # Return item data
            return JsonResponse({
                'status': 'success',
                'item': {
                    'id': item.id,
                    'code': item.code,
                    'name': item.name,
                    'category': item.category,
                    'current_stock': item.current_stock,
                    'selling_price': float(item.selling_price) if item.selling_price else 0,
                    'minimum_stock': item.minimum_stock
                }
            })
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def update_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Get item
            item = Item.objects.get(id=item_id)
            
            # Update fields
            if 'code' in data:
                item.code = data['code']
            if 'name' in data:
                item.name = data['name']
            if 'category' in data:
                item.category = data['category']
            if 'current_stock' in data:
                item.current_stock = data['current_stock']
            if 'selling_price' in data:
                item.selling_price = data['selling_price']
            if 'minimum_stock' in data:
                item.minimum_stock = data['minimum_stock']
            
            item.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_item',
                status='success',
                notes=f'Updated item: {item.name}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Item ID is required'})
            
            # Get item
            item = Item.objects.get(id=item_id)
            item_name = item.name
            
            # Delete item
            item.delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_item',
                notes=f'Deleted item: {item_name}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def save_transfer(request):
    """
    View for saving transfer data (asal and tujuan)
    """
    if request.method == 'POST':
        try:
            logger.info("Processing save_transfer request")
            data = json.loads(request.body)
            
            asal = data.get('asal')
            tujuan = data.get('tujuan')
            
            if not asal or not tujuan:
                logger.error("Missing asal or tujuan in save_transfer request")
                return JsonResponse({'status': 'error', 'message': 'Asal and tujuan are required'})
            
            if asal == tujuan:
                logger.error("Asal and tujuan are the same in save_transfer request")
                return JsonResponse({'status': 'error', 'message': 'Asal and tujuan cannot be the same'})
            
            # Log the transfer request
            logger.info(f"Transfer request from {asal} to {tujuan}")
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='save_transfer',
                status='success',
                notes=f'Transfer from {asal} to {tujuan}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in save_transfer request")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            logger.error(f"Error in save_transfer view: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
