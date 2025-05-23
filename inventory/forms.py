from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import WebhookSettings, UserProfile

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        label="Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'}),
        label="File Excel"
    )

class WebhookSettingsForm(forms.ModelForm):
    class Meta:
        model = WebhookSettings
        fields = ['telegram_webhook_url', 'webhook_kelola_stok', 'webhook_transfer_stok', 'webhook_data_exp_produk', 'webhook_kelola_harga', 'webhook_kelola_stok_packing', 'webhook_pesanan_dibatalkan']
        widgets = {
            'telegram_webhook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/webhook'}),
            'webhook_kelola_stok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/webhook/kelola-stok'}),
            'webhook_transfer_stok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/webhook/transfer-stok'}),
            'webhook_data_exp_produk': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hooks.zapier.com/hooks/catch/...'}),
            'webhook_kelola_harga': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hooks.zapier.com/hooks/catch/...'}),
            'webhook_kelola_stok_packing': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hooks.zapier.com/hooks/catch/...'}),
            'webhook_pesanan_dibatalkan': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hooks.zapier.com/hooks/catch/...'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'role']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap'}),
        label="Nama Lengkap"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (Opsional)'}),
        label="Email",
        required=False
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Role/Akses"
    )
    
    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Konfirmasi Password'})
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username sudah digunakan")
        return username
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Password tidak cocok")
        return password2

class UserEditForm(forms.ModelForm):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap'}),
        label="Nama Lengkap"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (Opsional)'}),
        label="Email",
        required=False
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Role/Akses"
    )
    
    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        
        # If we have a user instance, get the profile data
        if instance:
            try:
                profile = instance.profile
                initial['full_name'] = profile.full_name
                initial['role'] = profile.role
            except UserProfile.DoesNotExist:
                pass
        
        kwargs['initial'] = initial
        super(UserEditForm, self).__init__(*args, **kwargs)
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        instance = getattr(self, 'instance', None)
        
        if instance and instance.username == username:
            return username
            
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username sudah digunakan")
        return username
