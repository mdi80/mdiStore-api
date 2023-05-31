from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Product, Category, ImageProduct

User = get_user_model()


class ImageProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageProduct
        fields = ['image']


class UserSerilizer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ProductSerilizer(serializers.ModelSerializer):
    image = ImageProductSerializer(many=True, read_only=True)
    # image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'productCategory', 'description',
                  'price', 'discount', 'isAmazing', 'image']

    # def get_image_urls(self, obj):
    #     return [image.image.url for image in obj.image.all()]


class CategorySerilizer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
