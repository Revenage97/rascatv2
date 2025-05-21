from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import os
import pandas as pd
import logging
import traceback
from datetime import datetime
from .models import Item, ActivityLog, UploadHistory

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def upload_exp_produk_file(request):
    """
    View for uploading Excel file for Data Exp Produk
    This is a separate upload logic that only affects Data Exp Produk
    """
    if request.method == 'POST':
        try:
            # Get the uploaded file
            exp_produk_file = request.FILES.get('exp_produk_file')
            
            if not exp_produk_file:
                messages.error(request, 'File tidak ditemukan')
                return redirect('inventory:upload_file')
            
            # Check file extension
            if not exp_produk_file.name.endswith('.xlsx'):
                messages.error(request, 'Format file harus .xlsx')
                return redirect('inventory:upload_file')
            
            # Save file temporarily
            file_path = os.path.join(settings.MEDIA_ROOT, 'temp', exp_produk_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb+') as destination:
                for chunk in exp_produk_file.chunks():
                    destination.write(chunk)
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check required columns
            required_columns = ['Kode Barang', 'Nama Barang', 'Total Stok', 'Tanggal Expired']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(request, f'Kolom yang diperlukan tidak ditemukan: {", ".join(missing_columns)}')
                return redirect('inventory:upload_file')
            
            # Process data
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Extract data
                    code = str(row['Kode Barang']).strip()
                    name = str(row['Nama Barang']).strip()
                    stock = int(row['Total Stok'])
                    
                    # Handle expiry date
                    expiry_date = None
                    if pd.notna(row['Tanggal Expired']):
                        if isinstance(row['Tanggal Expired'], str):
                            try:
                                expiry_date = datetime.strptime(row['Tanggal Expired'], '%Y-%m-%d').date()
                            except ValueError:
                                try:
                                    expiry_date = datetime.strptime(row['Tanggal Expired'], '%d/%m/%Y').date()
                                except ValueError:
                                    # If date parsing fails, log and continue
                                    logger.warning(f"Could not parse date: {row['Tanggal Expired']} for item {code}")
                        else:
                            # Pandas might have already parsed it as datetime
                            expiry_date = row['Tanggal Expired'].date() if hasattr(row['Tanggal Expired'], 'date') else row['Tanggal Expired']
                    
                    # Check if item exists
                    try:
                        # First try to find by code with expiry date
                        item = Item.objects.get(code=code, expiry_date__isnull=False)
                        
                        # Update existing item
                        item.name = name
                        item.current_stock = stock
                        item.expiry_date = expiry_date
                        item.save()
                        
                    except Item.DoesNotExist:
                        # Item doesn't exist with expiry date, check if it exists without expiry date
                        try:
                            # If item exists without expiry date, create a new one with expiry date
                            # This ensures we don't modify the original item used in Kelola Stok Barang
                            existing_item = Item.objects.get(code=code, expiry_date__isnull=True)
                            
                            # Create new item with same code but with expiry date
                            Item.objects.create(
                                code=code,
                                name=name,
                                category=existing_item.category,  # Use category from existing item
                                current_stock=stock,
                                selling_price=existing_item.selling_price,  # Use price from existing item
                                expiry_date=expiry_date
                            )
                            
                        except Item.DoesNotExist:
                            # Item doesn't exist at all, create new
                            Item.objects.create(
                                code=code,
                                name=name,
                                category="Tidak Dikategorikan",  # Default category
                                current_stock=stock,
                                selling_price=0,  # Default price
                                expiry_date=expiry_date
                            )
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing row for item {code if 'code' in locals() else 'unknown'}: {str(e)}")
                    error_count += 1
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='upload_exp_produk_file',
                status='success',
                notes=f'Uploaded exp produk file: {exp_produk_file.name} ({success_count} items processed, {error_count} errors)'
            )
            
            # Create upload history
            UploadHistory.objects.create(
                user=request.user,
                filename=exp_produk_file.name,
                file_path=file_path,
                file_size=exp_produk_file.size,
                success_count=success_count,
                error_count=error_count
            )
            
            messages.success(request, f'File berhasil diupload. {success_count} item berhasil diproses, {error_count} error.')
            
        except Exception as e:
            logger.error(f"Error in upload_exp_produk_file view: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='upload_exp_produk_file',
                status='failed',
                notes=f'Failed to upload exp produk file: {str(e)}'
            )
            
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('inventory:upload_file')
