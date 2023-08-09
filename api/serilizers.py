from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *
from django.db.models import Avg
from .utils import get_color_name
from mdistore.settings import HOST_NAME

User = get_user_model()


class HomeContentSerilizer(serializers.ModelSerializer):
    class Meta:
        model = HomeContent
        fields = ["order", "contentType", "params", "api_name", "title", "subtitle"]


class HeaderSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Header
        fields = ["image", "link"]


class ImageProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageProduct
        fields = ["image", "image_url"]

    def get_image_url(self, obj):
        image_url = obj.image.url
        return HOST_NAME + image_url


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
    comments = serializers.SerializerMethodField()
    color_names = serializers.SerializerMethodField()
    color_values = serializers.SerializerMethodField()
    fav = serializers.SerializerMethodField()
    discount_precent = serializers.SerializerMethodField()
    cart_count = serializers.SerializerMethodField()

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
            "rating",
            "sales",
            "views",
            "fav",
            "comments",
            "category_name",
            "image",
            "color_names",
            "color_values",
            "discount_precent",
            "recDays",
            "added",
            "cart_count",
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

    def get_comments(self, obj):
        return obj.commentproduct_set.count()

    def get_fav(self, obj):
        fav = UserFavoriteProduct.objects.filter(
            user=self.context["request"].user, product=obj
        ).count()

        return fav >= 1

    def get_color_names(self, obj):
        color_values = obj.productcolors_set.values_list("color", flat=True)
        color_names = []
        for color_value in color_values:
            color_names.append(get_color_name(color_value))
        return color_names

    def get_color_values(self, obj):
        return obj.productcolors_set.values_list("color", flat=True)

    def get_discount_precent(self, obj):
        return (obj.discount / obj.price) * 100

    def get_cart_count(self, obj):
        cart = CurrentCartUser.objects.filter(user=self.context["request"].user)
        if not cart.exists():
            return 0
        cart_item = ProductCart.objects.filter(cart=cart.first(), product=obj)
        if not cart_item.exists():
            return 0

        return cart_item.first().count


class CategorySerilizer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class CommentSerilizer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    likestatus = serializers.SerializerMethodField()
    buyer = serializers.SerializerMethodField()

    class Meta:
        model = CommentProduct
        fields = [
            "id",
            "user",
            "comment",
            "product",
            "isLiked",
            "created",
            "likes",
            "dislikes",
            "likestatus",
            "buyer",
        ]

    def get_likes(self, obj):
        return obj.commentuserlike_set.filter(liked=True).count()

    def get_dislikes(self, obj):
        return obj.commentuserlike_set.filter(liked=False).count()

    def get_likestatus(self, obj):
        user = self.context["request"].user
        if obj.commentuserlike_set.filter(user=user).count() == 0:
            return -1
        else:
            if obj.commentuserlike_set.filter(user=user).first().liked:
                return 1
            else:
                return 0

    def get_buyer(self, obj):
        user = obj.user
        product = obj.product

        return SaleProduct.objects.filter(user=user, product=product).exists()


class ViewProductSerilizer(serializers.ModelSerializer):
    productobj = serializers.SerializerMethodField()

    class Meta:
        model = ViewProduct
        fields = ["product", "user", "visited", "productobj"]

    def get_productobj(self, obj):
        return ProductSerilizer2(obj.product).data


class ProductSerilizer2(serializers.ModelSerializer):
    image = ImageProductSerializer(many=True, read_only=True)
    sales = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "productCategory",
            "price",
            "discount",
            "isAmazing",
            "sales",
            "views",
            "category_name",
            "image",
            "recDays",
        ]

    def get_views(self, obj):
        return obj.viewproduct_set.count()

    def get_sales(self, obj):
        return obj.saleproduct_set.count()


class ProductSerilizer3(serializers.ModelSerializer):
    views = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "views",
            "category_name",
        ]

    def get_views(self, obj):
        return obj.viewproduct_set.count()


class SearchHistSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchProduct
        fields = [
            "text",
        ]


class ProductCartSerializer(serializers.ModelSerializer):
    product = ProductSerilizer2()

    class Meta:
        model = ProductCart
        fields = ["product", "count"]


class CurrentCartSerializer(serializers.ModelSerializer):
    items = ProductCartSerializer(source="productcart_set", many=True)

    class Meta:
        model = CurrentCartUser
        fields = ["user", "items"]


class IPProductCartSerializer(serializers.ModelSerializer):
    product = ProductSerilizer2()

    class Meta:
        model = IPProductCart
        fields = ["product", "count"]


class AddressUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressUser
        fields = [
            "id",
            "address",
            "postal_code",
            "phone",
            "state",
            "city",
        ]


class InProgressCartSerializer(serializers.ModelSerializer):
    items = IPProductCartSerializer(source="ipproductcart_set", many=True)
    address = AddressUserSerializer()

    class Meta:
        model = InProgressCart
        fields = [
            "id",
            "recorded_date",
            "items",
            "address",
        ]


class ProductPaidCartSerializer(serializers.ModelSerializer):
    product = ProductSerilizer2()

    class Meta:
        model = ProductPaidCart
        fields = ["product", "count", "unitPrice", "discount"]


class PaidCartSerializer(serializers.ModelSerializer):
    items = ProductPaidCartSerializer(source="productpaidcart_set", many=True)

    class Meta:
        model = PaidCart
        fields = [
            "id",
            "recorded_date",
            "amount",
            "ref_id",
            "authority",
            "paid_date",
            "send",
            "send_date",
            "recived_date",
            "items",
            "address",
            "postal_code",
            "phone",
        ]
