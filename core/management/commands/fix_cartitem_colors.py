from django.core.management.base import BaseCommand
from core.models import CartItem, ProductColor

class Command(BaseCommand):
    help = 'Fix CartItem color_name and color_hex for old items'

    def handle(self, *args, **kwargs):
        fixed = 0
        for item in CartItem.objects.filter(color_name__isnull=True):
            color_obj = ProductColor.objects.filter(product=item.product).first()
            if color_obj:
                item.color_name = color_obj.name
                item.color_hex = color_obj.hex_code
                item.color = color_obj.hex_code
                item.save()
                fixed += 1
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed} cart items with missing color info.')) 