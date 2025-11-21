from django.core.management.base import BaseCommand
from inventory.models import Producto

class Command(BaseCommand):
    help = 'Recalculates stock_actual and costo_promedio for all products based on their associated batches.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting recalculation of product stock and average cost...'))
        products = Producto.objects.all()
        total_products = products.count()
        updated_count = 0

        for product in products:
            self.stdout.write(f'Recalculating for product: {product.nombre} (ID: {product.id})...')
            try:
                product.actualizar_costo_promedio_y_stock()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully updated product: {product.nombre}. New stock: {product.stock_actual}, New avg cost: {product.costo_promedio}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating product {product.nombre} (ID: {product.id}): {e}'))

        self.stdout.write(self.style.SUCCESS(f'Finished recalculation. {updated_count} of {total_products} products updated successfully.'))
