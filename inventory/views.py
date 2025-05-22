from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
import json
import logging
import traceback
from .models import Item, WebhookSettings, ActivityLog, UserProfile
from .forms import LoginForm, WebhookSettingsForm, UserRegistrationForm, UserEditForm, UserProfileForm
from .views_timezone import get_localized_time, format_datetime

# Configure logging
logger = logging.getLogger(__name__)

def is_admin(user):
    """
    Check if user has admin role
    """
    try:
        return user.profile.is_admin
    except:
        return False

def is_staff_gudang(user):
    """
    Check if user has staff_gudang role
    """
    try:
        # Add logging to debug role checking
        logger.info(f"Checking staff_gudang role for user {user.username}: {user.profile.is_staff_gudang}")
        return user.profile.is_staff_gudang
    except Exception as e:
        logger.error(f"Error checking staff_gudang role: {str(e)}")
        return False

def is_manajer(user):
    """
    Check if user has manajer role
    """
    try:
        return user.profile.is_manajer
    except:
        return False

@login_required
def dashboard(request):
    """
    View for dashboard
    """
    # Get counts for dashboard stats
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(current_stock__lt=10).count()
    
    # Get recent activity logs
    recent_logs = ActivityLog.objects.all().order_by('-timestamp')[:5]
    
    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'recent_logs': recent_logs
    }
    
    return render(request, 'inventory/dashboard.html', context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def forecasting(request):
    """
    View for forecasting
    """
    return render(request, 'inventory/forecasting.html')

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def otomatisasi(request):
    """
    View for otomatisasi
    """
    return render(request, 'inventory/otomatisasi.html')

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u), login_url='/dashboard/')
def kelola_stok_barang(request):
    # Double-check permission inside the view
    if is_staff_gudang(request.user):
        logger.warning(f"Staff Gudang user {request.user.username} attempted to access kelola_stok_barang")
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini")
        return redirect('inventory:dashboard')
        
    """
    View for managing stock items
    """
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    filter_option = request.GET.get('filter', '')
    
    items = Item.objects.all()
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
    
    # Filter functionality
    if filter_option == 'low_stock':
        items = items.filter(current_stock__lt=10)
    
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
    
    context = {
        'items': items,
        'query': query,
    }
    
    return render(request, 'inventory/kelola_stok_barang.html', context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def data_exp_produk(request):
    """
    View for managing expired products
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    
    items = Item.objects.all()
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query)
    
    # Sorting functionality
    if sort == 'exp_asc':
        items = items.order_by('expiry_date')
    elif sort == 'exp_desc':
        items = items.order_by('-expiry_date')
    elif sort == 'name':
        items = items.order_by('name')
    elif sort == 'name_desc':
        items = items.order_by('-name')
    elif sort == 'stock_asc':
        items = items.order_by('current_stock')
    elif sort == 'stock_desc':
        items = items.order_by('-current_stock')
    
    # Calculate dates for expiry coloring
    today = timezone.now().date()
    six_months_future = today + timedelta(days=180)  # ~6 months
    twelve_months_future = today + timedelta(days=365)  # ~12 months
    
    context = {
        'items': items,
        'query': query,
        'today': today,
        'six_months_future': six_months_future,
        'twelve_months_future': twelve_months_future,
    }
    
    return render(request, 'inventory/data_exp_produk.html', context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u), login_url='/dashboard/')
def kelola_harga(request):
    # Double-check permission inside the view
    if is_staff_gudang(request.user):
        logger.warning(f"Staff Gudang user {request.user.username} attempted to access kelola_harga")
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini")
        return redirect('inventory:dashboard')
        
    """
    View for managing prices
    """
    query = request.GET.get('query', '')
    sort = request.GET.get('sort', '')
    
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
    elif sort == 'price_asc':
        items = items.order_by('selling_price')
    elif sort == 'price_desc':
        items = items.order_by('-selling_price')
    
    context = {
        'items': items,
        'query': query,
    }
    
    return render(request, 'inventory/kelola_harga.html', context)

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
        
        context = {
            'items': items,
            'query': query,
        }
        
        return render(request, 'inventory/transfer_stok.html', context)
    except Exception as e:
        logger.error(f"Error in transfer_stok view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, f"Error: {str(e)}")
        return redirect('inventory:dashboard')

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def change_password(request):
    """
    View for changing user password
    """
    user = request.user
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate old password
        if not user.check_password(old_password):
            messages.error(request, 'Password lama salah')
            return render(request, 'inventory/change_password.html')
        
        # Validate new password
        if new_password != confirm_password:
            messages.error(request, 'Password baru dan konfirmasi password tidak cocok')
            return render(request, 'inventory/change_password.html')
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='change_password',
            status='success',
            notes=f'User {user.username} changed password'
        )
        
        # Update session auth hash to prevent logout
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Password berhasil diubah')
        return redirect('inventory:dashboard')
    
    return render(request, 'inventory/change_password.html')

@login_required
@user_passes_test(is_admin)
def webhook_settings(request):
    """
    View for managing webhook settings
    """
    # Get or create webhook settings
    webhook_settings, created = WebhookSettings.objects.get_or_create(pk=1)
    
    # Get the webhook type from query parameter
    webhook_type = request.GET.get('type', '')
    
    if request.method == 'POST':
        # Create a form instance with POST data
        form = WebhookSettingsForm(request.POST, instance=webhook_settings)
        
        if form.is_valid():
            # Determine which webhook field to update based on the type parameter
            field_to_update = None
            if webhook_type == 'kelola_stok':
                field_to_update = 'webhook_kelola_stok'
            elif webhook_type == 'transfer_stok':
                field_to_update = 'webhook_transfer_stok'
            elif webhook_type == 'data_exp_produk':
                field_to_update = 'webhook_data_exp_produk'
            elif webhook_type == 'kelola_harga':
                field_to_update = 'webhook_kelola_harga'
            elif webhook_type == 'kelola_stok_packing':
                field_to_update = 'webhook_kelola_stok_packing'
            
            if field_to_update:
                # Only update the specific field
                setattr(webhook_settings, field_to_update, form.cleaned_data[field_to_update])
                webhook_settings.updated_by = request.user
                webhook_settings.save(update_fields=[field_to_update, 'updated_by', 'updated_at'])
                
                # Log activity with specific details
                field_display_name = field_to_update.replace('webhook_', '').replace('_', ' ').title()
                notes = f"Webhook {field_display_name} diperbarui: {getattr(webhook_settings, field_to_update)}"
                
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_webhook_settings',
                    status='success',
                    notes=notes
                )
                
                # Add success message with extra tag for the specific webhook type
                messages.success(
                    request, 
                    f'URL Webhook untuk {field_display_name} berhasil disimpan', 
                    extra_tags=webhook_type
                )
            else:
                # If no specific type, update all fields (fallback)
                webhook_settings = form.save(commit=False)
                webhook_settings.updated_by = request.user
                webhook_settings.save()
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='update_webhook_settings',
                    status='success',
                    notes="Semua pengaturan webhook diperbarui"
                )
                
                messages.success(request, 'Semua pengaturan webhook berhasil disimpan')
            
            # Redirect to prevent form resubmission
            return redirect('inventory:webhook_settings')
        else:
            # Form is invalid, add error message with the specific webhook type tag
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, 
                        f'Error: {error}', 
                        extra_tags=webhook_type
                    )
    else:
        # For GET requests, just create the form with the current instance
        form = WebhookSettingsForm(instance=webhook_settings)
    
    context = {
        'form': form
    }
    
    return render(request, 'inventory/webhook_settings.html', context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def activity_logs(request):
    """
    View for displaying activity logs
    """
    logs = ActivityLog.objects.all().order_by('-timestamp')
    
    # Convert timestamps to user's timezone for display
    for log in logs:
        log.localized_timestamp = get_localized_time(log.timestamp)
    
    context = {
        'logs': logs
    }
    
    return render(request, 'inventory/activity_logs.html', context)

def login_view(request):
    """
    View for user login
    """
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('inventory:dashboard')
    
    # Get the next parameter, but limit its length to prevent redirect loops
    next_url = request.GET.get('next', '')
    if len(next_url) > 100:  # Limit the length of next parameter
        next_url = ''
    
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
                    notes=f'User {username} logged in'
                )
                
                # Redirect to next URL if it's safe, otherwise to dashboard
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                    return redirect(next_url)
                return redirect('inventory:dashboard')
            else:
                messages.error(request, 'Username atau password salah')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
        'next': next_url  # Pass the sanitized next URL to the template
    }
    
    return render(request, 'inventory/login.html', context)

@login_required
def logout_view(request):
    """
    View for user logout
    """
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        status='success',
        notes=f'User {request.user.username} logged out'
    )
    
    logout(request)
    return redirect('inventory:login')

@login_required
@user_passes_test(is_admin)
def kelola_pengguna(request):
    """
    View for managing users
    """
    users = User.objects.all()
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
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
                notes=f'Created user {user.username} with role {form.cleaned_data["role"]}'
            )
            
            messages.success(request, f'User {user.username} berhasil dibuat')
            return redirect('inventory:kelola_pengguna')
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
    View for editing user
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User tidak ditemukan')
        return redirect('inventory:kelola_pengguna')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            # Update user
            user = form.save()
            
            # Update or create user profile
            try:
                profile = user.profile
                profile.full_name = form.cleaned_data['full_name']
                profile.role = form.cleaned_data['role']
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=user,
                    full_name=form.cleaned_data['full_name'],
                    role=form.cleaned_data['role']
                )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='edit_user',
                status='success',
                notes=f'Updated user {user.username} with role {form.cleaned_data["role"]}'
            )
            
            messages.success(request, f'User {user.username} berhasil diperbarui')
            return redirect('inventory:kelola_pengguna')
    else:
        # Get user profile data for initial form values
        try:
            profile = user.profile
            initial_data = {
                'full_name': profile.full_name,
                'role': profile.role
            }
        except UserProfile.DoesNotExist:
            initial_data = {}
        
        form = UserEditForm(instance=user, initial=initial_data)
    
    context = {
        'form': form,
        'user_obj': user
    }
    
    return render(request, 'inventory/edit_user.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """
    View for deleting user
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Don't allow deleting yourself
        if user == request.user:
            messages.error(request, 'Anda tidak dapat menghapus akun Anda sendiri')
            return redirect('inventory:kelola_pengguna')
        
        username = user.username
        user.delete()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='delete_user',
            status='success',
            notes=f'Deleted user {username}'
        )
        
        messages.success(request, f'User {username} berhasil dihapus')
    except User.DoesNotExist:
        messages.error(request, 'User tidak ditemukan')
    
    return redirect('inventory:kelola_pengguna')
