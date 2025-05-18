from django.core.management.base import BaseCommand
from inventory.models import WebhookSettings

class Command(BaseCommand):
    help = 'Initialize webhook settings'

    def handle(self, *args, **kwargs):
        if not WebhookSettings.objects.exists():
            WebhookSettings.objects.create(telegram_webhook_url='')
            self.stdout.write(self.style.SUCCESS('Successfully initialized webhook settings'))
        else:
            self.stdout.write(self.style.WARNING('Webhook settings already exist'))
