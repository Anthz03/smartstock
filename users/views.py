import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .serializers import RegisterSerializer, UserProfileSerializer
from products.models import Product
from inventory.models import InventoryTransaction

BASE_API_URL = 'http://127.0.0.1:8000/api'


def get_auth_headers(request):
    token = request.session.get('access')
    return {'Authorization': f'Bearer {token}'} if token else {}


# ── API Views ──────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'status': 'success',
                    'message': 'User registered successfully.',
                    'data': {
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'status': 'error', 'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({'status': 'success', 'data': serializer.data})

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Profile updated.', 'data': serializer.data})
        return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_role(request):
    return Response({
        'username': request.user.username,
        'role': request.user.role,
        'is_authenticated': request.user.is_authenticated,
    })


# ── Frontend Views ─────────────────────────────────────────────────────────

def login_view(request):
    if request.session.get('access'):
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        response = requests.post(f'{BASE_API_URL}/auth/login/', json={
            'username': username,
            'password': password
        })

        if response.status_code == 200:
            data = response.json()
            request.session['access'] = data['access']
            request.session['refresh'] = data['refresh']
            request.session['username'] = username
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def dashboard_view(request):
    if not request.session.get('access'):
        return redirect('login')

    products = Product.objects.all()
    low_stock = [p for p in products if p.is_low_stock]
    recent_transactions = InventoryTransaction.objects.all().order_by('-created_at')[:5]

    return render(request, 'users/dashboard.html', {
        'username': request.session.get('username'),
        'total_products': products.count(),
        'low_stock_count': len(low_stock),
        'low_stock_products': low_stock,
        'recent_transactions': recent_transactions,
    })


def products_view(request):
    if not request.session.get('access'):
        return redirect('login')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        unit_cost = request.POST.get('unit_cost')
        unit = request.POST.get('unit')
        low_stock_threshold = request.POST.get('low_stock_threshold')

        try:
            Product.objects.create(
                name=name,
                description=description,
                unit_cost=unit_cost,
                unit=unit,
                low_stock_threshold=low_stock_threshold,
            )
            messages.success(request, 'Product added successfully.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('products')

    search = request.GET.get('search', '')
    products = Product.objects.all().order_by('-created_at')
    if search:
        products = products.filter(name__icontains=search)

    return render(request, 'users/products.html', {
        'username': request.session.get('username'),
        'products': products,
        'search': search,
    })


def delete_product(request, product_id):
    if not request.session.get('access'):
        return redirect('login')

    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            product.delete()
            messages.success(request, 'Product deleted successfully.')
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')

    return redirect('products')


def inventory_view(request):
    if not request.session.get('access'):
        return redirect('login')

    product_filter = request.GET.get('product', '')
    type_filter = request.GET.get('type', '')

    transactions = InventoryTransaction.objects.all().order_by('-created_at')
    if product_filter:
        transactions = transactions.filter(product__id=product_filter)
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    products = Product.objects.all()

    return render(request, 'users/inventory.html', {
        'username': request.session.get('username'),
        'transactions': transactions,
        'products': products,
        'product_filter': product_filter,
        'type_filter': type_filter,
    })


def stock_in_view(request):
    if not request.session.get('access'):
        return redirect('login')

    if request.method == 'POST':
        try:
            product = Product.objects.get(id=request.POST.get('product'))
            quantity = int(request.POST.get('quantity'))
            notes = request.POST.get('notes', '')

            product.stock_quantity += quantity
            product.save()

            from users.models import CustomUser
            user = CustomUser.objects.get(username=request.session.get('username'))

            InventoryTransaction.objects.create(
                product=product,
                transaction_type='stock_in',
                quantity=quantity,
                notes=notes,
                performed_by=user,
            )
            messages.success(request, 'Stock in recorded successfully.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('inventory')


def stock_out_view(request):
    if not request.session.get('access'):
        return redirect('login')

    if request.method == 'POST':
        try:
            product = Product.objects.get(id=request.POST.get('product'))
            quantity = int(request.POST.get('quantity'))
            notes = request.POST.get('notes', '')

            if product.stock_quantity < quantity:
                messages.error(request, f'Not enough stock. Current stock is {product.stock_quantity}.')
                return redirect('inventory')

            product.stock_quantity -= quantity
            product.save()

            from users.models import CustomUser
            user = CustomUser.objects.get(username=request.session.get('username'))

            InventoryTransaction.objects.create(
                product=product,
                transaction_type='stock_out',
                quantity=quantity,
                notes=notes,
                performed_by=user,
            )
            messages.success(request, 'Stock out recorded successfully.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('inventory')

def register_view(request):
    if request.session.get('access'):
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/register.html')

        from users.models import CustomUser
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'users/register.html')

        try:
            CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='staff',
            )
            messages.success(request, 'Account created! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'users/register.html')