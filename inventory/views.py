from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt # Added missing import
import json
import logging
import traceback
from .models import Item, WebhookSettings, ActivityLog, UserProfile
from .forms import LoginForm, WebhookSettingsForm, UserRegistrationForm, UserEditForm, UserProfileForm
from .views_timezone import get_localized_time, format_datetime
from .utils import is_admin, is_staff_gudang, is_manajer

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """
    View for dashboard
    """
    # Get counts for dashboard stats
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(current_stock__lt=10).count()
    
    # Get recent activity logs
    recent_logs = ActivityLog.objects.all().order_by("-timestamp")[:5]
    
    context = {
        "total_items": total_items,
        "low_stock_items": low_stock_items,
        "recent_logs": recent_logs
    }
    
    return render(request, "inventory/dashboard.html", context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def forecasting(request):
    """
    View for forecasting
    """
    return render(request, "inventory/forecasting.html")

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def otomatisasi(request):
    """
    View for otomatisasi
    """
    return render(request, "inventory/otomatisasi.html")

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u), login_url="/dashboard/")
def kelola_stok_barang(request):
    # Double-check permission inside the view
    if is_staff_gudang(request.user):
        logger.warning(f"Staff Gudang user {request.user.username} attempted to access kelola_stok_barang")
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini")
        return redirect("inventory:dashboard")
        
    """
    View for managing stock items
    """
    query = request.GET.get("query", "")
    sort = request.GET.get("sort", "")
    filter_option = request.GET.get("filter", "")
    
    items = Item.objects.all()
    
    # Default sort by name ascending
    items = items.order_by("name")
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
    
    # Filter functionality
    if filter_option == "low_stock":
        items = items.filter(current_stock__lt=10)
    
    # Specific sorting functionality (overrides default)
    if sort == "name_desc":
        items = items.order_by("-name")
    elif sort == "category":
        items = items.order_by("category")
    elif sort == "category_desc":
        items = items.order_by("-category")
    elif sort == "stock_asc":
        items = items.order_by("current_stock")
    elif sort == "stock_desc":
        items = items.order_by("-current_stock")
    # No need for sort == 'name' as it's the default
    
    context = {
        "items": items,
        "query": query,
    }
    
    return render(request, "inventory/kelola_stok_barang.html", context)

@login_required
# @user_passes_test(lambda u: not is_staff_gudang(u)) # Removed staff gudang check
def data_exp_produk(request):
    """
    View for managing expired products
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    query = request.GET.get("query", "")
    sort = request.GET.get("sort", "")
    
    items = Item.objects.all()
    
    # Default sort by name ascending
    items = items.order_by("name")
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query)
    
    # Specific sorting functionality (overrides default)
    if sort == "exp_asc":
        items = items.order_by("expiry_date")
    elif sort == "exp_desc":
        items = items.order_by("-expiry_date")
    elif sort == "name_desc":
        items = items.order_by("-name")
    elif sort == "stock_asc":
        items = items.order_by("current_stock")
    elif sort == "stock_desc":
        items = items.order_by("-current_stock")
    # No need for sort == 'name' as it's the default
    
    # Calculate dates for expiry coloring
    today = timezone.now().date()
    six_months_future = today + timedelta(days=180)  # ~6 months
    twelve_months_future = today + timedelta(days=365)  # ~12 months
    
    context = {
        "items": items,
        "query": query,
        "today": today,
        "six_months_future": six_months_future,
        "twelve_months_future": twelve_months_future,
    }
    
    return render(request, "inventory/data_exp_produk.html", context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u), login_url="/dashboard/")
def kelola_harga(request):
    # Double-check permission inside the view
    if is_staff_gudang(request.user):
        logger.warning(f"Staff Gudang user {request.user.username} attempted to access kelola_harga")
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini")
        return redirect("inventory:dashboard")
        
    """
    View for managing prices
    """
    query = request.GET.get("query", "")
    sort = request.GET.get("sort", "")
    
    items = Item.objects.all()
    
    # Default sort by name ascending
    items = items.order_by("name")
    
    # Search functionality
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
    
    # Specific sorting functionality (overrides default)
    if sort == "name_desc":
        items = items.order_by("-name")
    elif sort == "category":
        items = items.order_by("category")
    elif sort == "category_desc":
        items = items.order_by("-category")
    elif sort == "price_asc":
        items = items.order_by("selling_price")
    elif sort == "price_desc":
        items = items.order_by("-selling_price")
    # No need for sort == 'name' as it's the default
    
    context = {
        "items": items,
        "query": query,
    }
    
    return render(request, "inventory/kelola_harga.html", context)

@login_required
def kelola_stok_packing(request):
    # This view logic is now in views_packing.py
    # Redirect or render a placeholder if needed, but the main logic is moved.
    # For now, just pass through to the template which might be handled by views_packing.py via URL patterns
    # Or, more correctly, this view might not be used anymore if urls.py points directly to views_packing.kelola_stok_packing
    # Let's assume urls.py handles it correctly and this view is potentially redundant for this specific page.
    # If issues arise, check urls.py mapping for /kelola-stok-packing/
    return render(request, "inventory/kelola_stok_packing.html") # Keeping this for now, but might need removal/update

@login_required
def transfer_stok(request):
    try:
        logger.info("Accessing transfer_stok view")
        query = request.GET.get("query", "")
        sort = request.GET.get("sort", "")
        filter_option = request.GET.get("filter", "")
        
        items = Item.objects.all()
        logger.info(f"Retrieved {items.count()} items from database")
        
        # Default sort by name ascending
        items = items.order_by("name")
        
        # Search functionality
        if query:
            items = items.filter(name__icontains=query) | items.filter(code__icontains=query) | items.filter(category__icontains=query)
        
        # Specific sorting functionality (overrides default)
        if sort == "name_desc":
            items = items.order_by("-name")
        elif sort == "category":
            items = items.order_by("category")
        elif sort == "category_desc":
            items = items.order_by("-category")
        elif sort == "stock_asc":
            items = items.order_by("current_stock")
        elif sort == "stock_desc":
            items = items.order_by("-current_stock")
        # No need for sort == 'name' as it's the default
        
        context = {
            "items": items,
            "query": query,
        }
        
        return render(request, "inventory/transfer_stok.html", context)
    except Exception as e:
        logger.error(f"Error in transfer_stok view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, f"Error: {str(e)}")
        return redirect("inventory:dashboard")

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def change_password(request):
    """
    View for changing user password
    """
    user = request.user
    
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        
        # Validate old password
        if not user.check_password(old_password):
            messages.error(request, "Password lama salah")
            return render(request, "inventory/change_password.html")
        
        # Validate new password
        if new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi password tidak cocok")
            return render(request, "inventory/change_password.html")
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action="change_password",
            status="success",
            notes=f"User {user.username} changed password"
        )
        
        # Update session auth hash to prevent logout
        update_session_auth_hash(request, user)
        
        messages.success(request, "Password berhasil diubah")
        return redirect("inventory:dashboard")
    
    return render(request, "inventory/change_password.html")

@login_required
@user_passes_test(is_admin)
def webhook_settings(request):
    """
    View for managing webhook settings
    """
    # Get or create webhook settings
    webhook_settings, created = WebhookSettings.objects.get_or_create(pk=1)
    
    # Get the webhook type from query parameter
    webhook_type = request.GET.get("type", "")
    
    if request.method == "POST":
        # Create a form instance with POST data
        form = WebhookSettingsForm(request.POST, instance=webhook_settings)
        
        if form.is_valid():
            # Determine which webhook field to update based on the type parameter
            field_to_update = None
            if webhook_type == "kelola_stok":
                field_to_update = "webhook_kelola_stok"
            elif webhook_type == "transfer_stok":
                field_to_update = "webhook_transfer_stok"
            elif webhook_type == "data_exp_produk":
                field_to_update = "webhook_data_exp_produk"
            elif webhook_type == "kelola_harga":
                field_to_update = "webhook_kelola_harga"
            elif webhook_type == "kelola_stok_packing":
                field_to_update = "webhook_kelola_stok_packing"
            
            if field_to_update:
                # Only update the specific field
                setattr(webhook_settings, field_to_update, form.cleaned_data[field_to_update])
                webhook_settings.updated_by = request.user
                webhook_settings.save(update_fields=[field_to_update, "updated_by", "updated_at"])
                
                # Log activity with specific details
                field_display_name = field_to_update.replace("webhook_", "").replace("_", " ").title()
                notes = f"Webhook {field_display_name} diperbarui: {getattr(webhook_settings, field_to_update)}"
                
                ActivityLog.objects.create(
                    user=request.user,
                    action="update_webhook_settings",
                    status="success",
                    notes=notes
                )
                
                # Add success message with extra tag for the specific webhook type
                messages.success(
                    request, 
                    f"URL Webhook untuk {field_display_name} berhasil disimpan", 
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
                    action="update_webhook_settings",
                    status="success",
                    notes="Semua pengaturan webhook diperbarui"
                )
                
                messages.success(request, "Semua pengaturan webhook berhasil disimpan")
            
            # Redirect to prevent form resubmission
            return redirect("inventory:webhook_settings")
        else:
            # Form is invalid, add error message with the specific webhook type tag
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, 
                        f"Error: {error}", 
                        extra_tags=webhook_type
                    )
    else:
        # For GET requests, just create the form with the current instance
        form = WebhookSettingsForm(instance=webhook_settings)
    
    context = {
        "form": form
    }
    
    return render(request, "inventory/webhook_settings.html", context)

@login_required
@user_passes_test(lambda u: not is_staff_gudang(u))
def activity_logs(request):
    """
    View for displaying activity logs
    """
    logs = ActivityLog.objects.all().order_by("-timestamp")
    
    # Convert timestamps to user's timezone for display
    for log in logs:
        log.localized_timestamp = get_localized_time(log.timestamp)
    
    context = {
        "logs": logs
    }
    
    return render(request, "inventory/activity_logs.html", context)

def login_view(request):
    """
    View for user login
    """
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect("inventory:dashboard")
    
    # Get the next parameter, but limit its length to prevent redirect loops
    next_url = request.GET.get("next", "")
    if len(next_url) > 100:  # Limit the length of next parameter
        next_url = ""
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Log activity
                ActivityLog.objects.create(
                    user=user,
                    action="login",
                    status="success",
                    notes=f"User {username} logged in"
                )
                
                # Redirect to next URL if it's safe, otherwise to dashboard
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                    return redirect(next_url)
                return redirect("inventory:dashboard")
            else:
                messages.error(request, "Username atau password salah")
    else:
        form = LoginForm()
    
    context = {
        "form": form,
        "next": next_url  # Pass the sanitized next URL to the template
    }
    
    return render(request, "inventory/login.html", context)

@login_required
def logout_view(request):
    """
    View for user logout
    """
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        action="logout",
        status="success",
        notes=f"User {request.user.username} logged out"
    )
    
    logout(request)
    return redirect("inventory:login")

@login_required
@user_passes_test(is_admin)
def kelola_pengguna(request):
    """
    View for managing users
    """
    users = User.objects.all().order_by("username") # Default sort users by username
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                is_staff_gudang=form.cleaned_data.get("is_staff_gudang", False),
                is_manajer=form.cleaned_data.get("is_manajer", False)
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action="create_user",
                status="success",
                notes=f"User {user.username} created by {request.user.username}"
            )
            
            messages.success(request, f"Pengguna {user.username} berhasil dibuat")
            return redirect("inventory:kelola_pengguna")
        else:
            messages.error(request, "Gagal membuat pengguna. Periksa kembali data yang dimasukkan.")
    else:
        form = UserRegistrationForm()
    
    context = {
        "users": users,
        "form": form
    }
    
    return render(request, "inventory/kelola_pengguna.html", context)

@login_required
@user_passes_test(is_admin)
def edit_pengguna(request, user_id):
    """
    View for editing user details
    """
    user_to_edit = get_object_or_404(User, pk=user_id)
    profile_to_edit = get_object_or_404(UserProfile, user=user_to_edit)
    
    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=user_to_edit)
        profile_form = UserProfileForm(request.POST, instance=profile_to_edit)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action="edit_user",
                status="success",
                notes=f"User {user_to_edit.username} edited by {request.user.username}"
            )
            
            messages.success(request, f"Pengguna {user_to_edit.username} berhasil diperbarui")
            return redirect("inventory:kelola_pengguna")
        else:
            messages.error(request, "Gagal memperbarui pengguna. Periksa kembali data yang dimasukkan.")
    else:
        user_form = UserEditForm(instance=user_to_edit)
        profile_form = UserProfileForm(instance=profile_to_edit)
    
    context = {
        "user_to_edit": user_to_edit,
        "user_form": user_form,
        "profile_form": profile_form
    }
    
    return render(request, "inventory/edit_pengguna.html", context)

@login_required
@user_passes_test(is_admin)
@csrf_exempt
def delete_pengguna(request):
    """
    API endpoint to delete a user
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            
            if not user_id:
                return JsonResponse({"status": "error", "message": "User ID is required"})
            
            # Prevent deleting the current admin user
            if user_id == request.user.id:
                return JsonResponse({"status": "error", "message": "Anda tidak dapat menghapus akun Anda sendiri"})
            
            user_to_delete = get_object_or_404(User, pk=user_id)
            username_deleted = user_to_delete.username
            user_to_delete.delete()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action="delete_user",
                status="success",
                notes=f"User {username_deleted} deleted by {request.user.username}"
            )
            
            return JsonResponse({"status": "success", "message": f"Pengguna {username_deleted} berhasil dihapus"})
            
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Pengguna tidak ditemukan"})
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({"status": "error", "message": str(e)})
    
    return JsonResponse({"status": "error", "message": "Invalid request method"})




@login_required
@user_passes_test(lambda u: is_admin(u) or is_staff_gudang(u), login_url="/dashboard/")
def pesanan_dibatalkan(request):
    """
    View for displaying cancelled orders (placeholder).
    Accessible only by admin and staff gudang.
    """
    # Double-check permission inside the view for robustness
    if not (is_admin(request.user) or is_staff_gudang(request.user)):
        logger.warning(f"User {request.user.username} (role: {request.user.profile.role}) attempted to access pesanan_dibatalkan without permission.")
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect("inventory:dashboard")
        
    context = {} # No data needed for now
    return render(request, "inventory/pesanan_dibatalkan.html", context)

