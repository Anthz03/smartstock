import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserProfileSerializer

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

    headers = get_auth_headers(request)

    products_response = requests.get(f'{BASE_API_URL}/products/', headers=headers)
    if products_response.status_code == 401:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')
    products = products_response.json().get('data', []) if products_response.status_code == 200 else []

    low_stock_response = requests.get(f'{BASE_API_URL}/products/low-stock/', headers=headers)
    low_stock = low_stock_response.json().get('data', []) if low_stock_response.status_code == 200 else []

    history_response = requests.get(f'{BASE_API_URL}/inventory/history/', headers=headers)
    history = history_response.json().get('data', []) if history_response.status_code == 200 else []

    return render(request, 'users/dashboard.html', {
        'username': request.session.get('username'),
        'total_products': len(products),
        'low_stock_count': len(low_stock),
        'low_stock_products': low_stock,
        'recent_transactions': history[:5],
    })


def products_view(request):
    if not request.session.get('access'):
        return redirect('login')

    headers = get_auth_headers(request)

    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'description': request.POST.get('description'),
            'unit_cost': request.POST.get('unit_cost'),
            'unit': request.POST.get('unit'),
            'low_stock_threshold': request.POST.get('low_stock_threshold'),
        }
        response = requests.post(f'{BASE_API_URL}/products/', json=data, headers=headers)

        if response.status_code == 201:
            messages.success(request, 'Product added successfully.')
        elif response.status_code == 401:
            messages.error(request, 'Session expired. Please log in again.')
            return redirect('login')
        else:
            error = response.json().get('message', 'Failed to add product.')
            messages.error(request, f'Error: {error}')

        return redirect('products')

    search = request.GET.get('search', '')
    url = f'{BASE_API_URL}/products/?search={search}' if search else f'{BASE_API_URL}/products/'
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    products = response.json().get('data', []) if response.status_code == 200 else []

    return render(request, 'users/products.html', {
        'username': request.session.get('username'),
        'products': products,
        'search': search,
    })


def delete_product(request, product_id):
    if not request.session.get('access'):
        return redirect('login')

    if request.method == 'POST':
        headers = get_auth_headers(request)
        response = requests.delete(f'{BASE_API_URL}/products/{product_id}/', headers=headers)

        if response.status_code == 200:
            messages.success(request, 'Product deleted successfully.')
        elif response.status_code == 401:
            messages.error(request, 'Session expired. Please log in again.')
            return redirect('login')
        else:
            messages.error(request, 'Failed to delete product.')

    return redirect('products')


def inventory_view(request):
    if not request.session.get('access'):
        return redirect('login')

    headers = get_auth_headers(request)

    product_filter = request.GET.get('product', '')
    type_filter = request.GET.get('type', '')

    url = f'{BASE_API_URL}/inventory/history/'
    params = []
    if product_filter:
        params.append(f'product={product_filter}')
    if type_filter:
        params.append(f'type={type_filter}')
    if params:
        url += '?' + '&'.join(params)

    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    transactions = response.json().get('data', []) if response.status_code == 200 else []

    products_response = requests.get(f'{BASE_API_URL}/products/', headers=headers)
    products = products_response.json().get('data', []) if products_response.status_code == 200 else []

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
        headers = get_auth_headers(request)
        data = {
            'product': request.POST.get('product'),
            'quantity': request.POST.get('quantity'),
            'notes': request.POST.get('notes'),
        }
        response = requests.post(f'{BASE_API_URL}/inventory/stock-in/', json=data, headers=headers)

        if response.status_code == 201:
            messages.success(request, 'Stock in recorded successfully.')
        elif response.status_code == 401:
            messages.error(request, 'Session expired. Please log in again.')
            return redirect('login')
        else:
            error = response.json().get('message', 'Failed to record stock in.')
            messages.error(request, f'Error: {error}')

    return redirect('inventory')


def stock_out_view(request):
    if not request.session.get('access'):
        return redirect('login')

    if request.method == 'POST':
        headers = get_auth_headers(request)
        data = {
            'product': request.POST.get('product'),
            'quantity': request.POST.get('quantity'),
            'notes': request.POST.get('notes'),
        }
        response = requests.post(f'{BASE_API_URL}/inventory/stock-out/', json=data, headers=headers)

        if response.status_code == 201:
            messages.success(request, 'Stock out recorded successfully.')
        elif response.status_code == 401:
            messages.error(request, 'Session expired. Please log in again.')
            return redirect('login')
        else:
            error = response.json().get('message', 'Failed to record stock out.')
            messages.error(request, f'Error: {error}')

    return redirect('inventory')