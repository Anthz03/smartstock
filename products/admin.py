from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_cost', 'unit', 'stock_quantity', 'low_stock_threshold', 'is_low_stock', 'created_at')
    list_filter = ('unit',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')