from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from inventory.models import Item
import os

class Command(BaseCommand):
    help = 'Import sample data from Excel file'

    def handle(self, *args, **kwargs):
        try:
            # Path to the sample Excel file
            excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                     'sample_data', 'sample_inventory.xlsx')
            
            if not os.path.exists(excel_path):
                self.stdout.write(self.style.WARNING(f'Sample file not found at {excel_path}'))
                return
                
            wb = load_workbook(excel_path)
            sheet = wb.active
            
            # Skip header row
            rows = list(sheet.rows)[1:]
            
            success_count = 0
            error_count = 0
            
            for row in rows:
                try:
                    code = str(row[0].value).strip()
                    name = str(row[1].value).strip()
                    category = str(row[2].value).strip()
                    current_stock = int(row[3].value) if row[3].value is not None else 0
                    selling_price = float(row[4].value) if row[4].value is not None else 0
                    
                    # Create new item
                    Item.objects.create(
                        code=code,
                        name=name,
                        category=category,
                        current_stock=current_stock,
                        selling_price=selling_price,
                        minimum_stock=0  # Default value
                    )
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Error importing row: {str(e)}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {success_count} items, failed {error_count} items'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing sample data: {str(e)}'))
