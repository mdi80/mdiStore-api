from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Product, Category, ImageProduct, ProductColors
from django.db.models import Avg
from .utils import get_color_name

User = get_user_model()


class ImageProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageProduct
        fields = ["image"]


class UserSerilizer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ColorsSerilizer(serializers.ModelSerializer):
    class Meta:
        model = ProductColors
        fields = ["color_name"]


class ProductSerilizer(serializers.ModelSerializer):
    image = ImageProductSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()
    sales = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    color_names = serializers.SerializerMethodField()
    color_values = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "productCategory",
            "description",
            "price",
            "discount",
            "isAmazing",
            "image",
            "rating",
            "sales",
            "views",
            "category_name",
            "color_names",
            "color_values",
        ]

    def get_rating(self, obj):
        rating = obj.rating_set.aggregate(average=Avg("rate"))["average"]
        if rating == None:
            rating = 0
        return rating

    def get_views(self, obj):
        return obj.viewproduct_set.count()

    def get_sales(self, obj):
        return obj.saleproduct_set.count()

    def get_color_names(self, obj):
        color_values = obj.productcolors_set.values_list("color", flat=True)
        color_names = []
        for color_value in color_values:
            color_names.append(get_color_name(color_value))
        return color_names

    def get_color_values(self, obj):
        return obj.productcolors_set.values_list("color", flat=True)


class CategorySerilizer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


