from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
import os
import logging
import traceback
from datetime import datetime
from .models import Item, WebhookSettings, ActivityLog
from .forms import ExcelUploadForm, WebhookSettingsForm

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
            # Convert Decimal to string for intcomma filter
            item_dict = {
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'category': item.category,
                'current_stock': item.current_stock,
                'selling_price': str(item.selling_price),  # Convert to string for template
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action='login',
                notes=f'User {username} logged in'
            )
            return redirect('inventory:dashboard')
        else:
            messages.error(request, 'Username atau password salah')
    
    return render(request, 'inventory/login.html')

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
                return redirect('inventory:upload_file')
            
            # Check file extension
            if not file.name.endswith('.xlsx'):
                logger.error(f"Invalid file format: {file.name}")
                messages.error(request, 'File harus berformat Excel (.xlsx)')
                return redirect('inventory:upload_file')
            
            # Process Excel file
            logger.info(f"Reading Excel file: {file.name}")
            try:
                df = pd.read_excel(file)
            except Exception as e:
                logger.error(f"Error reading Excel file: {str(e)}")
                messages.error(request, f'Error membaca file Excel: {str(e)}')
                return redirect('inventory:upload_file')
            
            # Check required columns
            required_columns = ['Kode', 'Nama Barang', 'Kategori', 'Total Stok', 'Harga Jual']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Required columns missing: {', '.join(missing_columns)}")
                messages.error(request, f'Kolom berikut tidak ditemukan dalam file: {", ".join(missing_columns)}')
                return redirect('inventory:upload_file')
            
            # Process data
            updated_count = 0
            created_count = 0
            error_count = 0
            
            try:
                for _, row in df.iterrows():
                    try:
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
                    except Exception as row_error:
                        logger.error(f"Error processing row: {str(row_error)}")
                        error_count += 1
                        continue
            except Exception as inner_e:
                logger.error(f"Error processing Excel data: {str(inner_e)}")
                logger.error(traceback.format_exc())
                messages.error(request, f'Error saat memproses data: {str(inner_e)}')
                return redirect('inventory:upload_file')
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='upload_transfer_file',
                status='success',
                notes=f'Uploaded file untuk Transfer Stok: {file.name}, Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
            )
            
            logger.info(f"File processed successfully: {created_count} created, {updated_count} updated, {error_count} errors")
            messages.success(request, f'File berhasil diupload ke Transfer Stok. {created_count} item baru ditambahkan, {updated_count} item diperbarui.')
            return redirect('inventory:transfer_stok')
            
        except Exception as e:
            logger.error(f"Error in upload_transfer_file: {str(e)}")
            logger.error(traceback.format_exc())
            messages.error(request, f'Error: {str(e)}')
            return redirect('inventory:upload_file')
    
    return redirect('inventory:upload_file')

@login_required
def backup_file(request):
    try:
        logger.info("Accessing backup_file view")
        
        if request.method == 'POST':
            try:
                # Get all inventory items
                items = Item.objects.all()
                logger.info(f"Retrieved {items.count()} items for backup")
                
                # Convert Decimal to float for Excel compatibility
                items_list = []
                for item in items:
                    items_list.append({
                        'code': item.code,
                        'name': item.name,
                        'category': item.category,
                        'current_stock': item.current_stock,
                        'selling_price': float(item.selling_price),
                        'minimum_stock': item.minimum_stock
                    })
                
                # Create DataFrame
                data = {
                    'Kode': [item['code'] for item in items_list],
                    'Nama Barang': [item['name'] for item in items_list],
                    'Kategori': [item['category'] for item in items_list],
                    'Total Stok': [item['current_stock'] for item in items_list],
                    'Harga Jual': [item['selling_price'] for item in items_list],
                    'Stok Minimum': [item['minimum_stock'] for item in items_list],
                }
                
                df = pd.DataFrame(data)
                
                # Use Render disk path if available, otherwise use temp directory
                if os.path.exists('/opt/render/project/data'):
                    backup_dir = '/opt/render/project/data'
                else:
                    backup_dir = '/tmp'
                
                logger.info(f"Using backup directory: {backup_dir}")
                
                # Ensure directory exists
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'backup_{timestamp}.xlsx'
                filepath = os.path.join(backup_dir, filename)
                
                # Save to Excel
                logger.info(f"Saving backup to: {filepath}")
                df.to_excel(filepath, index=False)
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='backup_file',
                    status='success',
                    notes=f'Created backup file: {filename}'
                )
                
                # Prepare file for download
                with open(filepath, 'rb') as f:
                    response = HttpResponse(
                        f.read(),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                # Clean up temporary file if not using persistent storage
                if backup_dir == '/tmp':
                    os.remove(filepath)
                
                logger.info("Backup file created and ready for download")
                return response
                
            except Exception as e:
                logger.error(f"Error in backup_file POST: {str(e)}")
                logger.error(traceback.format_exc())
                messages.error(request, f'Error: {str(e)}')
                return redirect('inventory:kelola_stok_barang')
        
        logger.info("Rendering backup_file template")
        return render(request, 'inventory/backup_file.html')
    
    except Exception as e:
        logger.error(f"Error in backup_file view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('inventory:kelola_stok_barang')

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
    logs = ActivityLog.objects.all().order_by('-timestamp')
    return render(request, 'inventory/activity_logs.html', {'logs': logs})

@login_required
@csrf_exempt
def send_to_telegram(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items selected'})
            
            # Get webhook URL
            webhook_settings = WebhookSettings.objects.first()
            if not webhook_settings or not webhook_settings.telegram_webhook_url:
                return JsonResponse({'status': 'error', 'message': 'Webhook URL not configured'})
            
            # Get selected items
            items = Item.objects.filter(id__in=item_ids)
            
            # Prepare data for Telegram
            telegram_data = {
                'produk': []
            }
            
            for item in items:
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
            response = requests.post(
                webhook_settings.telegram_webhook_url,
                json=telegram_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='send_to_telegram',
                    notes=f'Sent {len(items)} items to Telegram'
                )
                
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': f'Webhook returned status code {response.status_code}'})
            
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
