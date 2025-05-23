# Generated by Django 5.2.1 on 2025-05-21 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_item_latest_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackingItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Kode Barang')),
                ('name', models.CharField(max_length=255, verbose_name='Nama Barang')),
                ('category', models.CharField(max_length=100, verbose_name='Kategori')),
                ('current_stock', models.IntegerField(default=0, verbose_name='Stok Saat Ini')),
                ('minimum_stock', models.IntegerField(default=0, verbose_name='Stok Minimum')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Packing Item',
                'verbose_name_plural': 'Packing Items',
                'ordering': ['code'],
            },
        ),
        migrations.AddField(
            model_name='webhooksettings',
            name='webhook_kelola_stok_packing',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='URL Webhook Telegram - Kelola Stok Packing'),
        ),
    ]
