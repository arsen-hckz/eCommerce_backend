from rest_framework import serializers
from .models import Category, Product
from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price", "stock",
            "image", "is_active", "category", "category_name", "created_at"
        ]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                url = request.build_absolute_uri(obj.image.url)
                return url.replace("http://", "https://")
            return f"https://ecommercebackend-production-33b6.up.railway.app{obj.image.url}"
        return None

class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "stock", "image", "category", "is_active"]