"""
WSGI config for stock_management project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_management.settings')

# Increase the maximum request line size
os.environ['DJANGO_SETTINGS_MODULE'] = 'stock_management.settings'
os.environ['WSGI_REQUEST_HEADER_MAX_SIZE'] = '8192'  # Increase from default 4096 to 8192

application = get_wsgi_application()
