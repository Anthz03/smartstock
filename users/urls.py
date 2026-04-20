from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, UserProfileView,
    login_view, logout_view, dashboard_view,
    products_view, delete_product,
    inventory_view, stock_in_view, stock_out_view, check_role,

)

urlpatterns = [
    # ── API endpoints ──────────────────────────────────────────
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/check-role/', check_role, name='check-role'),

    # ── Frontend pages ─────────────────────────────────────────
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('products/', products_view, name='products'),
    path('products/delete/<int:product_id>/', delete_product, name='delete-product'),
    path('inventory/', inventory_view, name='inventory'),
    path('inventory/stock-in/', stock_in_view, name='stock-in'),
    path('inventory/stock-out/', stock_out_view, name='stock-out'),
]

