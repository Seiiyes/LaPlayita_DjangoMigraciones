from django.core.management.base import BaseCommand
from inventory.models import Producto

class Command(BaseCommand):
    help = 'Recalculates stock_actual and costo_promedio for all products based on their associated lots.'

    def handle(self, *args, **options):
        self.stdout.write('Starting recalculation of product stock and average cost...')
        products = Producto.objects.all()
        total_products = products.count()
        updated_count = 0

        for product in products:
            self.stdout.write(f'Processing product: {product.nombre} (ID: {product.id})')
            old_stock = product.stock_actual
            old_costo = product.costo_promedio
            product.actualizar_costo_promedio_y_stock()
            if old_stock != product.stock_actual or old_costo != product.costo_promedio:
                updated_count += 1
                self.stdout.write(f'  - Stock updated from {old_stock} to {product.stock_actual}')
                self.stdout.write(f'  - Costo Promedio updated from {old_costo} to {product.costo_promedio}')
            else:
                self.stdout.write('  - No change in stock or average cost.')

        self.stdout.write(f'Recalculation complete. {updated_count} of {total_products} products updated.')
        self.stdout.write(self.style.SUCCESS('Successfully recalculated all product stocks and average costs.'))