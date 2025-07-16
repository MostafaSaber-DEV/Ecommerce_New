from django.core.management.base import BaseCommand
from core.models import CartOrder, CartItem, Product, User

class Command(BaseCommand):
    help = 'Add a default product to any order that has no products.'

    def handle(self, *args, **options):
        default_product = Product.objects.first()
        admin_user = User.objects.filter(is_superuser=True).first()
        if not default_product or not admin_user:
            self.stdout.write(self.style.ERROR('No products or admin user found.'))
            return
        count = 0
        for order in CartOrder.objects.all():
            if not order.items.exists():
                CartItem.objects.create(
                    order=order,
                    user=admin_user,
                    product=default_product,
                    quantity=1,
                    price=default_product.price
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Added default product to order {order.order_id}'))
        if count == 0:
            self.stdout.write(self.style.WARNING('All orders already have products.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {count} orders.')) 