from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Item, ActivityLog
import json
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def reset_exp_data(request):
    """
    Reset all expiry dates for products.
    This only affects the Data Exp Produk page and does not impact other data.
    """
    try:
        # Check if user is admin
        if not request.user.profile.is_admin:
            return JsonResponse({
                'status': 'error',
                'message': 'Anda tidak memiliki izin untuk melakukan tindakan ini'
            })
            
        with transaction.atomic():
            # Set all expiry_date fields to NULL
            updated_count = Item.objects.all().update(expiry_date=None)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_exp_data',
                status='success',
                notes=f'Reset all expiry dates ({updated_count} records updated)'
            )
            
            logger.info(f"User {request.user.username} reset all expiry dates. {updated_count} records updated.")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Berhasil menghapus {updated_count} data tanggal expired',
                'updated_count': updated_count
            })
            
    except Exception as e:
        logger.error(f"Error resetting expiry dates: {str(e)}")
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='reset_exp_data',
            status='failed',
            notes=f'Failed to reset expiry dates: {str(e)}'
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@login_required
@require_POST
def reset_transfer_data(request):
    """
    Reset all transfer stock data.
    This only affects the Transfer Stok page and does not impact other data.
    """
    try:
        # Check if user is admin
        if not request.user.profile.is_admin:
            return JsonResponse({
                'status': 'error',
                'message': 'Anda tidak memiliki izin untuk melakukan tindakan ini'
            })
            
        with transaction.atomic():
            # Set all minimum_stock fields to 0
            updated_count = Item.objects.all().update(minimum_stock=0)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_transfer_data',
                status='success',
                notes=f'Reset all transfer stock data ({updated_count} records updated)'
            )
            
            logger.info(f"User {request.user.username} reset all transfer stock data. {updated_count} records updated.")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Berhasil menghapus {updated_count} data transfer stok',
                'updated_count': updated_count
            })
            
    except Exception as e:
        logger.error(f"Error resetting transfer stock data: {str(e)}")
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='reset_transfer_data',
            status='failed',
            notes=f'Failed to reset transfer stock data: {str(e)}'
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@login_required
@require_POST
def reset_latest_price_data(request):
    """
    Reset all latest price data.
    This only affects the Kelola Harga page and does not impact other data.
    """
    try:
        # Check if user is admin
        if not request.user.profile.is_admin:
            return JsonResponse({
                'status': 'error',
                'message': 'Anda tidak memiliki izin untuk melakukan tindakan ini'
            })
            
        with transaction.atomic():
            # Set all latest_price fields to NULL
            updated_count = Item.objects.all().update(latest_price=None)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='reset_latest_price_data',
                status='success',
                notes=f'Reset all latest price data ({updated_count} records updated)'
            )
            
            logger.info(f"User {request.user.username} reset all latest price data. {updated_count} records updated.")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Berhasil menghapus {updated_count} data harga terbaru',
                'updated_count': updated_count
            })
            
    except Exception as e:
        logger.error(f"Error resetting latest price data: {str(e)}")
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='reset_latest_price_data',
            status='failed',
            notes=f'Failed to reset latest price data: {str(e)}'
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        })
