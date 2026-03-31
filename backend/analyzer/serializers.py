from rest_framework import serializers

from .models import (
    AnalysisRecord,
    ContactMessage,
    Product,
    ProductFavorite,
    SearchEvent,
)

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'created_at']


class ProductFavoriteSerializer(serializers.ModelSerializer):
    product_barcode = serializers.CharField(source="product.barcode", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_brand = serializers.CharField(source="product.brand", read_only=True)

    class Meta:
        model = ProductFavorite
        fields = ["id", "product_barcode", "product_name", "product_brand", "created_at"]


class AnalysisRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRecord
        fields = [
            "id",
            "input_method",
            "input_text_preview",
            "product_name",
            "product_brand",
            "user_goal",
            "food_type",
            "confidence",
            "score",
            "nova_group",
            "nutriscore_grade",
            "created_at",
            "analysis_json",
        ]


class SearchEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchEvent
        fields = ["id", "query", "local_only", "ip_address", "user_agent", "created_at"]
