"""
Script to update existing products' status based on completeness
Run this once after adding the status field
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.models import Product

def update_all_product_statuses():
    products = Product.objects.all()
    updated_count = 0
    
    for product in products:
        old_status = product.status
        product.update_status()
        
        if old_status != product.status:
            updated_count += 1
            print(f"Updated {product.name}: {old_status} -> {product.status}")
    
    print(f"\nTotal products: {products.count()}")
    print(f"Updated: {updated_count}")
    print(f"Published: {Product.objects.filter(status='published').count()}")
    print(f"Draft: {Product.objects.filter(status='draft').count()}")

if __name__ == '__main__':
    update_all_product_statuses()
