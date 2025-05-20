from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import pandas as pd
import os
import logging
import traceback
from datetime import datetime
from .models import Item, WebhookSettings, ActivityLog, UploadHistory
from .forms import ExcelUploadForm, WebhookSettingsForm, LoginForm

# Configure logging
logger = logging.getLogger(__name__)

# Existing views
@login_required
def dashboard(request):
    # Redirect to kelola_stok_barang view
    return redirect('inventory:kelola_stok_barang')

# New views for submenu pages
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
                messages.error(request, 'File harus berformat Excel (.xlsx, .xls)')
                return redirect('inventory:transfer_stok')
            
            # Use MEDIA_ROOT from settings
            upload_dir = settings.MEDIA_ROOT
            
            # Save the file
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            file_name = f"transfer_{timestamp}_{file.name}"
            file_path = os.path.join(upload_dir, file_name)
            
            # Save file path to database for later access
            upload_history = UploadHistory.objects.create(
                user=request.user,
                filename=file_name,
                file_path=file_path,
                file_size=file.size
            )
            
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            logger.info(f"File saved to {file_path}")
            
            # Process Excel file
            logger.info(f"Reading Excel file: {file.name}")
            try:
                df = pd.read_excel(file_path)
                
                # Always remove the second row (index 1) from the Excel file before processing
                if len(df) > 1:
                    logger.info(f"Removing second row from Excel file as per requirements")
                    df = pd.concat([df.iloc[:1], df.iloc[2:]], ignore_index=True)
                    
            except Exception as e:
                logger.error(f"Error reading Excel file: {str(e)}")
                messages.error(request, f'Error membaca file Excel: {str(e)}')
                return redirect('inventory:transfer_stok')
            
            # Check required columns
            required_columns = ['Kode', 'Nama Barang', 'Total Stok']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Required columns missing: {', '.join(missing_columns)}")
                messages.error(request, f'Kolom berikut tidak ditemukan dalam file: {", ".join(missing_columns)}')
                return redirect('inventory:transfer_stok')
            
            # Process data
            updated_count = 0
            created_count = 0
            error_count = 0
            error_messages = []
            
            try:
                for index, row in df.iterrows():
                    try:
                        # Extract data with robust error handling
                        code = str(row['Kode']).strip() if not pd.isna(row['Kode']) else None
                        name = str(row['Nama Barang']).strip() if not pd.isna(row['Nama Barang']) else None
                        
                        # Handle potential NaN values
                        try:
                            stock = int(row['Total Stok']) if not pd.isna(row['Total Stok']) else 0
                        except (ValueError, TypeError):
                            stock = 0
                            
                        try:
                            min_stock = int(row['Stok Minimum']) if 'Stok Minimum' in df.columns and not pd.isna(row['Stok Minimum']) else None
                        except (ValueError, TypeError):
                            min_stock = None
                        
                        # Skip empty rows
                        if not code or not name:
                            logger.warning(f"Skipping row {index+2}: Empty code or name")
                            error_count += 1
                            error_messages.append(f"Baris {index+2}: Kode atau Nama Barang kosong")
                            continue
                        
                        # Update or create item
                        # Ensure minimum_stock is never null to avoid not-null constraint violation
                        defaults = {
                            'name': name,
                            'current_stock': stock,
                            'minimum_stock': 0  # Default to 0 if min_stock is None
                        }
                        
                        # Only update minimum_stock if a valid value is provided
                        if min_stock is not None:
                            defaults['minimum_stock'] = min_stock
                            
                        item, created = Item.objects.update_or_create(
                            code=code,
                            defaults=defaults
                        )
                        
                        if created:
                            logger.info(f"Created new item: {code} - {name}")
                            created_count += 1
                        else:
                            logger.info(f"Updated existing item: {code} - {name}")
                            updated_count += 1
                            
                    except Exception as row_error:
                        logger.error(f"Error processing row {index+2}: {str(row_error)}")
                        error_count += 1
                        error_messages.append(f"Baris {index+2}: {str(row_error)}")
                        continue
                        
            except Exception as inner_e:
                logger.error(f"Error processing Excel data: {str(inner_e)}")
                logger.error(traceback.format_exc())
                messages.error(request, f'Error saat memproses data: {str(inner_e)}')
                
                # Log activity for failure
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload_transfer_file',
                    status='failure',
                    notes=f'Error processing file: {file.name}. Error: {str(inner_e)}'
                )
                
                # Clean up temporary file
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                    
                return redirect('inventory:transfer_stok')
            
            # Log activity
            status = 'success' if error_count == 0 else 'partial'
            ActivityLog.objects.create(
                user=request.user,
                action='upload_transfer_file',
                status=status,
                notes=f'Uploaded file untuk Transfer Stok: {file.name}, Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
            )
            
            logger.info(f"File processed successfully: {created_count} created, {updated_count} updated, {error_count} errors")
            
            # Show success/error message
            if error_count == 0:
                messages.success(request, f'Berhasil mengupload file. {created_count} item baru ditambahkan, {updated_count} item diperbarui.')
            else:
                messages.warning(request, f'File diproses dengan {error_count} error. {created_count} item baru ditambahkan, {updated_count} item diperbarui.')
                for error in error_messages[:10]:  # Show first 10 errors
                    messages.error(request, error)
                if len(error_messages) > 10:
                    messages.error(request, f'... dan {len(error_messages) - 10} error lainnya.')
            
            # Clean up temporary file
            try:
                os.remove(file_path)
                logger.info(f"Temporary file {file_path} removed")
            except Exception as cleanup_error:
                logger.warning(f"Could not remove temporary file {file_path}: {str(cleanup_error)}")
            
            return redirect('inventory:transfer_stok')
            
        except Exception as e:
            logger.error(f"Error in upload_transfer_file: {str(e)}")
            logger.error(traceback.format_exc())
            messages.error(request, f'Error: {str(e)}')
            return redirect('inventory:transfer_stok')
    
    return redirect('inventory:transfer_stok')

# Backup file view has been removed as per requirements

@login_required
def change_password(request):
    try:
        logger.info("Accessing change_password view")
        
        if request.method == 'POST':
            # Import here to avoid circular import
            from django.contrib.auth.forms import PasswordChangeForm
            
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='change_password',
                    notes=f'User {request.user.username} changed password'
                )
                
                messages.success(request, 'Password berhasil diubah')
                return redirect('inventory:dashboard')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
        else:
            # Import here to avoid circular import
            from django.contrib.auth.forms import PasswordChangeForm
            form = PasswordChangeForm(request.user)
        
        return render(request, 'inventory/change_password.html', {'form': form})
    
    except Exception as e:
        logger.error(f"Error in change_password view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('inventory:dashboard')

@login_required
def webhook_settings(request):
    try:
        settings = WebhookSettings.objects.first()
        if not settings:
            settings = WebhookSettings.objects.create()
    except Exception as e:
        logger.error(f"Error getting webhook settings: {str(e)}")
        settings = WebhookSettings.objects.create()
    
    if request.method == 'POST':
        form = WebhookSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            webhook = form.save(commit=False)
            webhook.updated_by = request.user
            webhook.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_webhook',
                status='success',
                notes=f'Updated webhook URLs'
            )
            
            messages.success(request, 'Pengaturan webhook berhasil disimpan')
            return redirect('inventory:webhook_settings')
    else:
        form = WebhookSettingsForm(instance=settings)
    
    return render(request, 'inventory/webhook_settings.html', {'form': form})

@login_required
def activity_logs(request):
    # Get activity logs
    logs = ActivityLog.objects.all().order_by('-timestamp')
    
    # Get uploaded files
    uploads = UploadHistory.objects.all().order_by('-upload_date')
    
    # Create media URL for each upload
    for upload in uploads:
        # Extract just the filename from the full path
        filename = os.path.basename(upload.file_path)
        # Create the download URL using MEDIA_URL
        upload.download_url = f"{settings.MEDIA_URL}{filename}"
    
    return render(request, 'inventory/activity_logs.html', {
        'logs': logs,
        'uploads': uploads
    })

@login_required
@csrf_exempt
def send_to_telegram(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            source = data.get('source', 'kelola_stok')  # Default to kelola_stok if not specified
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get webhook URL based on source
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings:
                return JsonResponse({'status': 'error', 'message': 'Webhook settings not configured'})
            
            # Determine which webhook URL to use based on source
            if source == 'transfer_stok' and webhook_settings.webhook_transfer_stok:
                webhook_url = webhook_settings.webhook_transfer_stok
            elif source == 'kelola_stok' and webhook_settings.webhook_kelola_stok:
                webhook_url = webhook_settings.webhook_kelola_stok
            else:
                return JsonResponse({'status': 'error', 'message': f'Webhook URL for {source} not configured'})
            
            # Get selected items
            items = Item.objects.filter(id__in=item_ids)
            
            # Prepare data for Telegram
            telegram_data = {
                'produk': []
            }
            
            for item in items:
                # Different format based on source
                if source == 'transfer_stok':
                    # For transfer_stok, only include code, name, and minimum_stock (as stok_transfer)
                    telegram_data['produk'].append({
                        'kode_barang': item.code,
                        'nama_barang': item.name,
                        'stok_transfer': item.minimum_stock or 0
                    })
                else:
                    # For kelola_stok, include all fields as before
                    # Format price with thousand separator
                    price_str = f"Rp {item.selling_price:,.0f}".replace(',', '.')
                    
                    telegram_data['produk'].append({
                        'kode_barang': item.code,
                        'nama_barang': item.name,
                        'kategori': item.category,
                        'stok': item.current_stock,
                        'harga': price_str,
                        'stok_minimum': item.minimum_stock or 0
                    })
            
            # Send to webhook
            import requests
            try:
                # Add logging to debug webhook issues
                logger.info(f"Sending to webhook URL: {webhook_url}")
                logger.info(f"Webhook payload: {json.dumps(telegram_data)}")
                
                response = requests.post(
                    webhook_url,
                    json=telegram_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10  # Add timeout to prevent hanging
                )
                
                logger.info(f"Webhook response status: {response.status_code}")
                logger.info(f"Webhook response content: {response.text[:500]}")  # Log first 500 chars of response
                
                if response.status_code == 200:
                    # Log activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_to_telegram',
                        status='success',
                        notes=f'Sent {len(items)} items to Telegram via {source} webhook'
                    )
                    
                    return JsonResponse({'status': 'success', 'message': 'Data berhasil dikirim ke Telegram'})
                else:
                    # Log failed activity
                    ActivityLog.objects.create(
                        user=request.user,
                        action='send_to_telegram',
                        status='error',
                        notes=f'Failed to send to {source} webhook. Status code: {response.status_code}'
                    )
                    
                    return JsonResponse({'status': 'error', 'message': f'Webhook returned status code {response.status_code}. Response: {response.text[:100]}'})
            except requests.exceptions.RequestException as e:
                # Log connection error
                logger.error(f"Webhook connection error: {str(e)}")
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_to_telegram',
                    status='error',
                    notes=f'Connection error with {source} webhook: {str(e)}'
                )
                
                return JsonResponse({'status': 'error', 'message': f'Tidak dapat terhubung ke webhook: {str(e)}'})
            
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
            min_stock = data.get('min_stock')
            
            if not item_id or min_stock is None:
                return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})
            
            # Update item
            item = Item.objects.get(id=item_id)
            item.minimum_stock = min_stock
            item.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_min_stock',
                notes=f'Updated minimum stock for {item.name} to {min_stock}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
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
                return JsonResponse({'status': 'error', 'message': 'Missing item_id parameter'})
            
            # Update item
            item = Item.objects.get(id=item_id)
            item.minimum_stock = None
            item.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='delete_min_stock',
                notes=f'Removed minimum stock for {item.name}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def get_item(request):
    try:
        item_id = request.GET.get('item_id')
        if not item_id:
            return JsonResponse({'status': 'error', 'message': 'Missing item_id parameter'})
        
        item = Item.objects.get(id=item_id)
        
        return JsonResponse({
            'status': 'success',
            'item': {
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'category': item.category,
                'current_stock': item.current_stock,
                'selling_price': item.selling_price,
                'minimum_stock': item.minimum_stock or 0
            }
        })
        
    except Item.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@csrf_exempt
def update_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Missing item_id parameter'})
            
            # Get item
            item = Item.objects.get(id=item_id)
            
            # Update fields
            item.code = data.get('code', item.code)
            item.name = data.get('name', item.name)
            item.category = data.get('category', item.category)
            item.current_stock = data.get('current_stock', item.current_stock)
            item.selling_price = data.get('selling_price', item.selling_price)
            item.minimum_stock = data.get('minimum_stock', item.minimum_stock)
            
            # Save changes
            item.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='update_item',
                notes=f'Updated item: {item.name}'
            )
            
            return JsonResponse({'status': 'success'})
            
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'})
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
                return JsonResponse({'status': 'error', 'message': 'Missing item_id parameter'})
            
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
