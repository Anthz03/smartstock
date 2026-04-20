from django.db import models
from django.conf import settings
from products.models import Product


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity})"