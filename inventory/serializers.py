from rest_framework import serializers
from .models import InventoryTransaction


class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    performed_by_username = serializers.ReadOnlyField(source='performed_by.username')

    class Meta:
        model = InventoryTransaction
        fields = (
            'id',
            'product',
            'product_name',
            'transaction_type',
            'quantity',
            'notes',
            'performed_by',
            'performed_by_username',
            'created_at',
        )
        read_only_fields = ('id', 'performed_by', 'created_at')

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate(self, attrs):
        product = attrs.get('product')
        transaction_type = attrs.get('transaction_type')
        quantity = attrs.get('quantity')

        if transaction_type == 'stock_out':
            if product.stock_quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f"Not enough stock. Current stock is {product.stock_quantity}."
                })
        return attrs