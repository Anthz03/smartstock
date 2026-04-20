from django.urls import path
from .views import ProductListCreateView, ProductDetailView, LowStockView

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/low-stock/', LowStockView.as_view(), name='low-stock'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]