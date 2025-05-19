from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from .models import Item, WebhookSettings

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['code', 'name', 'category', 'current_stock', 'selling_price', 'minimum_stock']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class WebhookSettingsForm(forms.ModelForm):
    class Meta:
        model = WebhookSettings
        fields = ['telegram_webhook_url', 'webhook_kelola_stok', 'webhook_transfer_stok']
        widgets = {
            'telegram_webhook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://api.telegram.org/bot<token>/sendMessage?chat_id=<chat_id>'}),
            'webhook_kelola_stok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hooks.zapier.com/hooks/catch/...'}),
            'webhook_transfer_stok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hooks.zapier.com/hooks/catch/...'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )
