from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsAdmin, IsAdminOrStaff
from .models import InventoryTransaction
from .serializers import InventoryTransactionSerializer


class StockInView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = InventoryTransactionSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']

            product.stock_quantity += quantity
            product.save()

            serializer.save(
                performed_by=request.user,
                transaction_type='stock_in'
            )

            return Response(
                {
                    'status': 'success',
                    'message': f'Stock in recorded. New stock level: {product.stock_quantity}.',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'status': 'error', 'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class StockOutView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = InventoryTransactionSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']

            product.stock_quantity -= quantity
            product.save()

            serializer.save(
                performed_by=request.user,
                transaction_type='stock_out'
            )

            return Response(
                {
                    'status': 'success',
                    'message': f'Stock out recorded. New stock level: {product.stock_quantity}.',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'status': 'error', 'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class InventoryHistoryView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        queryset = InventoryTransaction.objects.all().order_by('-created_at')

        product_id = request.query_params.get('product', None)
        transaction_type = request.query_params.get('type', None)

        if product_id:
            queryset = queryset.filter(product__id=product_id)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        serializer = InventoryTransactionSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        })