from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
import pandas as pd
import logging
import traceback
from .models import Item, ActivityLog
from .forms import ExcelUploadForm

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def upload_file(request):
    """
    View for uploading a single Excel file and distributing data to multiple models
    """
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Check file extension
            if not excel_file.name.endswith('.xlsx'):
                messages.error(request, 'Format file tidak valid. Harap upload file Excel (.xlsx)')
                return redirect('inventory:upload_file')
            
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Validate required columns
                required_columns = ['Kode', 'Nama Barang', 'Kategori', 'Harga Jual', 'Total Stok']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    messages.error(request, f'Kolom yang diperlukan tidak ditemukan: {", ".join(missing_columns)}')
                    return redirect('inventory:upload_file')
                
                # Process data and distribute to models
                success_count, error_count = process_excel_data(df, request.user)
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload_file',
                    status='success',
                    notes=f'File {excel_file.name} berhasil diupload. {success_count} item berhasil, {error_count} item gagal'
                )
                
                messages.success(request, f'File berhasil diupload. {success_count} item berhasil diperbarui, {error_count} item gagal')
                return redirect('inventory:upload_file')
                
            except Exception as e:
                logger.error(f"Error in upload_file view: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload_file',
                    status='failed',
                    notes=f'Gagal mengupload file {excel_file.name}: {str(e)}'
                )
                
                messages.error(request, f'Gagal mengupload file: {str(e)}')
                return redirect('inventory:upload_file')
    else:
        form = ExcelUploadForm()
    
    return render(request, 'inventory/upload_file.html', {'form': form})

def process_excel_data(df, user):
    """
    Process Excel data and distribute to multiple models
    
    Args:
        df (DataFrame): Pandas DataFrame containing Excel data
        user (User): User who uploaded the file
        
    Returns:
        tuple: (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    
    # Process each row
    for index, row in df.iterrows():
        try:
            with transaction.atomic():
                # Get or create item
                item, created = Item.objects.update_or_create(
                    code=row['Kode'],
                    defaults={
                        'name': row['Nama Barang'],
                        'category': row['Kategori'],
                        'current_stock': row['Total Stok'],
                        'selling_price': row['Harga Jual']
                    }
                )
                
                # Log activity
                action = 'create_item' if created else 'update_item'
                ActivityLog.objects.create(
                    user=user,
                    action=action,
                    status='success',
                    notes=f'{"Membuat" if created else "Memperbarui"} item {item.code} - {item.name}'
                )
                
                success_count += 1
                
        except Exception as e:
            logger.error(f"Error processing row {index}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='process_excel_row',
                status='failed',
                notes=f'Gagal memproses baris {index}: {str(e)}'
            )
            
            error_count += 1
    
    return success_count, error_count
