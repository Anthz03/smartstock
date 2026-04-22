from django.db import models
from django.conf import settings

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text="e.g. pcs, kg, box")
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold