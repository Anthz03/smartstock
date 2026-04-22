from django.urls import path
from .views import StockInView, StockOutView, InventoryHistoryView

urlpatterns = [
    path('inventory/stock-in/', StockInView.as_view(), name='stock-in-api'),
    path('inventory/stock-out/', StockOutView.as_view(), name='stock-out-api'),
    path('inventory/history/', InventoryHistoryView.as_view(), name='inventory-history'),
]