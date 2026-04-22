from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'description',
            'unit_cost',
            'unit',
            'stock_quantity',
            'low_stock_threshold',
            'is_low_stock',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'stock_quantity', 'created_at', 'updated_at')

    def validate_unit_cost(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit cost must be greater than zero.")
        return value

    def validate_low_stock_threshold(self, value):
        if value < 0:
            raise serializers.ValidationError("Low stock threshold cannot be negative.")
        return value