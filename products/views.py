from django.db.models import F
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsAdmin, IsAdminOrStaff
from .models import Product
from .serializers import ProductSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class ProductListCreateView(APIView):
    permission_classes = []

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAdminOrStaff()]

    def get(self, request):
        search = request.query_params.get('search', None)
        products = Product.objects.all().order_by('-created_at')

        if search:
            products = products.filter(name__icontains=search)

        serializer = ProductSerializer(products, many=True)
        return Response({
            'status': 'success',
            'count': products.count(),
            'data': serializer.data
        })

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'status': 'success', 'message': 'Product created successfully.', 'data': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'status': 'error', 'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailView(APIView):
    permission_classes = []

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminOrStaff()]
        return [IsAdmin()]

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'status': 'error', 'message': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response({'status': 'success', 'data': serializer.data})

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'status': 'error', 'message': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Product updated successfully.', 'data': serializer.data})
        return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'status': 'error', 'message': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Product updated successfully.', 'data': serializer.data})
        return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'status': 'error', 'message': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({'status': 'success', 'message': 'Product deleted successfully.'}, status=status.HTTP_200_OK)


class LowStockView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        low_stock_products = Product.objects.filter(stock_quantity__lte=F('low_stock_threshold'))
        serializer = ProductSerializer(low_stock_products, many=True)
        return Response({
            'status': 'success',
            'count': low_stock_products.count(),
            'data': serializer.data
        })